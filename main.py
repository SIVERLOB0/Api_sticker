import os
import uuid
import time
import threading
import glob
import io
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'stickers'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🐺 WOLF STICKER SYSTEM (IMAGE + TEXT): ONLINE...")

def limpiar_basura():
    while True:
        try:
            now = time.time()
            files = glob.glob(os.path.join(DOWNLOAD_FOLDER, '*'))
            for f in files:
                if os.stat(f).st_mtime < now - 600: 
                    os.remove(f)
        except Exception: pass
        time.sleep(600)

threading.Thread(target=limpiar_basura, daemon=True).start()

# --- ENDPOINT PARA IMAGEN (EL QUE YA TENÍAS) ---
@app.route('/create', methods=['GET'])
def create_sticker():
    url = request.args.get('url')
    if not url: return jsonify({"status": False, "error": "Falta URL"}), 400
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.webp"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    try:
        response = requests.get(url, stream=True, timeout=10)
        img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        img.thumbnail((512, 512))
        final_canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        final_canvas.paste(img, ((512 - img.width) // 2, (512 - img.height) // 2), img)
        final_canvas.save(filepath, format="WEBP", quality=90)
        return jsonify({"status": True, "resultado": {"descarga": f"{request.host_url}file/{filename}"}})
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

# --- NUEVO: ENDPOINT PARA TEXTO ---
@app.route('/text', methods=['GET'])
def text_sticker():
    text = request.args.get('text', 'Wolf Bot')
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.webp"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    
    try:
        # Crear lienzo cuadrado transparente
        img = Image.new('RGBA', (512, 512), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Intentar cargar una fuente, si no, usar la básica
        try:
            font = ImageFont.load_default(size=50) # Pillow moderno permite size
        except:
            font = ImageFont.load_default()

        # Centrar texto
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        position = ((512-w)//2, (512-h)//2)

        # Dibujar borde negro para que se vea en cualquier fondo
        for adj in range(-3, 4):
            draw.text((position[0]+adj, position[1]), text, font=font, fill="black")
            draw.text((position[0], position[1]+adj), text, font=font, fill="black")

        # Dibujar texto blanco encima
        draw.text(position, text, font=font, fill="white")
        
        img.save(filepath, format="WEBP", quality=90)
        return jsonify({"status": True, "resultado": {"descarga": f"{request.host_url}file/{filename}"}})
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

@app.route('/file/<filename>')
def get_file(filename):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    return send_file(path, mimetype='image/webp') if os.path.exists(path) else ("404", 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
