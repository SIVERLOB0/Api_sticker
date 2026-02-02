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

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'stickers'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🐺 WOLF STICKER (SUPER LITE): ONLINE...")

# --- LIMPIEZA AUTOMÁTICA ---
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
    return "🐺 WOLF STICKER: MODO SUPER LITE (SIN IA)"

@app.route('/create', methods=['GET'])
def create_sticker():
    url = request.args.get('url')
    
    if not url: return jsonify({"status": False, "error": "Falta URL"}), 400

    print(f"🖼️ Convirtiendo: {url}")
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.webp"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        # 1. Descargar imagen
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # 2. Abrir con Pillow
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")

        # 3. TRANSFORMACIÓN INTELIGENTE (Sin IA)
        # Redimensionamos para que quepa en 512x512 sin deformarse
        img.thumbnail((512, 512))
        
        # Crear lienzo transparente 512x512
        final_canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        
        # Centrar la imagen en el lienzo
        x_offset = (512 - img.width) // 2
        y_offset = (512 - img.height) // 2
        final_canvas.paste(img, (x_offset, y_offset), img) # Usamos la misma img como máscara por si tiene transparencia

        # 4. Guardar como WebP (Formato Sticker)
        final_canvas.save(filepath, format="WEBP", quality=95)

        return jsonify({
            "status": True,
            "resultado": {
                "descarga": f"{request.host_url}file/{filename}",
                "nota": "Sticker creado (Sin recorte)"
            }
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"status": False, "error": str(e)}), 500

@app.route('/file/<filename>')
def get_file(filename):
    try:
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(path):
            return send_file(path, mimetype='image/webp')
        else:
            return "Expirado", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
