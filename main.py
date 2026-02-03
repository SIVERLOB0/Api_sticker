import os
import uuid
import time
import threading
import glob
import io
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image

# Importante: Si tu archivo se llama main.py en Railway, Flask debe llamarse 'app'
app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'stickers'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🐺 WOLF STICKER (SUPER LITE - SIN IA): ONLINE...")

def limpiar_basura():
    while True:
        try:
            now = time.time()
            files = glob.glob(os.path.join(DOWNLOAD_FOLDER, '*'))
            for f in files:
                if os.stat(f).st_mtime < now - 600: 
                    os.remove(f)
        except Exception:
            pass
        time.sleep(600)

threading.Thread(target=limpiar_basura, daemon=True).start()

@app.route('/')
def home():
    return "🐺 WOLF STICKER: MODO SUPER LITE (SIN CRASHEOS)"

@app.route('/create', methods=['GET'])
def create_sticker():
    url = request.args.get('url')
    if not url: return jsonify({"status": False, "error": "Falta URL"}), 400

    file_id = str(uuid.uuid4())
    filename = f"{file_id}.webp"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        # 1. Descargar imagen
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # 2. Abrir imagen
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")

        # 3. Redimensionar a 512x512 (Estándar Sticker)
        img.thumbnail((512, 512))
        
        # Centrar en lienzo transparente
        final_canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        x_offset = (512 - img.width) // 2
        y_offset = (512 - img.height) // 2
        final_canvas.paste(img, (x_offset, y_offset), img)

        # 4. Guardar
        final_canvas.save(filepath, format="WEBP", quality=90)

        return jsonify({
            "status": True,
            "resultado": {
                "descarga": f"{request.host_url}file/{filename}",
                "nota": "Sticker Lite"
            }
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": False, "error": str(e)}), 500

@app.route('/file/<filename>')
def get_file(filename):
    try:
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(path):
            return send_file(path, mimetype='image/webp')
        return "Expirado", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
