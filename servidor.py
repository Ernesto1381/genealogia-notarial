#!/usr/bin/env python3
"""
Backend para Genealogia Notarial
- Deploy en Render.com
- Busqueda por nombre: Playwright -> nombrerutyfirma.com
- Busqueda por RUT:    api.rutificador.live
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json
import os
import re
import threading

RUTIFY_BASE = "https://api.rutificador.live"
RUTIFY_KEY  = "rutify_sk_test-fsanu9dasniuyfdsanuyfnudyas"
PORT        = int(os.environ.get("PORT", 8080))
_pw_lock    = threading.Lock()


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"  {args[0]}")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if self.path.startswith("/api/buscar-nombre"):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name   = params.get("name", [""])[0].strip()
            print(f"Buscando nombre: {name}")
            try:
                data = self._playwright_nombre(name)
                self._json(200, data)
            except Exception as e:
                print(f"Error: {e}")
                self._json(500, {"error": str(e)})

        elif self.path.startswith("/api/buscar-rut"):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            rut    = params.get("rut", [""])[0]
            print(f"Buscando RUT: {rut}")
            try:
                url = RUTIFY_BASE + "/search/rut?rut=" + urllib.parse.quote(rut)
                req = urllib.request.Request(url, headers={
                    "x-api-key": RUTIFY_KEY,
                    "Accept":    "application/json",
                    "User-Agent":"Mozilla/5.0"
                })
                with urllib.request.urlopen(req, timeout=10) as r:
                    d = json.loads(r.read())
                if isinstance(d, dict) and not d.get("title"):
                    d = [self._norm(d)]
                elif isinstance(d, list):
                    d = [self._norm(x) for x in d]
                else:
                    d = []
                self._json(200, d)
            except urllib.error.HTTPError as e:
                self._json(e.code, {"error": e.read().decode()})
            except Exception as e:
                self._json(500, {"error": str(e)})

        elif path == "/health":
            self._json(200, {"status": "ok"})

        else:
            self.send_response(404)
            self.end_headers()

    def _playwright_nombre(self, nombre):
        with _pw_lock:
            from playwright.sync_api import sync_playwright
            url = "https://www.nombrerutyfirma.com/nombre/" + urllib.parse.quote(nombre)
            print(f"Chrome -> {url}")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox","--disable-dev-shm-usage"])
                page    = browser.new_page()
                page.set_extra_http_headers({"Accept-Language":"es-CL,es;q=0.9"})
                page.goto(url, wait_until="networkidle", timeout=25000)
                html = page.content()
                browser.close()

            resultados = []
            for fila in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL|re.IGNORECASE):
                celdas = re.findall(r'<td[^>]*>(.*?)</td>', fila, re.DOTALL|re.IGNORECASE)
                celdas = [re.sub(r'\s+',' ',re.sub(r'<[^>]+>','',c)).strip() for c in celdas]
                celdas = [c for c in celdas if c]
                if len(celdas) < 2: continue
                n,r = celdas[0], celdas[1]
                d   = celdas[2] if len(celdas)>2 else ""
                if any(k in n.lower() for k in ["nombre","rut","direcci","apellido"]): continue
                if len(n)<3 or not re.search(r'\d',r): continue
                resultados.append({"name":n,"rut":r,"address":d,"city":""})
            print(f"Resultados: {len(resultados)}")
            return resultados[:8]

    def _norm(self, p):
        nombre = p.get("name") or " ".join(filter(None,[p.get("firstName",""),p.get("lastName","")])).strip()
        return {"name":nombre,"rut":p.get("rut",""),"address":p.get("address",""),"city":p.get("city","")}

    def _json(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(raw)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")


if __name__ == "__main__":
    print(f"Servidor iniciando en puerto {PORT}...")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
