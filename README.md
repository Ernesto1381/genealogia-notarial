# Registro Genealógico Notarial

App para búsqueda de personas, gestión de certificados y árbol genealógico.

## Estructura
- `index.html` — Frontend (GitHub Pages)
- `servidor.py` — Backend API (Render.com)
- `requirements.txt` — Dependencias Python
- `render.yaml` — Configuración Render

## Deploy

### 1. Backend en Render
1. Crear cuenta en [render.com](https://render.com)
2. New → Web Service → conectar este repositorio
3. Render detecta `render.yaml` automáticamente
4. Copiar la URL del servicio (ej: `https://genealogia-api.onrender.com`)

### 2. Frontend en GitHub Pages
1. Settings → Pages → Branch: main → /root
2. Editar `index.html`: reemplazar `%%RENDER_URL%%` por la URL de Render

## Uso local
```
pip install playwright
python -m playwright install chromium
python servidor.py
```
