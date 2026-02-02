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
from rembg import remove, new_session 

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'stickers'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# --- OPTIMIZACIÓN DE MEMORIA ---
# Usamos 'u2netp' (versión ligera) para que no crashee en Railway
print("🐺 CARGANDO CEREBRO IA (MODO LITE)...")
model_session = new_session("u2netp") 

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
    return "🐺 WOLF STICKER API (LITE): ACTIVA"

@app.route('/create', methods=['GET'])
def create_sticker():
    url = request.args.get('url')
    
    if not url: return jsonify({"status": False, "error": "Falta URL"}), 400

    file_id = str(uuid.uuid4())
    filename = f"{file_id}.webp"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        input_image = Image.open(io.BytesIO(response.content)).convert("RGBA")

        # AQUÍ ESTÁ LA MAGIA: Usamos la session pre-cargada ligera
        output_image = remove(input_image, session=model_session)

        # Redimensionar y centrar
        final_canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        output_image.thumbnail((512, 512), Image.Resampling.LANCZOS)
        x_offset = (512 - output_image.width) // 2
        y_offset = (512 - output_image.height) // 2
        final_canvas.paste(output_image, (x_offset, y_offset), output_image)

        final_canvas.save(filepath, format="WEBP", quality=85) # Calidad 85 para ahorrar más RAM

        download_link = f"{request.host_url}file/{filename}"

        return jsonify({
            "status": True,
            "resultado": {
                "descarga": download_link,
                "info": "Modelo u2netp (Lite)"
            }
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        # Importante: Devolver error 500 para saber si fue crash o lógica
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
