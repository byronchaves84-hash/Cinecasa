import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CINEMA_DIR = os.path.join(BASE_DIR, "Cinema-main")
DATA_FILE = os.path.join(CINEMA_DIR, "data.json")

HOST = "0.0.0.0"
PORT = 8000


# ============================================================
# SERVIDOR
# ============================================================

class CinemaXHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CINEMA_DIR, **kwargs)

    # ========================================================
    # GET
    # ========================================================

    def do_GET(self):

        parsed = urlparse(self.path)

        # API DEL CATÁLOGO
        if parsed.path == "/api/catalog":
            self.send_catalog()
            return

        # Página normal de CINEMAX
        super().do_GET()

    # ========================================================
    # POST
    # ========================================================

    def do_POST(self):

        parsed = urlparse(self.path)

        if parsed.path == "/api/catalog":
            self.add_catalog_item()
            return

        self.send_error(404, "Ruta no encontrada")

    # ========================================================
    # PUT
    # ========================================================

    def do_PUT(self):

        parsed = urlparse(self.path)

        if parsed.path.startswith("/api/catalog/"):

            item_id = parsed.path.split("/")[-1]

            self.update_catalog_item(item_id)

            return

        self.send_error(404, "Ruta no encontrada")

    # ========================================================
    # DELETE
    # ========================================================

    def do_DELETE(self):

        parsed = urlparse(self.path)

        if parsed.path.startswith("/api/catalog/"):

            item_id = parsed.path.split("/")[-1]

            self.delete_catalog_item(item_id)

            return

        self.send_error(404, "Ruta no encontrada")

    # ========================================================
    # LEER CATÁLOGO
    # ========================================================

    def load_catalog(self):

        if not os.path.exists(DATA_FILE):
            return []

        try:

            with open(DATA_FILE, "r", encoding="utf-8") as file:

                return json.load(file)

        except Exception as e:

            print("Error leyendo data.json:", e)

            return []

    # ========================================================
    # GUARDAR CATÁLOGO
    # ========================================================

    def save_catalog(self, catalog):

        with open(DATA_FILE, "w", encoding="utf-8") as file:

            json.dump(
                catalog,
                file,
                ensure_ascii=False,
                indent=4
            )

    # ========================================================
    # RESPUESTA JSON
    # ========================================================

    def send_json(self, data, status=200):

        response = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.end_headers()

        self.wfile.write(response)

    # ========================================================
    # GET /api/catalog
    # ========================================================

    def send_catalog(self):

        catalog = self.load_catalog()

        self.send_json(catalog)

    # ========================================================
    # LEER BODY
    # ========================================================

    def read_body(self):

        content_length = int(
            self.headers.get("Content-Length", 0)
        )

        body = self.rfile.read(content_length)

        return json.loads(
            body.decode("utf-8")
        )

    # ========================================================
    # POST /api/catalog
    # ========================================================

    def add_catalog_item(self):

        try:

            new_item = self.read_body()

            catalog = self.load_catalog()

            catalog.append(new_item)

            self.save_catalog(catalog)

            self.send_json({
                "success": True,
                "message": "Contenido agregado",
                "item": new_item
            })

        except Exception as e:

            self.send_json({
                "success": False,
                "error": str(e)
            }, 500)

    # ========================================================
    # PUT /api/catalog/<id>
    # ========================================================

    def update_catalog_item(self, item_id):

        try:

            updated_item = self.read_body()

            catalog = self.load_catalog()

            found = False

            for index, item in enumerate(catalog):

                if item.get("id") == item_id:

                    catalog[index] = updated_item

                    found = True

                    break

            if not found:

                self.send_json({
                    "success": False,
                    "error": "Contenido no encontrado"
                }, 404)

                return

            self.save_catalog(catalog)

            self.send_json({
                "success": True,
                "message": "Contenido actualizado",
                "item": updated_item
            })

        except Exception as e:

            self.send_json({
                "success": False,
                "error": str(e)
            }, 500)

    # ========================================================
    # DELETE /api/catalog/<id>
    # ========================================================

    def delete_catalog_item(self, item_id):

        try:

            catalog = self.load_catalog()

            new_catalog = [
                item
                for item in catalog
                if item.get("id") != item_id
            ]

            if len(new_catalog) == len(catalog):

                self.send_json({
                    "success": False,
                    "error": "Contenido no encontrado"
                }, 404)

                return

            self.save_catalog(new_catalog)

            self.send_json({
                "success": True,
                "message": "Contenido eliminado",
                "id": item_id
            })

        except Exception as e:

            self.send_json({
                "success": False,
                "error": str(e)
            }, 500)


# ============================================================
# INICIAR SERVIDOR
# ============================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print("        CINEMAX PYTHON SERVER")
    print("==========================================")
    print()
    print("Servidor:")
    print("http://localhost:8000")
    print()
    print("Carpeta web:")
    print(CINEMA_DIR)
    print()
    print("Catálogo:")
    print(DATA_FILE)
    print()
    print("API:")
    print("GET    /api/catalog")
    print("POST   /api/catalog")
    print("PUT    /api/catalog/<id>")
    print("DELETE /api/catalog/<id>")
    print()
    print("Servidor iniciado...")
    print("==========================================")
    print()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        CinemaXHandler
    )

    server.serve_forever()