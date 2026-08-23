import json
import os
import threading
import uuid
import time
import base64
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
# GITHUB - CONFIGURACIÓN
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
# GITHUB - ARCHIVOS PERSISTENTES
#
# sessions.json NO se sincroniza con GitHub.
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

# Importante:
# GitHub exige que las operaciones de actualización
# de archivos sean seriales.
GITHUB_LOCK = threading.RLock()


# ============================================================
# UTILIDADES
# ============================================================

def now_iso():
    return datetime.now(timezone.utc).isoformat()


def clean_id(value):
    return str(value or "").strip()


# ============================================================
# GITHUB - ESTADO
# ============================================================

def github_enabled():
    """
    Devuelve True únicamente cuando están configuradas
    las variables necesarias para usar GitHub.
    """

    return bool(
        GITHUB_TOKEN
        and GITHUB_OWNER
        and GITHUB_REPO
    )


def github_path(local_filename):
    """
    Convierte:

        C:\\...\\Cinema-main\\data.json

    en:

        Cinema-main/data.json
    """

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
    """
    Construye la URL de la API de GitHub.
    """

    return (
        f"{GITHUB_API_BASE}/repos/"
        f"{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/contents/"
        f"{path}"
    )


def github_headers():
    """
    Headers utilizados por GitHub.
    """

    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "User-Agent": "CINEMAX-Server"
    }


# ============================================================
# GITHUB - REQUEST
# ============================================================

def github_request(
    method,
    url,
    payload=None,
    timeout=20
):
    """
    Realiza una petición HTTP a GitHub.

    No utiliza requests para que el servidor
    pueda funcionar sin instalar dependencias adicionales.
    """

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
                "message": (
                    f"Error de conexión con GitHub: {e}"
                )
            }
        )

    except Exception as e:

        return (
            0,
            {
                "message": str(e)
            }
        )


# ============================================================
# GITHUB - LEER ARCHIVO
# ============================================================

def github_get_file(
    local_filename
):
    """
    Obtiene un archivo JSON desde GitHub.

    Devuelve:

        {
            "success": True,
            "sha": "...",
            "content": [...]
        }

    o:

        {
            "success": False,
            ...
        }
    """

    if not github_enabled():

        return {
            "success": False,
            "enabled": False,
            "error": (
                "GitHub no está configurado."
            )
        }

    path = github_path(
        local_filename
    )

    if not path:

        return {
            "success": False,
            "error": (
                "Archivo no configurado "
                "para persistencia GitHub."
            )
        }

    url = github_url(path)

    status, response = github_request(
        "GET",
        url
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

            # GitHub puede devolver saltos de línea
            # dentro del Base64.
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
                "error": (
                    "No se pudo decodificar "
                    f"{path}: {e}"
                )
            }

    if status == 404:

        return {
            "success": False,
            "not_found": True,
            "status": status,
            "error": (
                f"No existe {path} en GitHub."
            )
        }

    return {
        "success": False,
        "status": status,
        "error": (
            response.get(
                "message",
                f"GitHub respondió HTTP {status}."
            )
        )
    }


# ============================================================
# GITHUB - OBTENER SHA
# ============================================================

def github_get_sha(
    local_filename
):
    """
    Obtiene exclusivamente el SHA actual del archivo.
    """

    result = github_get_file(
        local_filename
    )

    if not result.get("success"):

        return None

    return result.get(
        "sha"
    )


# ============================================================
# GITHUB - CREAR / ACTUALIZAR JSON
# ============================================================

def github_save_json(
    local_filename,
    data,
    commit_message=None,
    retries=3
):
    """
    Guarda un JSON en GitHub.

    GitHub exige el SHA actual para actualizar
    un archivo existente.

    Si hay conflicto 409:
        vuelve a obtener SHA
        y reintenta.
    """

    if not github_enabled():

        return {
            "success": False,
            "enabled": False,
            "error": (
                "GitHub no está configurado."
            )
        }

    path = github_path(
        local_filename
    )

    if not path:

        return {
            "success": False,
            "error": (
                "Archivo no configurado "
                "para persistencia GitHub."
            )
        }

    if commit_message is None:

        commit_message = (
            "CINEMAX: actualizar "
            f"{os.path.basename(local_filename)}"
        )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

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
            "error": (
                f"No se pudo preparar JSON: {e}"
            )
        }

    url = github_url(path)

    # --------------------------------------------------------
    # LOCK GITHUB
    # --------------------------------------------------------

    with GITHUB_LOCK:

        for attempt in range(
            retries
        ):

            # -----------------------------------------------
            # Obtener SHA actual
            # -----------------------------------------------

            current = github_get_file(
                local_filename
            )

            sha = None

            if current.get("success"):

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
                    "error": current.get(
                        "error",
                        "No se pudo consultar GitHub."
                    )
                }

            # -----------------------------------------------
            # Payload
            # -----------------------------------------------

            payload = {
                "message": commit_message,
                "content": encoded,
                "branch": GITHUB_BRANCH,
                "committer": {
                    "name": GITHUB_COMMITTER_NAME,
                    "email": GITHUB_COMMITTER_EMAIL
                }
            }

            # Si existe, GitHub exige SHA.
            if sha:

                payload["sha"] = sha

            # -----------------------------------------------
            # PUT
            # -----------------------------------------------

            status, response = github_request(
                "PUT",
                url,
                payload
            )

            # -----------------------------------------------
            # ÉXITO
            # -----------------------------------------------

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

                print()
                print(
                    "☁️ GITHUB: archivo guardado"
                )
                print(
                    f"   Archivo: {path}"
                )
                print(
                    f"   Commit:  {commit_sha or 'OK'}"
                )
                print()

                return {
                    "success": True,
                    "path": path,
                    "sha": response.get(
                        "content",
                        {}
                    ).get(
                        "sha"
                    ),
                    "commit_sha": commit_sha
                }

            # -----------------------------------------------
            # CONFLICTO
            # -----------------------------------------------

            if status == 409:

                print(
                    "⚠️ GitHub 409: conflicto."
                )

                if attempt < retries - 1:

                    time.sleep(
                        0.5 * (
                            attempt + 1
                        )
                    )

                    continue

            # -----------------------------------------------
            # ERROR
            # -----------------------------------------------

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
        "error": (
            "No se pudo guardar el archivo "
            "en GitHub después de varios intentos."
        )
    }


# ============================================================
# GITHUB - SINCRONIZACIÓN INICIAL
# ============================================================

def github_restore_file(
    local_filename
):
    """
    Descarga un archivo persistente desde GitHub
    y lo guarda localmente.

    Se utiliza durante el arranque de Render.
    """

    if not github_enabled():

        return False

    result = github_get_file(
        local_filename
    )

    if not result.get("success"):

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
            "❌ Error restaurando",
            local_filename,
            ":",
            e
        )

        return False


def github_initial_sync():
    """
    Sincroniza al arrancar el servidor:

        GitHub → Render

    Únicamente los archivos persistentes.
    """

    if not github_enabled():

        print()
        print(
            "ℹ️ GitHub Persistence: DESACTIVADA"
        )
        print(
            "   Se utilizará almacenamiento local."
        )
        print()

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

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    github_restore_file(
        DATA_FILE
    )

    # --------------------------------------------------------
    # TRASH
    # --------------------------------------------------------

    github_restore_file(
        TRASH_FILE
    )

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    github_restore_file(
        USERS_FILE
    )

    # --------------------------------------------------------
    # SESSIONS
    # --------------------------------------------------------

    # NO se restaura desde GitHub.
    #
    # Las sesiones son temporales y se regeneran
    # después de reiniciar Render.

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
    # JSON - LECTURA
    # ========================================================

    def load_json_file(
        self,
        filename
    ):

        """
        Lee un JSON de forma segura.

        Si el archivo no existe:
            devuelve []

        Si hay error:
            intenta leer un .tmp reciente.

        Nunca hace que el servidor se caiga
        por un JSON corrupto.
        """

        if not os.path.exists(
            filename
        ):

            temp_candidates = []

            directory = os.path.dirname(
                filename
            )

            basename = os.path.basename(
                filename
            )

            if os.path.exists(
                directory
            ):

                try:

                    for name in os.listdir(
                        directory
                    ):

                        if (
                            name.startswith(
                                basename + "."
                            )
                            and
                            name.endswith(
                                ".tmp"
                            )
                        ):

                            temp_candidates.append(
                                os.path.join(
                                    directory,
                                    name
                                )
                            )

                except Exception:
                    pass

            if temp_candidates:

                try:

                    temp_candidates.sort(
                        key=lambda x:
                        os.path.getmtime(x),
                        reverse=True
                    )

                    with open(
                        temp_candidates[0],
                        "r",
                        encoding="utf-8"
                    ) as f:

                        data = json.load(
                            f
                        )

                    if isinstance(
                        data,
                        list
                    ):

                        return data

                except Exception:
                    pass

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
                f"ERROR JSON corrupto "
                f"en {filename}: {e}"
            )

            return []

        except PermissionError as e:

            print(
                f"ERROR permiso leyendo "
                f"{filename}: {e}"
            )

            return []

        except Exception as e:

            print(
                f"ERROR leyendo "
                f"{filename}: {e}"
            )

            return []

    # ========================================================
    # JSON - ESCRITURA SEGURA
    # ========================================================

    def save_json_file(
        self,
        filename,
        data,
        github_commit_message=None
    ):

        """
        Escritura segura local + GitHub.

        Para archivos persistentes:

            Local
              ↓
            GitHub

        sessions.json NO se sube a GitHub.
        """

        os.makedirs(
            os.path.dirname(
                filename
            ),
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

        last_error = None

        # ----------------------------------------------------
        # LOCAL
        # ----------------------------------------------------

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

            for attempt in range(
                5
            ):

                try:

                    os.replace(
                        temp,
                        filename
                    )

                    last_error = None

                    break

                except PermissionError as e:

                    last_error = e

                    if attempt < 4:

                        time.sleep(
                            0.15
                        )

            if last_error:

                raise last_error

        except Exception as e:

            print(
                f"ERROR guardando "
                f"{filename}: {e}"
            )

            try:

                if os.path.exists(
                    temp
                ):

                    os.remove(
                        temp
                    )

            except Exception:
                pass

            return False

        # ----------------------------------------------------
        # GITHUB
        # ----------------------------------------------------

        if (
            github_enabled()
            and filename in GITHUB_FILES
        ):

            github_result = github_save_json(
                filename,
                data,
                github_commit_message
            )

            if not github_result.get(
                "success"
            ):

                print()
                print(
                    "⚠️ LOCAL GUARDADO"
                )
                print(
                    "❌ GITHUB NO GUARDADO"
                )
                print(
                    "Archivo:",
                    filename
                )
                print(
                    "Error:",
                    github_result.get(
                        "error"
                    )
                )
                print()

                # Muy importante:
                # devolvemos False para que el panel
                # sepa que la persistencia completa
                # no terminó correctamente.

                return False

        return True

    # ========================================================
    # ARCHIVOS
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
    # GUARDADOS
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

            # sessions.json NO va a GitHub.
            return self.save_json_file(
                SESSIONS_FILE,
                data
            )

    # ========================================================
    # RESPUESTA JSON
    # ========================================================

    def send_json(
        self,
        data,
        status=200
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

        self.end_headers()

        try:

            self.wfile.write(
                body
            )

        except BrokenPipeError:
            pass

        except ConnectionResetError:
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
                "El cuerpo de la petición está vacío."
            )

        try:

            data = json.loads(
                raw.decode(
                    "utf-8"
                )
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
    # SESIONES
    # ========================================================

    def get_session_id_from_request(
        self
    ):

        # ----------------------------------------------------
        # X-Session-ID
        # ----------------------------------------------------

        value = clean_id(
            self.headers.get(
                "X-Session-ID"
            )
        )

        if value:

            return value

        # ----------------------------------------------------
        # Authorization Bearer
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Cookie
        # ----------------------------------------------------

        cookie = clean_id(
            self.headers.get(
                "Cookie"
            )
        )

        if cookie:

            cookies = {}

            for part in cookie.split(
                ";"
            ):

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

                if cookies.get(
                    key
                ):

                    return clean_id(
                        cookies[key]
                    )

        # ----------------------------------------------------
        # Query
        # ----------------------------------------------------

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
                    clean_id(
                        values[0]
                    )
                ):

                    return clean_id(
                        values[0]
                    )

        except Exception:
            pass

        return None

    # ========================================================
    # BUSCAR SESIÓN
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

            if (
                clean_id(
                    session.get("id")
                )
                == session_id
            ):

                return (
                    session,
                    index
                )

        return None, None

    # ========================================================
    # BUSCAR USUARIO
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
                == user_id
            ):

                return user

        return None

    # ========================================================
    # INVALIDAR SESIONES
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

            current_time = now_iso()

            for session in sessions:

                if not isinstance(
                    session,
                    dict
                ):

                    continue

                if (
                    clean_id(
                        session.get(
                            "user_id"
                        )
                    )
                    == user_id
                ):

                    if (
                        session.get(
                            "active"
                        )
                        is not False
                    ):

                        changed = True

                    session[
                        "active"
                    ] = False

                    session[
                        "last_activity"
                    ] = current_time

                    session[
                        "disconnected_at"
                    ] = current_time

            if changed:

                self.save_json_file(
                    SESSIONS_FILE,
                    sessions
                )

            return changed

    # ========================================================
    # ADMIN
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
                        "error": (
                            "Sesión de administrador requerida."
                        ),
                        "code": "SESSION_REQUIRED"
                    },
                    401
                )

                return None

            session, _ = self.find_session(
                session_id
            )

            if session is None:

                self.send_json(
                    {
                        "success": False,
                        "error": "Sesión inválida.",
                        "code": "INVALID_SESSION"
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
                        "error": "La sesión ha sido cerrada.",
                        "code": "SESSION_INACTIVE"
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
                        "error": "Usuario no encontrado.",
                        "code": "USER_NOT_FOUND"
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
                        "error": (
                            "Acceso denegado. "
                            "Se requiere una cuenta de administrador."
                        ),
                        "code": "ADMIN_REQUIRED"
                    },
                    403
                )

                return None

            return user

        except Exception as e:

            print(
                "ERROR comprobando administrador:",
                e
            )

            self.send_json(
                {
                    "success": False,
                    "error": "Error verificando permisos.",
                    "details": str(e)
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

        # ----------------------------------------------------
        # HEALTH
        # ----------------------------------------------------

        if path == "/api/health":

            self.send_json(
                {
                    "success": True,
                    "server": "CINEMAX",
                    "status": "online",
                    "time": now_iso(),
                    "github": {
                        "enabled": github_enabled(),
                        "repository": (
                            f"{GITHUB_OWNER}/{GITHUB_REPO}"
                            if github_enabled()
                            else None
                        ),
                        "branch": (
                            GITHUB_BRANCH
                            if github_enabled()
                            else None
                        )
                    }
                }
            )

            return

        # ----------------------------------------------------
        # CATÁLOGO
        # ----------------------------------------------------

        if path == "/api/catalog":

            self.send_json(
                self.load_catalog()
            )

            return

        # ----------------------------------------------------
        # PAPELERA
        # ----------------------------------------------------

        if path == "/api/trash":

            if not self.require_admin():

                return

            self.send_json(
                self.load_trash()
            )

            return

        # ----------------------------------------------------
        # USUARIOS
        # ----------------------------------------------------

        if path == "/api/users":

            if not self.require_admin():

                return

            self.send_users()

            return

        # ----------------------------------------------------
        # SESIÓN
        # ----------------------------------------------------

        if path.startswith(
            "/api/users/session/"
        ):

            session_id = path[
                len(
                    "/api/users/session/"
                ):
            ]

            self.check_session(
                session_id
            )

            return

        # ----------------------------------------------------
        # ARCHIVOS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # AGREGAR CATÁLOGO
        # ----------------------------------------------------

        if path == "/api/catalog":

            if not self.require_admin():

                return

            self.add_catalog_item()

            return

        # ----------------------------------------------------
        # RESTAURAR PAPELERA
        # ----------------------------------------------------

        if (
            path.startswith(
                "/api/trash/"
            )
            and
            path.endswith(
                "/restore"
            )
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

        # ----------------------------------------------------
        # REGISTRO
        # ----------------------------------------------------

        if path == "/api/users/register":

            self.user_register()

            return

        # ----------------------------------------------------
        # LOGIN
        # ----------------------------------------------------

        if path == "/api/users/login":

            self.user_login()

            return

        # ----------------------------------------------------
        # LOGOUT
        # ----------------------------------------------------

        if path == "/api/users/logout":

            self.user_logout()

            return

        # ----------------------------------------------------
        # DESCONECTAR
        # ----------------------------------------------------

        if (
            path.startswith(
                "/api/users/"
            )
            and
            path.endswith(
                "/disconnect"
            )
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

        # ----------------------------------------------------
        # EDITAR CATÁLOGO
        # ----------------------------------------------------

        if path.startswith(
            "/api/catalog/"
        ):

            if not self.require_admin():

                return

            item_id = path[
                len("/api/catalog/"):
            ]

            self.update_catalog_item(
                item_id
            )

            return

        # ----------------------------------------------------
        # EDITAR USUARIO
        # ----------------------------------------------------

        if path.startswith(
            "/api/users/"
        ):

            if path.endswith(
                "/disconnect"
            ):

                self.send_json(
                    {
                        "success": False,
                        "error": "Ruta no válida."
                    },
                    400
                )

                return

            if not self.require_admin():

                return

            user_id = path[
                len("/api/users/"):
            ]

            self.update_user(
                user_id
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

        # ----------------------------------------------------
        # ELIMINAR CATÁLOGO
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # ELIMINAR PAPELERA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # ELIMINAR USUARIO
        # ----------------------------------------------------

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
    # USUARIOS
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
                isinstance(
                    s,
                    dict
                )
                and
                s.get(
                    "active"
                ) is True
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
                user.get(
                    "id"
                )
            )

            result.append(
                {
                    "id": user_id,
                    "username": user.get(
                        "username",
                        ""
                    ),
                    "email": user.get(
                        "email",
                        ""
                    ),
                    "role": user.get(
                        "role",
                        "user"
                    ),
                    "connected": (
                        user_id in active_ids
                    )
                }
            )

        self.send_json(
            result
        )

    # ========================================================
    # REGISTRO
    # ========================================================

    def user_register(
        self
    ):

        try:

            data = self.read_body()

            username = clean_id(
                data.get(
                    "username"
                )
            )

            email = clean_id(
                data.get(
                    "email"
                )
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
                        "error": (
                            "El nombre de usuario "
                            "debe tener al menos 3 caracteres."
                        )
                    },
                    400
                )

                return

            if len(username) > 20:

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "El nombre de usuario "
                            "no puede superar 20 caracteres."
                        )
                    },
                    400
                )

                return

            if not email:

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "El correo electrónico "
                            "es obligatorio."
                        )
                    },
                    400
                )

                return

            if len(password) < 6:

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "La contraseña "
                            "debe tener al menos 6 caracteres."
                        )
                    },
                    400
                )

                return

            users = self.load_users()

            for user in users:

                if (
                    clean_id(
                        user.get(
                            "email"
                        )
                    ).lower()
                    == email
                ):

                    self.send_json(
                        {
                            "success": False,
                            "error": (
                                "Este correo electrónico "
                                "ya está registrado."
                            )
                        },
                        409
                    )

                    return

                if (
                    clean_id(
                        user.get(
                            "username"
                        )
                    ).lower()
                    == username.lower()
                ):

                    self.send_json(
                        {
                            "success": False,
                            "error": (
                                "Este nombre de usuario "
                                "ya está en uso."
                            )
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
                "password": password,
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
                        "error": (
                            "No se pudo guardar "
                            "el usuario."
                        )
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message": (
                        "Cuenta creada correctamente."
                    ),
                    "user": {
                        "id": new_user[
                            "id"
                        ],
                        "username": new_user[
                            "username"
                        ],
                        "email": new_user[
                            "email"
                        ],
                        "role": new_user[
                            "role"
                        ]
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

        try:

            data = self.read_body()

            email = clean_id(
                data.get(
                    "email"
                )
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
                        "error": (
                            "Correo y contraseña "
                            "son obligatorios."
                        )
                    },
                    400
                )

                return

            users = self.load_users()

            found_user = None

            for user in users:

                if (
                    clean_id(
                        user.get(
                            "email"
                        )
                    ).lower()
                    == email
                    and
                    str(
                        user.get(
                            "password",
                            ""
                        )
                    )
                    == password
                ):

                    found_user = user

                    break

            if found_user is None:

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "Correo electrónico "
                            "o contraseña incorrectos."
                        )
                    },
                    401
                )

                return

            user_id = clean_id(
                found_user.get(
                    "id"
                )
            )

            # ------------------------------------------------
            # UNA SOLA SESIÓN ACTIVA
            # ------------------------------------------------

            with SESSIONS_LOCK:

                sessions = self.load_json_file(
                    SESSIONS_FILE
                )

                sessions = [
                    s
                    for s in sessions
                    if (
                        clean_id(
                            s.get(
                                "user_id"
                            )
                        )
                        != user_id
                    )
                ]

                session_id = str(
                    uuid.uuid4()
                )

                sessions.append(
                    {
                        "id": session_id,
                        "user_id": user_id,
                        "active": True,
                        "last_activity": now_iso()
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
                        "error": (
                            "No se pudo crear "
                            "la sesión."
                        )
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
                "Session:",
                session_id
            )

            print(
                "=========================================="
            )
            print()

            self.send_json(
                {
                    "success": True,
                    "message": (
                        "Inicio de sesión correcto."
                    ),
                    "session_id": session_id,
                    "sessionId": session_id,
                    "token": session_id,
                    "user": {
                        "id": user_id,
                        "username": found_user.get(
                            "username",
                            ""
                        ),
                        "email": found_user.get(
                            "email",
                            ""
                        ),
                        "role": found_user.get(
                            "role",
                            "user"
                        )
                    }
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
                    "error": str(e)
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
                clean_id(
                    session_id
                )
                or
                self.get_session_id_from_request()
            )

            if not session_id:

                self.send_json(
                    {
                        "success": False,
                        "active": False,
                        "error": (
                            "Sesión no especificada."
                        )
                    },
                    400
                )

                return

            session, _ = self.find_session(
                session_id
            )

            if session is None:

                self.send_json(
                    {
                        "success": False,
                        "active": False,
                        "error": "Sesión inválida.",
                        "code": "INVALID_SESSION"
                    },
                    401
                )

                return

            if session.get(
                "active"
            ) is not True:

                self.send_json(
                    {
                        "success": False,
                        "active": False,
                        "error": (
                            "La sesión ha sido cerrada."
                        ),
                        "code": "SESSION_INACTIVE"
                    },
                    401
                )

                return

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
                        "active": False,
                        "error": (
                            "El usuario ya no existe."
                        ),
                        "code": "USER_NOT_FOUND"
                    },
                    401
                )

                return

            self.send_json(
                {
                    "success": True,
                    "active": True,
                    "session_id": session_id,
                    "sessionId": session_id,
                    "token": session_id,
                    "user": {
                        "id": user_id,
                        "username": user.get(
                            "username",
                            ""
                        ),
                        "email": user.get(
                            "email",
                            ""
                        ),
                        "role": user.get(
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
                    "error": str(e)
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
                        "error": (
                            "Sesión no especificada."
                        )
                    },
                    400
                )

                return

            with SESSIONS_LOCK:

                sessions = self.load_json_file(
                    SESSIONS_FILE
                )

                found = False

                current_time = now_iso()

                for session in sessions:

                    if (
                        clean_id(
                            session.get(
                                "id"
                            )
                        )
                        == session_id
                    ):

                        session[
                            "active"
                        ] = False

                        session[
                            "last_activity"
                        ] = current_time

                        session[
                            "logout_at"
                        ] = current_time

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
                    "message": "Sesión cerrada.",
                    "session_id": session_id
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
                    "error": str(e)
                },
                500
            )

    # ========================================================
    # DESCONECTAR USUARIO
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
                        "error": (
                            "Usuario no encontrado."
                        )
                    },
                    404
                )

                return

            with SESSIONS_LOCK:

                sessions = self.load_json_file(
                    SESSIONS_FILE
                )

                found = False

                current_time = now_iso()

                for session in sessions:

                    if (
                        clean_id(
                            session.get(
                                "user_id"
                            )
                        )
                        == user_id
                    ):

                        session[
                            "active"
                        ] = False

                        session[
                            "last_activity"
                        ] = current_time

                        session[
                            "disconnected_at"
                        ] = current_time

                        found = True

                if found:

                    self.save_json_file(
                        SESSIONS_FILE,
                        sessions
                    )

            self.send_json(
                {
                    "success": True,
                    "message": (
                        "Usuario desconectado correctamente."
                    ),
                    "user_id": user_id,
                    "sessions_invalidated": found
                }
            )

        except Exception as e:

            print(
                "ERROR desconectando usuario:",
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
    # ACTUALIZAR USUARIO
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
                        user.get(
                            "id"
                        )
                    )
                    == clean_id(
                        user_id
                    )
                ):

                    found = user
                    index = i

                    break

            if found is None:

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "Usuario no encontrado."
                        )
                    },
                    404
                )

                return

            # ------------------------------------------------
            # USERNAME
            # ------------------------------------------------

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
                            "error": (
                                "El nombre de usuario "
                                "debe tener entre 3 y 20 caracteres."
                            )
                        },
                        400
                    )

                    return

                for user in users:

                    if (
                        clean_id(
                            user.get(
                                "id"
                            )
                        )
                        != clean_id(
                            user_id
                        )
                    ):

                        if (
                            clean_id(
                                user.get(
                                    "username"
                                )
                            ).lower()
                            == username.lower()
                        ):

                            self.send_json(
                                {
                                    "success": False,
                                    "error": (
                                        "Este nombre de usuario "
                                        "ya está en uso."
                                    )
                                },
                                409
                            )

                            return

                found[
                    "username"
                ] = username

            # ------------------------------------------------
            # EMAIL
            # ------------------------------------------------

            if "email" in data:

                email = clean_id(
                    data["email"]
                ).lower()

                if not email:

                    self.send_json(
                        {
                            "success": False,
                            "error": (
                                "El correo electrónico "
                                "es obligatorio."
                            )
                        },
                        400
                    )

                    return

                for user in users:

                    if (
                        clean_id(
                            user.get(
                                "id"
                            )
                        )
                        != clean_id(
                            user_id
                        )
                    ):

                        if (
                            clean_id(
                                user.get(
                                    "email"
                                )
                            ).lower()
                            == email
                        ):

                            self.send_json(
                                {
                                    "success": False,
                                    "error": (
                                        "Este correo electrónico "
                                        "ya está registrado."
                                    )
                                },
                                409
                            )

                            return

                found[
                    "email"
                ] = email

            # ------------------------------------------------
            # PASSWORD
            # ------------------------------------------------

            if "password" in data:

                password = str(
                    data["password"]
                )

                if len(password) < 6:

                    self.send_json(
                        {
                            "success": False,
                            "error": (
                                "La contraseña "
                                "debe tener al menos 6 caracteres."
                            )
                        },
                        400
                    )

                    return

                found[
                    "password"
                ] = password

            # ------------------------------------------------
            # ROLE
            # ------------------------------------------------

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

            users[
                index
            ] = found

            if not self.save_users(
                users
            ):

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "No se pudo guardar "
                            "el usuario."
                        )
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message": (
                        "Usuario actualizado correctamente."
                    ),
                    "user": {
                        "id": found.get(
                            "id",
                            ""
                        ),
                        "username": found.get(
                            "username",
                            ""
                        ),
                        "email": found.get(
                            "email",
                            ""
                        ),
                        "role": found.get(
                            "role",
                            "user"
                        )
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
                    "error": str(e)
                },
                500
            )

    # ========================================================
    # ELIMINAR USUARIO
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
                            u.get(
                                "id"
                            )
                        )
                        == user_id
                    )
                ),
                None
            )

            if found is None:

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "Usuario no encontrado."
                        )
                    },
                    404
                )

                return

            new_users = [
                u
                for u in users
                if (
                    clean_id(
                        u.get(
                            "id"
                        )
                    )
                    != user_id
                )
            ]

            if not self.save_users(
                new_users
            ):

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "No se pudo eliminar "
                            "el usuario."
                        )
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
                    "message": (
                        "Usuario eliminado correctamente."
                    ),
                    "user_id": user_id
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
                    "error": str(e)
                },
                500
            )

    # ========================================================
    # CATÁLOGO - AGREGAR
    # ========================================================

    def add_catalog_item(
        self
    ):

        try:

            item = self.read_body()

            catalog = self.load_catalog()

            if (
                not item.get(
                    "title"
                )
                and
                item.get(
                    "name"
                )
            ):

                item[
                    "title"
                ] = item[
                    "name"
                ]

            # ------------------------------------------------
            # ID AUTOMÁTICO
            # ------------------------------------------------

            if not item.get(
                "id"
            ):

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
                        x.get(
                            "id"
                        )
                    )
                    for x in catalog
                    if x.get(
                        "id"
                    )
                }

                while new_id in ids:

                    new_id = (
                        f"{base}-{counter}"
                    )

                    counter += 1

                item[
                    "id"
                ] = new_id

            item_id = clean_id(
                item.get(
                    "id"
                )
            )

            if any(
                clean_id(
                    x.get(
                        "id"
                    )
                )
                == item_id
                for x in catalog
            ):

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "Ya existe un contenido "
                            "con ese ID."
                        )
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
                        "error": (
                            "No se pudo guardar "
                            "el catálogo. "
                            "Comprueba la conexión "
                            "con GitHub."
                        )
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message": (
                        "Contenido agregado"
                    ),
                    "item": item
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
                    "error": str(e)
                },
                500
            )

    # ========================================================
    # CATÁLOGO - EDITAR
    # ========================================================

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
                        item.get(
                            "id"
                        )
                    )
                    == item_id
                ):

                    if (
                        not data.get(
                            "title"
                        )
                        and
                        data.get(
                            "name"
                        )
                    ):

                        data[
                            "title"
                        ] = data[
                            "name"
                        ]

                    merged = {
                        **item,
                        **data
                    }

                    merged[
                        "id"
                    ] = item.get(
                        "id"
                    )

                    catalog[
                        i
                    ] = merged

                    if not self.save_catalog(
                        catalog
                    ):

                        self.send_json(
                            {
                                "success": False,
                                "error": (
                                    "No se pudo guardar "
                                    "el catálogo. "
                                    "Comprueba GitHub."
                                )
                            },
                            500
                        )

                        return

                    self.send_json(
                        {
                            "success": True,
                            "message": (
                                "Contenido actualizado"
                            ),
                            "item": merged
                        }
                    )

                    return

            self.send_json(
                {
                    "success": False,
                    "error": (
                        "Contenido no encontrado"
                    )
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
                    "error": str(e)
                },
                500
            )

    # ========================================================
    # CATÁLOGO - ELIMINAR
    # ========================================================

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
                        item.get(
                            "id"
                        )
                    )
                    == item_id
                ):

                    found = dict(
                        item
                    )

                else:

                    new_catalog.append(
                        item
                    )

            if found is None:

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "Contenido no encontrado"
                        )
                    },
                    404
                )

                return

            trash = [
                x
                for x in trash
                if (
                    clean_id(
                        x.get(
                            "id"
                        )
                    )
                    != item_id
                )
            ]

            found[
                "deletedAt"
            ] = now_iso()

            trash.append(
                found
            )

            # ------------------------------------------------
            # Guardar catálogo
            # ------------------------------------------------

            if not self.save_catalog(
                new_catalog
            ):

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "No se pudo actualizar "
                            "el catálogo."
                        )
                    },
                    500
                )

                return

            # ------------------------------------------------
            # Guardar papelera
            # ------------------------------------------------

            if not self.save_trash(
                trash
            ):

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "El contenido salió del catálogo "
                            "pero no se pudo guardar "
                            "la papelera."
                        )
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message": (
                        "Contenido movido a la papelera"
                    ),
                    "item": found
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
                    "error": str(e)
                },
                500
            )

    # ========================================================
    # RESTAURAR
    # ========================================================

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
                        item.get(
                            "id"
                        )
                    )
                    == item_id
                ):

                    found = dict(
                        item
                    )

                else:

                    new_trash.append(
                        item
                    )

            if found is None:

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "Contenido no encontrado "
                            "en la papelera."
                        )
                    },
                    404
                )

                return

            if any(
                clean_id(
                    x.get(
                        "id"
                    )
                )
                == item_id
                for x in catalog
            ):

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "Ya existe un contenido "
                            "con ese ID en el catálogo."
                        )
                    },
                    409
                )

                return

            if "deletedAt" in found:

                del found[
                    "deletedAt"
                ]

            catalog.append(
                found
            )

            if not self.save_catalog(
                catalog
            ):

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "No se pudo restaurar "
                            "el contenido."
                        )
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
                        "error": (
                            "El contenido fue restaurado "
                            "pero no se pudo actualizar "
                            "la papelera."
                        )
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message": (
                        "Contenido recuperado correctamente"
                    ),
                    "item": found
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
                    "error": str(e)
                },
                500
            )

    # ========================================================
    # ELIMINAR DEFINITIVAMENTE
    # ========================================================

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
                        x.get(
                            "id"
                        )
                    )
                    != item_id
                )
            ]

            if (
                len(
                    new_trash
                )
                ==
                len(
                    trash
                )
            ):

                self.send_json(
                    {
                        "success": False,
                        "error": (
                            "Contenido no encontrado "
                            "en la papelera."
                        )
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
                        "error": (
                            "No se pudo eliminar "
                            "definitivamente."
                        )
                    },
                    500
                )

                return

            self.send_json(
                {
                    "success": True,
                    "message": (
                        "Contenido eliminado definitivamente"
                    ),
                    "id": item_id
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
                    "error": str(e)
                },
                500
            )


# ============================================================
# SERVIDOR
# ============================================================

class CinemaXServer(
    ThreadingHTTPServer
):

    allow_reuse_address = True


# ============================================================
# INICIO
# ============================================================

if __name__ == "__main__":

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

    # --------------------------------------------------------
    # GITHUB
    # --------------------------------------------------------

    if github_enabled():

        print(
            "☁️ GITHUB: ACTIVADO"
        )

        print(
            f"   Repo: "
            f"{GITHUB_OWNER}/{GITHUB_REPO}"
        )

        print(
            f"   Branch: "
            f"{GITHUB_BRANCH}"
        )

        print(
            f"   Path: "
            f"{GITHUB_PATH_PREFIX or '(raíz)'}"
        )

    else:

        print(
            "☁️ GITHUB: DESACTIVADO"
        )

        print(
            "   Variables GitHub no configuradas."
        )

    print()

    # --------------------------------------------------------
    # SINCRONIZAR GITHUB ANTES DE ARRANCAR
    # --------------------------------------------------------

    github_initial_sync()

    # --------------------------------------------------------
    # ESTADO
    # --------------------------------------------------------

    print(
        "🔐 ADMIN: ACTIVADO"
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
        "🔌 DESCONEXIÓN DE SESIONES: ACTIVADA"
    )

    print(
        "💾 PERSISTENCIA GITHUB: "
        + (
            "ACTIVADA"
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