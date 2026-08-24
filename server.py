import json
import os
import threading
import uuid
import time
import base64
import hashlib
import hmac
import secrets

from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ============================================================
# CINEMAX SERVER
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CINEMA_DIR = os.path.join(BASE_DIR, "Cinema-main")

DATA_FILE = os.path.join(CINEMA_DIR, "data.json")
TRASH_FILE = os.path.join(CINEMA_DIR, "trash.json")
USERS_FILE = os.path.join(CINEMA_DIR, "users.json")
SESSIONS_FILE = os.path.join(CINEMA_DIR, "sessions.json")

WEB_DIR = BASE_DIR

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8000))


# ============================================================
# SEGURIDAD
# ============================================================

# PBKDF2-SHA256
PASSWORD_HASH_ITERATIONS = 310_000

# 32 bytes de entropía para sesiones
SESSION_BYTES = 32

# Una sesión puede vivir como máximo 7 días
SESSION_MAX_AGE = 60 * 60 * 24 * 7

# Si pasan 4 horas sin actividad, la sesión expira
SESSION_IDLE_TIMEOUT = 60 * 60 * 4

# Rate limiting de login
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_BLOCK_SECONDS = 15 * 60

LOGIN_ATTEMPTS = {}
LOGIN_ATTEMPTS_LOCK = threading.RLock()


# ============================================================
# GITHUB
# ============================================================

GITHUB_TOKEN = os.environ.get(
    "GITHUB_TOKEN",
    ""
).strip()

GITHUB_OWNER = os.environ.get(
    "GITHUB_OWNER",
    ""
).strip()

GITHUB_REPO = os.environ.get(
    "GITHUB_REPO",
    ""
).strip()

GITHUB_BRANCH = os.environ.get(
    "GITHUB_BRANCH",
    "main"
).strip() or "main"

GITHUB_PATH_PREFIX = os.environ.get(
    "GITHUB_PATH_PREFIX",
    "Cinema-main"
).strip().strip("/")

GITHUB_COMMITTER_NAME = os.environ.get(
    "GITHUB_COMMITTER_NAME",
    "CINEMAX Server"
).strip() or "CINEMAX Server"

GITHUB_COMMITTER_EMAIL = os.environ.get(
    "GITHUB_COMMITTER_EMAIL",
    "cinemax-server@users.noreply.github.com"
).strip() or "cinemax-server@users.noreply.github.com"

GITHUB_API_VERSION = "2026-03-10"
GITHUB_API_BASE = "https://api.github.com"


# ============================================================
# ARCHIVOS PERSISTENTES
# ============================================================

GITHUB_FILES = {
    DATA_FILE: "data.json",
    TRASH_FILE: "trash.json",
    USERS_FILE: "users.json"
}


# ============================================================
# LOCKS
# ============================================================

DATA_LOCK = threading.RLock()
TRASH_LOCK = threading.RLock()
USERS_LOCK = threading.RLock()
SESSIONS_LOCK = threading.RLock()
GITHUB_LOCK = threading.RLock()


# ============================================================
# UTILIDADES
# ============================================================

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def now_epoch():
    return time.time()


def clean_id(value):
    return str(value or "").strip()


# ============================================================
# PASSWORDS
# ============================================================

def hash_password(password):
    """
    Genera:

    pbkdf2_sha256$iteraciones$salt$hash
    """

    password = str(password)

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS
    )

    return (
        "pbkdf2_sha256$"
        f"{PASSWORD_HASH_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(password_hash).decode('ascii')}"
    )


def verify_password(password, stored_hash):
    """
    Comprueba una contraseña contra un hash PBKDF2.
    """

    try:

        parts = str(
            stored_hash
        ).split("$")

        if len(parts) != 4:
            return False

        algorithm = parts[0]
        iterations = int(parts[1])
        salt_b64 = parts[2]
        hash_b64 = parts[3]

        if algorithm != "pbkdf2_sha256":
            return False

        salt = base64.b64decode(
            salt_b64
        )

        expected = base64.b64decode(
            hash_b64
        )

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            str(password).encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(
            actual,
            expected
        )

    except Exception:
        return False


def is_password_hash(value):
    return (
        isinstance(value, str)
        and value.startswith(
            "pbkdf2_sha256$"
        )
    )


def verify_user_password(user, password):
    """
    Soporta temporalmente dos formatos:

    1. Nuevo:
       password_hash

    2. Antiguo:
       password

    Si encuentra el formato antiguo y la contraseña
    es correcta, el usuario será migrado automáticamente.
    """

    password_hash = user.get(
        "password_hash"
    )

    if is_password_hash(
        password_hash
    ):

        return (
            verify_password(
                password,
                password_hash
            ),
            False
        )

    # --------------------------------------------------------
    # MIGRACIÓN LEGACY
    # --------------------------------------------------------

    old_password = str(
        user.get(
            "password",
            ""
        )
    )

    if old_password == "":
        return False, False

    if hmac.compare_digest(
        old_password,
        str(password)
    ):

        return True, True

    return False, False


def generate_session_token():
    return secrets.token_urlsafe(
        SESSION_BYTES
    )


# ============================================================
# RATE LIMIT LOGIN
# ============================================================

def get_client_ip(handler):

    try:
        return str(
            handler.client_address[0]
        )

    except Exception:
        return "unknown"


def check_login_rate_limit(ip):

    current = time.time()

    with LOGIN_ATTEMPTS_LOCK:

        record = LOGIN_ATTEMPTS.get(
            ip
        )

        if not record:
            return True, 0

        if (
            current -
            record["first"]
            >
            LOGIN_WINDOW_SECONDS
        ):

            del LOGIN_ATTEMPTS[ip]

            return True, 0

        blocked_until = record.get(
            "blocked_until",
            0
        )

        if blocked_until > current:

            remaining = int(
                blocked_until -
                current
            ) + 1

            return False, remaining

        return True, 0


def register_failed_login(ip):

    current = time.time()

    with LOGIN_ATTEMPTS_LOCK:

        record = LOGIN_ATTEMPTS.get(
            ip
        )

        if not record:

            LOGIN_ATTEMPTS[ip] = {
                "count": 1,
                "first": current,
                "blocked_until": 0
            }

            return

        if (
            current -
            record["first"]
            >
            LOGIN_WINDOW_SECONDS
        ):

            LOGIN_ATTEMPTS[ip] = {
                "count": 1,
                "first": current,
                "blocked_until": 0
            }

            return

        record["count"] += 1

        if (
            record["count"]
            >=
            LOGIN_MAX_ATTEMPTS
        ):

            record["blocked_until"] = (
                current +
                LOGIN_BLOCK_SECONDS
            )


def clear_login_attempts(ip):

    with LOGIN_ATTEMPTS_LOCK:

        LOGIN_ATTEMPTS.pop(
            ip,
            None
        )


# ============================================================
# VALIDAR SESIÓN
# ============================================================

def session_is_valid(session):

    if not isinstance(
        session,
        dict
    ):
        return False

    if session.get(
        "active"
    ) is not True:

        return False

    try:

        created = float(
            session.get(
                "created_at_epoch",
                0
            )
        )

        last_activity = float(
            session.get(
                "last_activity_epoch",
                0
            )
        )

    except Exception:

        return False

    if created <= 0:
        return False

    if last_activity <= 0:
        return False

    current = time.time()

    if (
        current -
        created
        >
        SESSION_MAX_AGE
    ):

        return False

    if (
        current -
        last_activity
        >
        SESSION_IDLE_TIMEOUT
    ):

        return False

    return True


# ============================================================
# GITHUB
# ============================================================

def github_enabled():

    return bool(
        GITHUB_TOKEN
        and
        GITHUB_OWNER
        and
        GITHUB_REPO
    )


def github_path(
    local_filename
):

    relative_name = GITHUB_FILES.get(
        local_filename
    )

    if not relative_name:
        return None

    if GITHUB_PATH_PREFIX:

        return (
            f"{GITHUB_PATH_PREFIX}/"
            f"{relative_name}"
        )

    return relative_name


def github_url(path):

    return (
        f"{GITHUB_API_BASE}/repos/"
        f"{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/contents/"
        f"{path}"
    )


def github_headers():

    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": "CINEMAX-Server"
    }


def github_request(
    method,
    url,
    payload=None,
    timeout=20
):

    body = None

    if payload is not None:

        body = json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")

    request = Request(
        url,
        data=body,
        headers=github_headers(),
        method=method
    )

    try:

        with urlopen(
            request,
            timeout=timeout
        ) as response:

            raw = response.read()

            if not raw:

                return (
                    response.status,
                    {}
                )

            try:

                data = json.loads(
                    raw.decode("utf-8")
                )

            except Exception:

                data = {
                    "raw": raw.decode(
                        "utf-8",
                        errors="replace"
                    )
                }

            return (
                response.status,
                data
            )

    except HTTPError as e:

        try:

            raw = e.read()

            try:

                data = json.loads(
                    raw.decode("utf-8")
                )

            except Exception:

                data = {
                    "raw": raw.decode(
                        "utf-8",
                        errors="replace"
                    )
                }

        except Exception:

            data = {
                "message": str(e)
            }

        return (
            e.code,
            data
        )

    except URLError as e:

        return (
            0,
            {
                "message":
                    f"Error de conexión con GitHub: {e}"
            }
        )

    except Exception as e:

        return (
            0,
            {
                "message": str(e)
            }
        )


def github_get_file(
    local_filename
):

    if not github_enabled():

        return {
            "success": False,
            "enabled": False,
            "error":
                "GitHub no está configurado."
        }

    path = github_path(
        local_filename
    )

    if not path:

        return {
            "success": False,
            "error":
                "Archivo no configurado para GitHub."
        }

    status, response = github_request(
        "GET",
        github_url(path)
    )

    if status == 200:

        encoded = response.get(
            "content",
            ""
        )

        sha = response.get(
            "sha",
            ""
        )

        try:

            encoded = encoded.replace(
                "\n",
                ""
            )

            raw = base64.b64decode(
                encoded
            )

            text = raw.decode(
                "utf-8"
            )

            data = json.loads(
                text
            )

            if not isinstance(
                data,
                list
            ):

                data = []

            return {
                "success": True,
                "sha": sha,
                "content": data
            }

        except Exception as e:

            return {
                "success": False,
                "error":
                    f"No se pudo decodificar {path}: {e}"
            }

    if status == 404:

        return {
            "success": False,
            "not_found": True,
            "status": status,
            "error":
                f"No existe {path} en GitHub."
        }

    return {
        "success": False,
        "status": status,
        "error":
            response.get(
                "message",
                f"GitHub respondió HTTP {status}."
            )
    }


def github_save_json(
    local_filename,
    data,
    commit_message=None,
    retries=3
):

    if not github_enabled():

        return {
            "success": False,
            "enabled": False,
            "error":
                "GitHub no está configurado."
        }

    path = github_path(
        local_filename
    )

    if not path:

        return {
            "success": False,
            "error":
                "Archivo no configurado para GitHub."
        }

    if commit_message is None:

        commit_message = (
            "CINEMAX: actualizar "
            f"{os.path.basename(local_filename)}"
        )

    try:

        text = json.dumps(
            data,
            ensure_ascii=False,
            indent=4
        ) + "\n"

        encoded = base64.b64encode(
            text.encode("utf-8")
        ).decode("ascii")

    except Exception as e:

        return {
            "success": False,
            "error":
                f"No se pudo preparar JSON: {e}"
        }

    url = github_url(path)

    with GITHUB_LOCK:

        for attempt in range(
            retries
        ):

            current = github_get_file(
                local_filename
            )

            sha = None

            if current.get(
                "success"
            ):

                sha = current.get(
                    "sha"
                )

            elif not current.get(
                "not_found"
            ):

                print(
                    "❌ GitHub GET ERROR:",
                    current.get("error")
                )

                return {
                    "success": False,
                    "error":
                        current.get(
                            "error",
                            "No se pudo consultar GitHub."
                        )
                }

            payload = {
                "message": commit_message,
                "content": encoded,
                "branch": GITHUB_BRANCH,
                "committer": {
                    "name":
                        GITHUB_COMMITTER_NAME,
                    "email":
                        GITHUB_COMMITTER_EMAIL
                }
            }

            if sha:
                payload["sha"] = sha

            status, response = github_request(
                "PUT",
                url,
                payload
            )

            if status in (
                200,
                201
            ):

                commit = response.get(
                    "commit",
                    {}
                )

                commit_sha = commit.get(
                    "sha"
                )

                print(
                    "☁️ GITHUB: archivo guardado"
                )

                print(
                    f"   Archivo: {path}"
                )

                print(
                    f"   Commit: {commit_sha or 'OK'}"
                )

                return {
                    "success": True,
                    "path": path,
                    "sha":
                        response.get(
                            "content",
                            {}
                        ).get(
                            "sha"
                        ),
                    "commit_sha":
                        commit_sha
                }

            if status == 409:

                print(
                    "⚠️ GitHub 409: conflicto."
                )

                if attempt < retries - 1:

                    time.sleep(
                        0.5 *
                        (
                            attempt + 1
                        )
                    )

                    continue

            error_message = response.get(
                "message",
                f"GitHub respondió HTTP {status}."
            )

            print(
                "❌ GITHUB SAVE ERROR:",
                error_message
            )

            return {
                "success": False,
                "status": status,
                "error": error_message
            }

    return {
        "success": False,
        "error":
            "No se pudo guardar en GitHub."
    }


def github_restore_file(
    local_filename
):

    if not github_enabled():
        return False

    result = github_get_file(
        local_filename
    )

    if not result.get(
        "success"
    ):

        print(
            "⚠️ GitHub no pudo restaurar:",
            os.path.basename(local_filename),
            result.get("error")
        )

        return False

    data = result.get(
        "content",
        []
    )

    try:

        directory = os.path.dirname(
            local_filename
        )

        os.makedirs(
            directory,
            exist_ok=True
        )

        with open(
            local_filename,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )

            f.write("\n")

        print(
            "☁️ GitHub → local:",
            os.path.basename(
                local_filename
            )
        )

        return True

    except Exception as e:

        print(
            "❌ Error restaurando:",
            e
        )

        return False


def github_initial_sync():

    if not github_enabled():

        print(
            "ℹ️ GitHub Persistence: DESACTIVADA"
        )

        print(
            "   Se utilizará almacenamiento local."
        )

        return

    print()
    print(
        "=========================================="
    )
    print(
        "       ☁️ GITHUB PERSISTENCE"
    )
    print(
        "=========================================="
    )

    print(
        f"Repositorio: {GITHUB_OWNER}/{GITHUB_REPO}"
    )

    print(
        f"Branch:      {GITHUB_BRANCH}"
    )

    print(
        f"Prefijo:     {GITHUB_PATH_PREFIX or '(raíz)'}"
    )

    print()

    github_restore_file(
        DATA_FILE
    )

    github_restore_file(
        TRASH_FILE
    )

    github_restore_file(
        USERS_FILE
    )

    print(
        "🔐 sessions.json: local/temporal"
    )

    print()
    print(
        "=========================================="
    )
    print(
        "       ☁️ GITHUB SYNC COMPLETADO"
    )
    print(
        "=========================================="
    )
    print()


# ============================================================
# HANDLER
# ============================================================

class CinemaXHandler(
    SimpleHTTPRequestHandler
):

    def __init__(
        self,
        *args,
        **kwargs
    ):

        super().__init__(
            *args,
            directory=WEB_DIR,
            **kwargs
        )

    def log_message(
        self,
        fmt,
        *args
    ):

        print(
            f"{self.client_address[0]} - - "
            f"[{self.log_date_time_string()}] "
            f"{fmt % args}"
        )

    # ========================================================
    # JSON
    # ========================================================

    def load_json_file(
        self,
        filename
    ):

        if not os.path.exists(
            filename
        ):

            return []

        try:

            with open(
                filename,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(
                    f
                )

            return (
                data
                if isinstance(
                    data,
                    list
                )
                else []
            )

        except json.JSONDecodeError as e:

            print(
                f"ERROR JSON corrupto en {filename}: {e}"
            )

            return []

        except Exception as e:

            print(
                f"ERROR leyendo {filename}: {e}"
            )

            return []

    def save_json_file(
        self,
        filename,
        data,
        github_commit_message=None
    ):

        os.makedirs(
            os.path.dirname(filename),
            exist_ok=True
        )

        directory = os.path.dirname(
            filename
        )

        basename = os.path.basename(
            filename
        )

        temp = os.path.join(
            directory,
            f"{basename}.{uuid.uuid4().hex}.tmp"
        )

        try:

            with open(
                temp,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

                f.write("\n")

                f.flush()

                try:
                    os.fsync(
                        f.fileno()
                    )
                except Exception:
                    pass

            os.replace(
                temp,
                filename
            )

        except Exception as e:

            print(
                f"ERROR guardando {filename}: {e}"
            )

            try:

                if os.path.exists(temp):
                    os.remove(temp)

            except Exception:
                pass

            return False

        if (
            github_enabled()
            and
            filename in GITHUB_FILES
        ):

            github_result = github_save_json(
                filename,
                data,
                github_commit_message
            )

            if not github_result.get(
                "success"
            ):

                print(
                    "⚠️ LOCAL GUARDADO"
                )

                print(
                    "❌ GITHUB NO GUARDADO:",
                    github_result.get("error")
                )

                return False

        return True

    # ========================================================
    # LOAD
    # ========================================================

    def load_catalog(self):

        with DATA_LOCK:
            return self.load_json_file(
                DATA_FILE
            )

    def load_trash(self):

        with TRASH_LOCK:
            return self.load_json_file(
                TRASH_FILE
            )

    def load_users(self):

        with USERS_LOCK:
            return self.load_json_file(
                USERS_FILE
            )

    def load_sessions(self):

        with SESSIONS_LOCK:
            return self.load_json_file(
                SESSIONS_FILE
            )

    # ========================================================
    # SAVE
    # ========================================================

    def save_catalog(
        self,
        data
    ):

        with DATA_LOCK:

            return self.save_json_file(
                DATA_FILE,
                data,
                "CINEMAX: actualizar catálogo"
            )

    def save_trash(
        self,
        data
    ):

        with TRASH_LOCK:

            return self.save_json_file(
                TRASH_FILE,
                data,
                "CINEMAX: actualizar papelera"
            )

    def save_users(
        self,
        data
    ):

        with USERS_LOCK:

            return self.save_json_file(
                USERS_FILE,
                data,
                "CINEMAX: actualizar usuarios"
            )

    def save_sessions(
        self,
        data
    ):

        with SESSIONS_LOCK:

            return self.save_json_file(
                SESSIONS_FILE,
                data
            )

    # ========================================================
    # RESPUESTA
    # ========================================================

    def send_json(
        self,
        data,
        status=200,
        extra_headers=None
    ):

        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode(
            "utf-8"
        )

        self.send_response(
            status
        )

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.send_header(
            "Cache-Control",
            "no-store, no-cache, must-revalidate, max-age=0"
        )

        self.send_header(
            "Pragma",
            "no-cache"
        )

        self.send_header(
            "Expires",
            "0"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, DELETE, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, X-Session-ID, Authorization, Cache-Control"
        )

        if extra_headers:

            for key, value in extra_headers.items():

                self.send_header(
                    key,
                    value
                )

        self.end_headers()

        try:
            self.wfile.write(body)

        except (
            BrokenPipeError,
            ConnectionResetError
        ):
            pass

    # ========================================================
    # BODY
    # ========================================================

    def read_body(
        self
    ):

        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

        except ValueError:

            length = 0

        if length <= 0:

            raise ValueError(
                "La petición no contiene datos."
            )

        raw = self.rfile.read(
            length
        )

        if not raw:

            raise ValueError(
                "El cuerpo está vacío."
            )

        try:

            data = json.loads(
                raw.decode("utf-8")
            )

        except json.JSONDecodeError:

            raise ValueError(
                "El JSON enviado no es válido."
            )

        if not isinstance(
            data,
            dict
        ):

            raise ValueError(
                "El contenido debe ser un objeto JSON."
            )

        return data

    # ========================================================
    # SESSION ID
    # ========================================================

    def get_session_id_from_request(
        self
    ):

        value = clean_id(
            self.headers.get(
                "X-Session-ID"
            )
        )

        if value:
            return value

        authorization = clean_id(
            self.headers.get(
                "Authorization"
            )
        )

        if authorization.lower().startswith(
            "bearer "
        ):

            token = clean_id(
                authorization[7:]
            )

            if token:
                return token

        cookie = clean_id(
            self.headers.get(
                "Cookie"
            )
        )

        if cookie:

            cookies = {}

            for part in cookie.split(";"):

                if "=" in part:

                    key, value = part.split(
                        "=",
                        1
                    )

                    cookies[
                        key.strip()
                    ] = value.strip()

            for key in (
                "session_id",
                "sessionId",
                "session",
                "sessionID",
                "token"
            ):

                if cookies.get(key):

                    return clean_id(
                        cookies[key]
                    )

        try:

            query = parse_qs(
                urlparse(
                    self.path
                ).query
            )

            for key in (
                "session_id",
                "sessionId",
                "session",
                "sessionID",
                "token"
            ):

                values = query.get(
                    key
                )

                if (
                    values
                    and
                    clean_id(values[0])
                ):

                    return clean_id(
                        values[0]
                    )

        except Exception:
            pass

        return None

    # ========================================================
    # FIND SESSION
    # ========================================================

    def find_session(
        self,
        session_id
    ):

        session_id = clean_id(
            session_id
        )

        if not session_id:
            return None, None

        sessions = self.load_sessions()

        for index, session in enumerate(
            sessions
        ):

            if not isinstance(
                session,
                dict
            ):
                continue

            if hmac.compare_digest(
                clean_id(
                    session.get("id")
                ),
                session_id
            ):

                return session, index

        return None, None

    # ========================================================
    # FIND USER
    # ========================================================

    def find_user_by_id(
        self,
        user_id
    ):

        user_id = clean_id(
            user_id
        )

        if not user_id:
            return None

        users = self.load_users()

        for user in users:

            if not isinstance(
                user,
                dict
            ):
                continue

            if (
                clean_id(
                    user.get("id")
                )
                ==
                user_id
            ):

                return user

        return None

    # ========================================================
    # INVALIDATE
    # ========================================================

    def invalidate_user_sessions(
        self,
        user_id
    ):

        user_id = clean_id(
            user_id
        )

        with SESSIONS_LOCK:

            sessions = self.load_json_file(
                SESSIONS_FILE
            )

            changed = False
            current = now_iso()
            epoch = now_epoch()

            for session in sessions:

                if not isinstance(
                    session,
                    dict
                ):
                    continue

                if (
                    clean_id(
                        session.get("user_id")
                    )
                    ==
                    user_id
                ):

                    if session.get(
                        "active"
                    ) is not False:

                        changed = True

                    session[
                        "active"
                    ] = False

                    session[
                        "last_activity"
                    ] = current

                    session[
                        "last_activity_epoch"
                    ] = epoch

                    session[
                        "disconnected_at"
                    ] = current

            if changed:

                self.save_json_file(
                    SESSIONS_FILE,
                    sessions
                )

            return changed

    # ========================================================
    # CLEAN EXPIRED SESSIONS
    # ========================================================

    def cleanup_expired_sessions(
        self
    ):

        with SESSIONS_LOCK:

            sessions = self.load_json_file(
                SESSIONS_FILE
            )

            changed = False
            current = now_iso()

            for session in sessions:

                if not isinstance(
                    session,
                    dict
                ):
                    continue

                if (
                    session.get("active")
                    is True
                    and
                    not session_is_valid(
                        session
                    )
                ):

                    session[
                        "active"
                    ] = False

                    session[
                        "expired_at"
                    ] = current

                    changed = True

            if changed:

                self.save_json_file(
                    SESSIONS_FILE,
                    sessions
                )

    # ========================================================
    # REQUIRE ADMIN
    # ========================================================

    def require_admin(
        self,
        session_id=None
    ):

        try:

            if not session_id:

                session_id = (
                    self.get_session_id_from_request()
                )

            if not session_id:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Sesión de administrador requerida.",
                        "code":
                            "SESSION_REQUIRED"
                    },
                    401
                )

                return None

            session, index = self.find_session(
                session_id
            )

            if session is None:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Sesión inválida.",
                        "code":
                            "INVALID_SESSION"
                    },
                    401
                )

                return None

            # ------------------------------------------------
            # EXPIRACIÓN
            # ------------------------------------------------

            if not session_is_valid(
                session
            ):

                with SESSIONS_LOCK:

                    sessions = self.load_json_file(
                        SESSIONS_FILE
                    )

                    if (
                        index is not None
                        and
                        index < len(sessions)
                    ):

                        sessions[index][
                            "active"
                        ] = False

                        sessions[index][
                            "expired_at"
                        ] = now_iso()

                        self.save_json_file(
                            SESSIONS_FILE,
                            sessions
                        )

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "La sesión ha expirado.",
                        "code":
                            "SESSION_EXPIRED"
                    },
                    401
                )

                return None

            if session.get(
                "active"
            ) is not True:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "La sesión ha sido cerrada.",
                        "code":
                            "SESSION_INACTIVE"
                    },
                    401
                )

                return None

            user_id = clean_id(
                session.get(
                    "user_id"
                )
            )

            user = self.find_user_by_id(
                user_id
            )

            if user is None:

                self.invalidate_user_sessions(
                    user_id
                )

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Usuario no encontrado.",
                        "code":
                            "USER_NOT_FOUND"
                    },
                    401
                )

                return None

            role = clean_id(
                user.get(
                    "role",
                    "user"
                )
            ).lower()

            if role != "admin":

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Acceso denegado.",
                        "code":
                            "ADMIN_REQUIRED"
                    },
                    403
                )

                return None

            # ------------------------------------------------
            # REFRESCAR ACTIVIDAD
            # ------------------------------------------------

            with SESSIONS_LOCK:

                sessions = self.load_json_file(
                    SESSIONS_FILE
                )

                for stored in sessions:

                    if (
                        clean_id(
                            stored.get("id")
                        )
                        ==
                        session_id
                    ):

                        stored[
                            "last_activity"
                        ] = now_iso()

                        stored[
                            "last_activity_epoch"
                        ] = now_epoch()

                        break

                self.save_json_file(
                    SESSIONS_FILE,
                    sessions
                )

            return user

        except Exception as e:

            print(
                "ERROR comprobando administrador:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error verificando permisos."
                },
                500
            )

            return None

    # ========================================================
    # OPTIONS
    # ========================================================

    def do_OPTIONS(
        self
    ):

        self.send_response(
            204
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, DELETE, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, X-Session-ID, Authorization, Cache-Control"
        )

        self.send_header(
            "Access-Control-Max-Age",
            "86400"
        )

        self.end_headers()

    # ========================================================
    # GET
    # ========================================================

    def do_GET(
        self
    ):

        path = urlparse(
            self.path
        ).path

        if path == "/api/health":

            self.send_json(
                {
                    "success": True,
                    "server": "CINEMAX",
                    "status": "online",
                    "time": now_iso(),
                    "security": {
                        "password_hash":
                            "PBKDF2-SHA256",
                        "session_max_age":
                            SESSION_MAX_AGE,
                        "idle_timeout":
                            SESSION_IDLE_TIMEOUT,
                        "rate_limit":
                            True
                    },
                    "github": {
                        "enabled":
                            github_enabled(),
                        "repository":
                            (
                                f"{GITHUB_OWNER}/{GITHUB_REPO}"
                                if github_enabled()
                                else None
                            ),
                        "branch":
                            (
                                GITHUB_BRANCH
                                if github_enabled()
                                else None
                            )
                    }
                }
            )

            return

        if path == "/api/catalog":

            self.send_json(
                self.load_catalog()
            )

            return

        if path == "/api/trash":

            if not self.require_admin():
                return

            self.send_json(
                self.load_trash()
            )

            return

        if path == "/api/users":

            if not self.require_admin():
                return

            self.send_users()

            return

        if path.startswith(
            "/api/users/session/"
        ):

            session_id = path[
                len("/api/users/session/"):
            ]

            self.check_session(
                session_id
            )

            return

        super().do_GET()

    # ========================================================
    # POST
    # ========================================================

    def do_POST(
        self
    ):

        path = urlparse(
            self.path
        ).path

        if path == "/api/catalog":

            if not self.require_admin():
                return

            self.add_catalog_item()
            return

        if (
            path.startswith("/api/trash/")
            and
            path.endswith("/restore")
        ):

            if not self.require_admin():
                return

            item_id = path[
                len("/api/trash/"):
                -len("/restore")
            ]

            self.restore_trash_item(
                item_id
            )

            return

        if path == "/api/users/register":

            self.user_register()
            return

        if path == "/api/users/login":

            self.user_login()
            return

        if path == "/api/users/logout":

            self.user_logout()
            return

        if (
            path.startswith("/api/users/")
            and
            path.endswith("/disconnect")
        ):

            if not self.require_admin():
                return

            user_id = path[
                len("/api/users/"):
                -len("/disconnect")
            ]

            self.disconnect_user(
                user_id
            )

            return

        self.send_error(
            404,
            "Ruta no encontrada"
        )

    # ========================================================
    # PUT
    # ========================================================

    def do_PUT(
        self
    ):

        path = urlparse(
            self.path
        ).path

        if path.startswith(
            "/api/catalog/"
        ):

            if not self.require_admin():
                return

            self.update_catalog_item(
                path[
                    len("/api/catalog/"):
                ]
            )

            return

        if path.startswith(
            "/api/users/"
        ):

            if path.endswith(
                "/disconnect"
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Ruta no válida."
                    },
                    400
                )

                return

            if not self.require_admin():
                return

            self.update_user(
                path[
                    len("/api/users/"):
                ]
            )

            return

        self.send_error(
            404,
            "Ruta no encontrada"
        )

    # ========================================================
    # DELETE
    # ========================================================

    def do_DELETE(
        self
    ):

        path = urlparse(
            self.path
        ).path

        if path.startswith(
            "/api/catalog/"
        ):

            if not self.require_admin():
                return

            self.delete_catalog_item(
                path[
                    len("/api/catalog/"):
                ]
            )

            return

        if path.startswith(
            "/api/trash/"
        ):

            if not self.require_admin():
                return

            self.permanently_delete_trash_item(
                path[
                    len("/api/trash/"):
                ]
            )

            return

        if path.startswith(
            "/api/users/"
        ):

            if not self.require_admin():
                return

            self.delete_user(
                path[
                    len("/api/users/"):
                ]
            )

            return

        self.send_error(
            404,
            "Ruta no encontrada"
        )

    # ========================================================
    # USERS
    # ========================================================

    def send_users(
        self
    ):

        users = self.load_users()
        sessions = self.load_sessions()

        active_ids = {
            clean_id(
                s.get("user_id")
            )
            for s in sessions
            if (
                isinstance(s, dict)
                and
                s.get("active") is True
                and
                session_is_valid(s)
            )
        }

        result = []

        for user in users:

            if not isinstance(
                user,
                dict
            ):
                continue

            user_id = clean_id(
                user.get("id")
            )

            result.append(
                {
                    "id": user_id,
                    "username":
                        user.get("username", ""),
                    "email":
                        user.get("email", ""),
                    "role":
                        user.get("role", "user"),
                    "connected":
                        user_id in active_ids
                }
            )

        self.send_json(
            result
        )

    # ========================================================
    # REGISTER
    # ========================================================

    def user_register(
        self
    ):

        try:

            data = self.read_body()

            username = clean_id(
                data.get("username")
            )

            email = clean_id(
                data.get("email")
            ).lower()

            password = str(
                data.get(
                    "password",
                    ""
                )
            )

            if len(username) < 3:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "El nombre de usuario debe tener al menos 3 caracteres."
                    },
                    400
                )

                return

            if len(username) > 20:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "El nombre de usuario no puede superar 20 caracteres."
                    },
                    400
                )

                return

            if not email:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "El correo electrónico es obligatorio."
                    },
                    400
                )

                return

            if len(password) < 6:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "La contraseña debe tener al menos 6 caracteres."
                    },
                    400
                )

                return

            users = self.load_users()

            for user in users:

                if (
                    clean_id(
                        user.get("email")
                    ).lower()
                    ==
                    email
                ):

                    self.send_json(
                        {
                            "success": False,
                            "error":
                                "Este correo electrónico ya está registrado."
                        },
                        409
                    )

                    return

                if (
                    clean_id(
                        user.get("username")
                    ).lower()
                    ==
                    username.lower()
                ):

                    self.send_json(
                        {
                            "success": False,
                            "error":
                                "Este nombre de usuario ya está en uso."
                        },
                        409
                    )

                    return

            new_user = {
                "id": str(
                    uuid.uuid4()
                ),
                "username": username,
                "email": email,

                # ====================================================
                # YA NO GUARDAMOS password EN TEXTO PLANO
                # ====================================================

                "password_hash":
                    hash_password(password),

                "role": "user",
                "createdAt": now_iso()
            }

            users.append(
                new_user
            )

            if not self.save_users(
                users
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo guardar el usuario."
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Cuenta creada correctamente.",
                    "user": {
                        "id":
                            new_user["id"],
                        "username":
                            new_user["username"],
                        "email":
                            new_user["email"],
                        "role":
                            new_user["role"]
                    }
                },
                201
            )

        except Exception as e:

            print(
                "ERROR registro:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error": str(e)
                },
                500
            )

    # ========================================================
    # LOGIN
    # ========================================================

    def user_login(
        self
    ):

        ip = get_client_ip(
            self
        )

        allowed, remaining = (
            check_login_rate_limit(ip)
        )

        if not allowed:

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Demasiados intentos de inicio de sesión.",
                    "code":
                        "LOGIN_RATE_LIMIT",
                    "retry_after":
                        remaining
                },
                429,
                {
                    "Retry-After":
                        str(remaining)
                }
            )

            return

        try:

            data = self.read_body()

            email = clean_id(
                data.get("email")
            ).lower()

            password = str(
                data.get(
                    "password",
                    ""
                )
            )

            if (
                not email
                or
                not password
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Correo y contraseña son obligatorios."
                    },
                    400
                )

                return

            users = self.load_users()

            found_user = None
            needs_migration = False

            for user in users:

                if (
                    clean_id(
                        user.get("email")
                    ).lower()
                    !=
                    email
                ):
                    continue

                valid, legacy = (
                    verify_user_password(
                        user,
                        password
                    )
                )

                if valid:

                    found_user = user
                    needs_migration = legacy

                break

            if found_user is None:

                register_failed_login(
                    ip
                )

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Correo electrónico o contraseña incorrectos."
                    },
                    401
                )

                return

            clear_login_attempts(
                ip
            )

            # ====================================================
            # MIGRACIÓN AUTOMÁTICA
            # ====================================================

            if needs_migration:

                print(
                    "🔐 MIGRANDO CONTRASEÑA LEGACY:",
                    found_user.get(
                        "username",
                        ""
                    )
                )

                found_user[
                    "password_hash"
                ] = hash_password(
                    password
                )

                # Eliminamos el password antiguo
                found_user.pop(
                    "password",
                    None
                )

                self.save_users(
                    users
                )

            user_id = clean_id(
                found_user.get("id")
            )

            # ====================================================
            # UNA SOLA SESIÓN
            # ====================================================

            with SESSIONS_LOCK:

                sessions = self.load_json_file(
                    SESSIONS_FILE
                )

                current = now_iso()
                epoch = now_epoch()

                for session in sessions:

                    if (
                        clean_id(
                            session.get(
                                "user_id"
                            )
                        )
                        ==
                        user_id
                    ):

                        session[
                            "active"
                        ] = False

                        session[
                            "replaced_at"
                        ] = current

                session_id = (
                    generate_session_token()
                )

                sessions.append(
                    {
                        "id":
                            session_id,
                        "user_id":
                            user_id,
                        "active":
                            True,
                        "created_at":
                            current,
                        "created_at_epoch":
                            epoch,
                        "last_activity":
                            current,
                        "last_activity_epoch":
                            epoch
                    }
                )

                saved = self.save_json_file(
                    SESSIONS_FILE,
                    sessions
                )

            if not saved:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo crear la sesión."
                    },
                    500
                )

                return

            print()
            print(
                "=========================================="
            )
            print(
                "          ✅ LOGIN CORRECTO"
            )
            print(
                "=========================================="
            )

            print(
                "Usuario:",
                found_user.get(
                    "username",
                    ""
                )
            )

            print(
                "Email:",
                found_user.get(
                    "email",
                    ""
                )
            )

            print(
                "Role:",
                found_user.get(
                    "role",
                    "user"
                )
            )

            print(
                "🔐 Autenticación:",
                "PBKDF2-SHA256"
            )

            print(
                "🔑 Sesión:",
                "token seguro generado"
            )

            print(
                "=========================================="
            )
            print()

            # ====================================================
            # COOKIE HTTPONLY
            # ====================================================

            cookie = (
                "session_id="
                + session_id
                + "; Path=/; HttpOnly; SameSite=Lax"
            )

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Inicio de sesión correcto.",
                    "session_id":
                        session_id,
                    "sessionId":
                        session_id,
                    "token":
                        session_id,
                    "user": {
                        "id":
                            user_id,
                        "username":
                            found_user.get(
                                "username",
                                ""
                            ),
                        "email":
                            found_user.get(
                                "email",
                                ""
                            ),
                        "role":
                            found_user.get(
                                "role",
                                "user"
                            )
                    }
                },
                200,
                {
                    "Set-Cookie":
                        cookie
                }
            )

        except Exception as e:

            print(
                "ERROR login:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error interno durante el inicio de sesión."
                },
                500
            )

    # ========================================================
    # CHECK SESSION
    # ========================================================

    def check_session(
        self,
        session_id
    ):

        try:

            session_id = (
                clean_id(session_id)
                or
                self.get_session_id_from_request()
            )

            if not session_id:

                self.send_json(
                    {
                        "success": False,
                        "active": False,
                        "error":
                            "Sesión no especificada."
                    },
                    400
                )

                return

            session, index = self.find_session(
                session_id
            )

            if session is None:

                self.send_json(
                    {
                        "success": False,
                        "active": False,
                        "error":
                            "Sesión inválida.",
                        "code":
                            "INVALID_SESSION"
                    },
                    401
                )

                return

            if not session_is_valid(
                session
            ):

                with SESSIONS_LOCK:

                    sessions = self.load_json_file(
                        SESSIONS_FILE
                    )

                    if (
                        index is not None
                        and
                        index < len(sessions)
                    ):

                        sessions[index][
                            "active"
                        ] = False

                        sessions[index][
                            "expired_at"
                        ] = now_iso()

                        self.save_json_file(
                            SESSIONS_FILE,
                            sessions
                        )

                self.send_json(
                    {
                        "success": False,
                        "active": False,
                        "error":
                            "La sesión ha expirado.",
                        "code":
                            "SESSION_EXPIRED"
                    },
                    401
                )

                return

            user_id = clean_id(
                session.get("user_id")
            )

            user = self.find_user_by_id(
                user_id
            )

            if user is None:

                self.invalidate_user_sessions(
                    user_id
                )

                self.send_json(
                    {
                        "success": False,
                        "active": False,
                        "error":
                            "El usuario ya no existe.",
                        "code":
                            "USER_NOT_FOUND"
                    },
                    401
                )

                return

            # Actualizar actividad
            with SESSIONS_LOCK:

                sessions = self.load_json_file(
                    SESSIONS_FILE
                )

                for stored in sessions:

                    if (
                        clean_id(
                            stored.get("id")
                        )
                        ==
                        session_id
                    ):

                        stored[
                            "last_activity"
                        ] = now_iso()

                        stored[
                            "last_activity_epoch"
                        ] = now_epoch()

                        break

                self.save_json_file(
                    SESSIONS_FILE,
                    sessions
                )

            self.send_json(
                {
                    "success": True,
                    "active": True,
                    "session_id":
                        session_id,
                    "sessionId":
                        session_id,
                    "token":
                        session_id,
                    "user": {
                        "id":
                            user_id,
                        "username":
                            user.get(
                                "username",
                                ""
                            ),
                        "email":
                            user.get(
                                "email",
                                ""
                            ),
                        "role":
                            user.get(
                                "role",
                                "user"
                            )
                    }
                }
            )

        except Exception as e:

            print(
                "ERROR comprobando sesión:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "active": False,
                    "error":
                        "Error comprobando sesión."
                },
                500
            )

    # ========================================================
    # LOGOUT
    # ========================================================

    def user_logout(
        self
    ):

        try:

            session_id = (
                self.get_session_id_from_request()
            )

            if not session_id:

                try:

                    data = self.read_body()

                    session_id = clean_id(
                        data.get(
                            "session_id",
                            data.get(
                                "sessionId",
                                data.get(
                                    "token",
                                    ""
                                )
                            )
                        )
                    )

                except Exception:
                    pass

            if not session_id:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Sesión no especificada."
                    },
                    400
                )

                return

            with SESSIONS_LOCK:

                sessions = self.load_json_file(
                    SESSIONS_FILE
                )

                found = False

                current = now_iso()
                epoch = now_epoch()

                for session in sessions:

                    if (
                        hmac.compare_digest(
                            clean_id(
                                session.get("id")
                            ),
                            session_id
                        )
                    ):

                        session[
                            "active"
                        ] = False

                        session[
                            "last_activity"
                        ] = current

                        session[
                            "last_activity_epoch"
                        ] = epoch

                        session[
                            "logout_at"
                        ] = current

                        found = True

                        break

                if found:

                    self.save_json_file(
                        SESSIONS_FILE,
                        sessions
                    )

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Sesión cerrada."
                },
                200,
                {
                    "Set-Cookie":
                        "session_id=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
                }
            )

        except Exception as e:

            print(
                "ERROR logout:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error cerrando sesión."
                },
                500
            )

    # ========================================================
    # DESCONECTAR
    # ========================================================

    def disconnect_user(
        self,
        user_id
    ):

        try:

            user_id = clean_id(
                user_id
            )

            user = self.find_user_by_id(
                user_id
            )

            if user is None:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Usuario no encontrado."
                    },
                    404
                )

                return

            with SESSIONS_LOCK:

                sessions = self.load_json_file(
                    SESSIONS_FILE
                )

                found = False
                current = now_iso()

                for session in sessions:

                    if (
                        clean_id(
                            session.get("user_id")
                        )
                        ==
                        user_id
                    ):

                        session[
                            "active"
                        ] = False

                        session[
                            "disconnected_at"
                        ] = current

                        found = True

                if found:

                    self.save_json_file(
                        SESSIONS_FILE,
                        sessions
                    )

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Usuario desconectado correctamente.",
                    "user_id":
                        user_id,
                    "sessions_invalidated":
                        found
                }
            )

        except Exception as e:

            print(
                "ERROR desconectando:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error desconectando usuario."
                },
                500
            )

    # ========================================================
    # UPDATE USER
    # ========================================================

    def update_user(
        self,
        user_id
    ):

        try:

            data = self.read_body()

            users = self.load_users()

            found = None
            index = -1

            for i, user in enumerate(
                users
            ):

                if (
                    clean_id(
                        user.get("id")
                    )
                    ==
                    clean_id(user_id)
                ):

                    found = user
                    index = i
                    break

            if found is None:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Usuario no encontrado."
                    },
                    404
                )

                return

            if "username" in data:

                username = clean_id(
                    data["username"]
                )

                if (
                    len(username) < 3
                    or
                    len(username) > 20
                ):

                    self.send_json(
                        {
                            "success": False,
                            "error":
                                "El nombre de usuario debe tener entre 3 y 20 caracteres."
                        },
                        400
                    )

                    return

                for user in users:

                    if (
                        clean_id(
                            user.get("id")
                        )
                        !=
                        clean_id(user_id)
                        and
                        clean_id(
                            user.get("username")
                        ).lower()
                        ==
                        username.lower()
                    ):

                        self.send_json(
                            {
                                "success": False,
                                "error":
                                    "Este nombre de usuario ya está en uso."
                            },
                            409
                        )

                        return

                found[
                    "username"
                ] = username

            if "email" in data:

                email = clean_id(
                    data["email"]
                ).lower()

                if not email:

                    self.send_json(
                        {
                            "success": False,
                            "error":
                                "El correo electrónico es obligatorio."
                        },
                        400
                    )

                    return

                for user in users:

                    if (
                        clean_id(
                            user.get("id")
                        )
                        !=
                        clean_id(user_id)
                        and
                        clean_id(
                            user.get("email")
                        ).lower()
                        ==
                        email
                    ):

                        self.send_json(
                            {
                                "success": False,
                                "error":
                                    "Este correo electrónico ya está registrado."
                            },
                            409
                        )

                        return

                found[
                    "email"
                ] = email

            if "password" in data:

                password = str(
                    data["password"]
                )

                if len(password) < 6:

                    self.send_json(
                        {
                            "success": False,
                            "error":
                                "La contraseña debe tener al menos 6 caracteres."
                        },
                        400
                    )

                    return

                found[
                    "password_hash"
                ] = hash_password(
                    password
                )

                found.pop(
                    "password",
                    None
                )

            if "role" in data:

                role = clean_id(
                    data["role"]
                ).lower()

                if role in (
                    "user",
                    "admin"
                ):

                    found[
                        "role"
                    ] = role

            users[index] = found

            if not self.save_users(
                users
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo guardar el usuario."
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Usuario actualizado correctamente.",
                    "user": {
                        "id":
                            found.get("id", ""),
                        "username":
                            found.get("username", ""),
                        "email":
                            found.get("email", ""),
                        "role":
                            found.get("role", "user")
                    }
                }
            )

        except Exception as e:

            print(
                "ERROR actualizando usuario:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error actualizando usuario."
                },
                500
            )

    # ========================================================
    # DELETE USER
    # ========================================================

    def delete_user(
        self,
        user_id
    ):

        try:

            user_id = clean_id(
                user_id
            )

            users = self.load_users()

            found = next(
                (
                    u
                    for u in users
                    if (
                        clean_id(
                            u.get("id")
                        )
                        ==
                        user_id
                    )
                ),
                None
            )

            if found is None:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Usuario no encontrado."
                    },
                    404
                )

                return

            new_users = [
                u
                for u in users
                if (
                    clean_id(
                        u.get("id")
                    )
                    !=
                    user_id
                )
            ]

            if not self.save_users(
                new_users
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo eliminar el usuario."
                    },
                    500
                )

                return

            self.invalidate_user_sessions(
                user_id
            )

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Usuario eliminado correctamente.",
                    "user_id":
                        user_id
                }
            )

        except Exception as e:

            print(
                "ERROR eliminando usuario:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error eliminando usuario."
                },
                500
            )

    # ========================================================
    # CATÁLOGO
    # ========================================================

    def add_catalog_item(
        self
    ):

        try:

            item = self.read_body()

            catalog = self.load_catalog()

            if (
                not item.get("title")
                and
                item.get("name")
            ):

                item["title"] = item["name"]

            if not item.get("id"):

                title = clean_id(
                    item.get(
                        "title",
                        "contenido"
                    )
                ).lower()

                base = title.replace(
                    " ",
                    "-"
                )

                base = "".join(
                    c
                    for c in base
                    if (
                        c.isalnum()
                        or
                        c in "-_"
                    )
                )

                base = (
                    base
                    or
                    "contenido"
                )

                new_id = base
                counter = 2

                ids = {
                    clean_id(
                        x.get("id")
                    )
                    for x in catalog
                    if x.get("id")
                }

                while new_id in ids:

                    new_id = (
                        f"{base}-{counter}"
                    )

                    counter += 1

                item["id"] = new_id

            item_id = clean_id(
                item.get("id")
            )

            if any(
                clean_id(
                    x.get("id")
                )
                ==
                item_id
                for x in catalog
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Ya existe un contenido con ese ID."
                    },
                    409
                )

                return

            catalog.append(
                item
            )

            if not self.save_catalog(
                catalog
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo guardar el catálogo."
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Contenido agregado",
                    "item":
                        item
                },
                201
            )

        except Exception as e:

            print(
                "ERROR agregando catálogo:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error agregando contenido."
                },
                500
            )

    def update_catalog_item(
        self,
        item_id
    ):

        try:

            data = self.read_body()

            catalog = self.load_catalog()

            item_id = clean_id(
                item_id
            )

            for i, item in enumerate(
                catalog
            ):

                if (
                    clean_id(
                        item.get("id")
                    )
                    ==
                    item_id
                ):

                    if (
                        not data.get("title")
                        and
                        data.get("name")
                    ):

                        data["title"] = data["name"]

                    merged = {
                        **item,
                        **data
                    }

                    merged["id"] = item.get(
                        "id"
                    )

                    catalog[i] = merged

                    if not self.save_catalog(
                        catalog
                    ):

                        self.send_json(
                            {
                                "success": False,
                                "error":
                                    "No se pudo guardar el catálogo."
                            },
                            500
                        )

                        return

                    self.send_json(
                        {
                            "success": True,
                            "message":
                                "Contenido actualizado",
                            "item":
                                merged
                        }
                    )

                    return

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Contenido no encontrado"
                },
                404
            )

        except Exception as e:

            print(
                "ERROR actualizando catálogo:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error actualizando catálogo."
                },
                500
            )

    def delete_catalog_item(
        self,
        item_id
    ):

        try:

            item_id = clean_id(
                item_id
            )

            catalog = self.load_catalog()
            trash = self.load_trash()

            found = None
            new_catalog = []

            for item in catalog:

                if (
                    clean_id(
                        item.get("id")
                    )
                    ==
                    item_id
                ):

                    found = dict(item)

                else:

                    new_catalog.append(
                        item
                    )

            if found is None:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Contenido no encontrado"
                    },
                    404
                )

                return

            trash = [
                x
                for x in trash
                if (
                    clean_id(
                        x.get("id")
                    )
                    !=
                    item_id
                )
            ]

            found["deletedAt"] = now_iso()

            trash.append(
                found
            )

            if not self.save_catalog(
                new_catalog
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo actualizar el catálogo."
                    },
                    500
                )

                return

            if not self.save_trash(
                trash
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo guardar la papelera."
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Contenido movido a la papelera",
                    "item":
                        found
                }
            )

        except Exception as e:

            print(
                "ERROR eliminando catálogo:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error eliminando contenido."
                },
                500
            )

    def restore_trash_item(
        self,
        item_id
    ):

        try:

            item_id = clean_id(
                item_id
            )

            catalog = self.load_catalog()
            trash = self.load_trash()

            found = None
            new_trash = []

            for item in trash:

                if (
                    clean_id(
                        item.get("id")
                    )
                    ==
                    item_id
                ):

                    found = dict(item)

                else:

                    new_trash.append(
                        item
                    )

            if found is None:

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Contenido no encontrado en la papelera."
                    },
                    404
                )

                return

            if any(
                clean_id(
                    x.get("id")
                )
                ==
                item_id
                for x in catalog
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Ya existe un contenido con ese ID."
                    },
                    409
                )

                return

            found.pop(
                "deletedAt",
                None
            )

            catalog.append(
                found
            )

            if not self.save_catalog(
                catalog
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo restaurar."
                    },
                    500
                )

                return

            if not self.save_trash(
                new_trash
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo actualizar la papelera."
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Contenido recuperado correctamente",
                    "item":
                        found
                }
            )

        except Exception as e:

            print(
                "ERROR restaurando:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error restaurando contenido."
                },
                500
            )

    def permanently_delete_trash_item(
        self,
        item_id
    ):

        try:

            item_id = clean_id(
                item_id
            )

            trash = self.load_trash()

            new_trash = [
                x
                for x in trash
                if (
                    clean_id(
                        x.get("id")
                    )
                    !=
                    item_id
                )
            ]

            if len(new_trash) == len(
                trash
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "Contenido no encontrado en la papelera."
                    },
                    404
                )

                return

            if not self.save_trash(
                new_trash
            ):

                self.send_json(
                    {
                        "success": False,
                        "error":
                            "No se pudo eliminar definitivamente."
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message":
                        "Contenido eliminado definitivamente",
                    "id":
                        item_id
                }
            )

        except Exception as e:

            print(
                "ERROR eliminando definitivamente:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error":
                        "Error eliminando definitivamente."
                },
                500
            )


# ============================================================
# SERVER
# ============================================================

class CinemaXServer(
    ThreadingHTTPServer
):

    allow_reuse_address = True


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    print(
        "🔥🔥🔥 CINEMAX SERVER.PY EJECUTADO 🔥🔥🔥",
        flush=True
    )

    os.makedirs(
        CINEMA_DIR,
        exist_ok=True
    )

    print()
    print(
        "=========================================="
    )
    print(
        "        CINEMAX PYTHON SERVER"
    )
    print(
        "             🔐 BLINDADO"
    )
    print(
        "=========================================="
    )
    print()

    print(
        f"Servidor: http://{HOST}:{PORT}"
    )

    print(
        f"Web:      {WEB_DIR}"
    )

    print(
        f"Cinema:   {CINEMA_DIR}"
    )

    print(
        f"Catálogo: {DATA_FILE}"
    )

    print(
        f"Papelera: {TRASH_FILE}"
    )

    print(
        f"Usuarios: {USERS_FILE}"
    )

    print(
        f"Sesiones: {SESSIONS_FILE}"
    )

    print()

    if github_enabled():

        print(
            "☁️ GITHUB: ACTIVADO"
        )

        print(
            f"   Repo: {GITHUB_OWNER}/{GITHUB_REPO}"
        )

        print(
            f"   Branch: {GITHUB_BRANCH}"
        )

        print(
            f"   Path: {GITHUB_PATH_PREFIX or '(raíz)'}"
        )

    else:

        print(
            "☁️ GITHUB: DESACTIVADO"
        )

    print()

    github_initial_sync()

    print(
        "=========================================="
    )

    print(
        "🔐 AUTENTICACIÓN: ACTIVADA"
    )

    print(
        "   Passwords: PBKDF2-SHA256"
    )

    print(
        "   Sesiones: tokens criptográficos"
    )

    print(
        "   Expiración: 7 días"
    )

    print(
        "   Inactividad: 4 horas"
    )

    print(
        "   Rate limit: ACTIVADO"
    )

    print(
        "   Migración legacy: ACTIVADA"
    )

    print(
        "=========================================="
    )

    print(
        "🎬 CATÁLOGO: ACTIVADO"
    )

    print(
        "👤 USUARIOS: ACTIVADO"
    )

    print(
        "🗑️ PAPELERA: ACTIVADA"
    )

    print(
        "❤️ HEALTH: ACTIVADO"
    )

    print(
        "🔌 DESCONEXIÓN: ACTIVADA"
    )

    print(
        "💾 GITHUB: "
        + (
            "ACTIVADO"
            if github_enabled()
            else "LOCAL"
        )
    )

    print()

    print(
        "Servidor iniciado correctamente."
    )

    print(
        "=========================================="
    )

    print()

    server = CinemaXServer(
        (HOST, PORT),
        CinemaXHandler
    )

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print()
        print(
            "Servidor detenido."
        )

    finally:

        server.server_close()
