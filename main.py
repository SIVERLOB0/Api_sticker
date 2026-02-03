import os
import uuid
import time
import threading
import glob
import io
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
from PIL import Image
from rembg import remove # La magia para quitar fondos

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🐺 WOLF API (FULL SUITE): ONLINE...")

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
    return "🐺 WOLF API: MEDIA & STICKERS READY."

# --- ENDPOINT DE YOUTUBE/TIKTOK (YA LO TIENES) ---
@app.route('/process', methods=['GET'])
def process_media():
    # ... (MANTÉN TU CÓDIGO DE YT-DLP AQUÍ IGUAL QUE ANTES) ...
    # Para no hacer este mensaje eterno, asumo que usas el código "TikTok Fix" que te di antes.
    return jsonify({"status": False, "error": "Usa el código anterior para esta parte"}), 501


# --- NUEVO: ENDPOINT DE STICKERS ---
@app.route('/sticker', methods=['GET'])
def make_sticker():
    url = request.args.get('url')
    
    if not url: return jsonify({"status": False, "error": "Falta URL"}), 400

    print(f"🎨 Creando Sticker de: {url}")
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.webp"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        # 1. Descargar la imagen
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 2. Abrir imagen con Pillow
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")

        # 3. Quitar fondo (Magia AI)
        # alpha_matting mejora los bordes (pelo, pelaje de lobo, etc)
        img_sin_fondo = remove(img, alpha_matting=True)

        # 4. Redimensionar a 512x512 (Formato Sticker)
        # No estiramos, hacemos que "quepa" manteniendo proporción
        img_sin_fondo.thumbnail((512, 512))
        
        # Crear un lienzo vacío transparente de 512x512
        final_img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        
        # Centrar la imagen en el lienzo
        offset = ((512 - img_sin_fondo.width) // 2, (512 - img_sin_fondo.height) // 2)
        final_img.paste(img_sin_fondo, offset)

        # 5. Guardar como WebP
        final_img.save(filepath, format="WEBP", quality=95)

        mi_link = f"{request.host_url}file/{filename}"

        return jsonify({
            "status": True,
            "resultado": {
                "descarga": mi_link,
                "nota": "Sticker sin fondo creado"
            }
        })

    except Exception as e:
        print(f"❌ Error Sticker: {str(e)}")
        return jsonify({"status": False, "error": str(e)}), 500

@app.route('/file/<filename>')
def get_file(filename):
    try:
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(path):
            return send_file(path) # WebP se envía directo
        else:
            return "Archivo expirado", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
