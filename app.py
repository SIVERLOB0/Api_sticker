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
from rembg import remove

app = Flask(__name__)
CORS(app)

# Carpeta temporal para guardar los stickers
DOWNLOAD_FOLDER = 'stickers'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

print("🐺 WOLF STICKER FACTORY: ONLINE...")

# --- SISTEMA DE LIMPIEZA (Para no llenar el disco) ---
def limpiar_basura():
    while True:
        try:
            now = time.time()
            files = glob.glob(os.path.join(DOWNLOAD_FOLDER, '*'))
            for f in files:
                # Borra archivos creados hace más de 10 minutos
                if os.stat(f).st_mtime < now - 600: 
                    os.remove(f)
                    print(f"🧹 Limpieza: {f}")
        except Exception:
            pass
        time.sleep(600) # Revisa cada 10 minutos

threading.Thread(target=limpiar_basura, daemon=True).start()

@app.route('/')
def home():
    return "🐺 WOLF STICKER API: ACTIVA"

@app.route('/create', methods=['GET'])
def create_sticker():
    url = request.args.get('url')
    
    if not url: return jsonify({"status": False, "error": "Falta parametro URL"}), 400

    print(f"🎨 Procesando imagen: {url}")
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.webp"
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

    try:
        # 1. Descargar la imagen original
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # 2. Abrir imagen en memoria
        input_image = Image.open(io.BytesIO(response.content)).convert("RGBA")

        # 3. QUITAR FONDO (La magia)
        # La primera vez que corras esto, tardará un poco descargando el modelo U2NET
        output_image = remove(input_image)

        # 4. Ajustar al estándar de WhatsApp (512x512)
        # Creamos un lienzo transparente vacío
        final_canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        
        # Redimensionamos la imagen para que quepa en 512x512 sin estirarse (contain)
        output_image.thumbnail((512, 512), Image.Resampling.LANCZOS)
        
        # Calculamos la posición para centrarla
        x_offset = (512 - output_image.width) // 2
        y_offset = (512 - output_image.height) // 2
        
        # Pegamos la imagen sin fondo en el centro del lienzo
        final_canvas.paste(output_image, (x_offset, y_offset), output_image)

        # 5. Guardar como WebP
        final_canvas.save(filepath, format="WEBP", quality=90)

        # Generar link de descarga
        download_link = f"{request.host_url}file/{filename}"

        return jsonify({
            "status": True,
            "resultado": {
                "descarga": download_link,
                "autor": "Wolf API"
            }
        })

    except Exception as e:
        print(f"❌ Error Sticker: {str(e)}")
        return jsonify({"status": False, "error": "Error al procesar imagen"}), 500

@app.route('/file/<filename>')
def get_file(filename):
    try:
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        if os.path.exists(path):
            return send_file(path, mimetype='image/webp')
        else:
            return "Archivo expirado o no existe", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
