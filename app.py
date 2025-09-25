# app.py - Servicio QR Scanner minimalista

from flask import Flask, request, jsonify
from PIL import Image, ImageEnhance, ImageFilter
from pyzbar.pyzbar import decode
import base64
import io
import numpy as np
import cv2
import logging
import sys
import time
import requests
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('qr_scanner.log')
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)


def preprocess_image(image):
    """Aplica múltiples técnicas para mejorar detección de QR"""
    processed_images = [image]  # Original

    if image.mode != 'L':
        gray_image = image.convert('L')
        processed_images.append(gray_image)

        # Aumentar contraste
        enhancer = ImageEnhance.Contrast(gray_image)
        processed_images.append(enhancer.enhance(2.0))
        processed_images.append(enhancer.enhance(3.0))

        # Aumentar brillo
        enhancer = ImageEnhance.Brightness(gray_image)
        processed_images.append(enhancer.enhance(1.5))
        processed_images.append(enhancer.enhance(2.0))

        # Aplicar nitidez
        processed_images.append(gray_image.filter(ImageFilter.SHARPEN))

    return processed_images


def decode_qr(image):
    """Intenta decodificar QR con múltiples técnicas, incluyendo casos ultra-difíciles"""
    logger.info("🔍 Iniciando decodificación con técnicas básicas...")

    # Primero intentar técnicas básicas
    basic_techniques = preprocess_image(image)
    logger.info(f"🔧 Aplicando {len(basic_techniques)} técnicas básicas...")

    for i, processed_img in enumerate(basic_techniques):
        decoded_objects = decode(processed_img)
        if decoded_objects:
            result = decoded_objects[0].data.decode('utf-8')
            logger.info(f"✅ QR detectado con técnica básica #{i}: '{result}'")
            return result

    logger.info(
        "⚡ Técnicas básicas fallaron, aplicando técnicas ultra-avanzadas...")
    # Si falla, usar técnicas ultra-avanzadas
    result = decode_qr_ultra_advanced(image)
    if result:
        logger.info(f"🚀 QR detectado con técnicas ultra-avanzadas: '{result}'")
    else:
        logger.warning("😔 Todas las técnicas fallaron - QR no detectado")
    return result


def decode_qr_ultra_advanced(image):
    """Técnicas ultra-avanzadas para QR muy desenfocados - versión completa"""
    try:
        # Convertir a numpy array
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            img_gray = img_array

        # Múltiples escalas y rotaciones (versión exhaustiva)
        for scale in [0.5, 1.0, 1.5, 2.0]:
            if scale != 1.0:
                h, w = img_gray.shape
                new_h, new_w = int(h * scale), int(w * scale)
                scaled = cv2.resize(img_gray, (new_w, new_h),
                                    interpolation=cv2.INTER_CUBIC)
            else:
                scaled = img_gray.copy()

            # Múltiples rotaciones
            for angle in [0, 1, -1, 2, -2, 5, -5]:
                if angle != 0:
                    center = (scaled.shape[1]//2, scaled.shape[0]//2)
                    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                    rotated = cv2.warpAffine(
                        scaled, matrix, (scaled.shape[1], scaled.shape[0]))
                else:
                    rotated = scaled.copy()

                # Lista exhaustiva de técnicas de mejora
                techniques = []

                # Original
                techniques.append(rotated)

                # Gaussian blur + unsharp mask
                blurred = cv2.GaussianBlur(rotated, (5, 5), 0)
                unsharp = cv2.addWeighted(rotated, 2.0, blurred, -1.0, 0)
                techniques.append(np.clip(unsharp, 0, 255).astype(np.uint8))

                # Bilateral filter (preserva bordes)
                techniques.append(cv2.bilateralFilter(rotated, 9, 75, 75))

                # Sharpening extremo
                kernel = np.array([[-1, -1, -1, -1, -1],
                                  [-1, 2, 2, 2, -1],
                                  [-1, 2, 8, 2, -1],
                                  [-1, 2, 2, 2, -1],
                                  [-1, -1, -1, -1, -1]]) / 8.0
                sharp = cv2.filter2D(rotated, -1, kernel)
                techniques.append(np.clip(sharp, 0, 255).astype(np.uint8))

                # Threshold con múltiples valores
                for thresh_val in [127, 100, 150, 80, 180]:
                    _, thresh = cv2.threshold(
                        rotated, thresh_val, 255, cv2.THRESH_BINARY)
                    techniques.append(thresh)

                # CLAHE extremo
                clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(4, 4))
                clahe_img = clahe.apply(rotated)
                techniques.append(clahe_img)

                # Morphological operations
                for kernel_size in [(2, 2), (3, 3)]:
                    kernel = np.ones(kernel_size, np.uint8)

                    # Opening
                    opening = cv2.morphologyEx(rotated, cv2.MORPH_OPEN, kernel)
                    techniques.append(opening)

                    # Closing
                    closing = cv2.morphologyEx(
                        rotated, cv2.MORPH_CLOSE, kernel)
                    techniques.append(closing)

                # Probar cada técnica
                for processed in techniques:
                    try:
                        pil_img = Image.fromarray(processed)
                        decoded_objects = decode(pil_img)
                        if decoded_objects:
                            return decoded_objects[0].data.decode('utf-8')
                    except:
                        continue

        return None
    except Exception:
        return None


@app.route('/scan', methods=['POST'])
def scan_qr():
    """Endpoint principal para escanear QR"""
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    logger.info(f"📥 [/scan] Nueva petición desde {client_ip}")

    if 'file' not in request.files:
        logger.warning(
            f"❌ [/scan] {client_ip} - No se encontró archivo en la petición")
        return jsonify({"error": "No se encontró archivo"}), 400

    file = request.files['file']
    filename = file.filename or 'sin_nombre'

    if file.filename == '':
        logger.warning(f"❌ [/scan] {client_ip} - Archivo vacío")
        return jsonify({"error": "Archivo vacío"}), 400

    logger.info(f"📸 [/scan] {client_ip} - Procesando archivo: {filename}")

    try:
        img = Image.open(file.stream)
        logger.info(
            f"🖼️  [/scan] {client_ip} - Imagen cargada: {img.size} píxeles, modo: {img.mode}")

        start_time = datetime.now()
        qr_text = decode_qr(img)
        processing_time = (datetime.now() - start_time).total_seconds()

        if qr_text:
            logger.info(
                f"✅ [/scan] {client_ip} - QR detectado en {processing_time:.2f}s: '{qr_text}'")
            return jsonify({"text": qr_text})
        else:
            logger.warning(
                f"❌ [/scan] {client_ip} - No se detectó QR después de {processing_time:.2f}s")
            return jsonify({"error": "No se pudo detectar código QR"}), 404

    except Exception as e:
        logger.error(
            f"💥 [/scan] {client_ip} - Error procesando {filename}: {str(e)}")
        return jsonify({"error": f"Error: {str(e)}"}), 500


@app.route('/scan-base64', methods=['POST'])
def scan_qr_base64():
    """Endpoint para escanear QR desde base64"""
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    logger.info(f"📥 [/scan-base64] Nueva petición desde {client_ip}")

    try:
        json_data = request.get_json()
        if not json_data or 'image' not in json_data:
            logger.warning(
                f"❌ [/scan-base64] {client_ip} - Falta campo 'image' en JSON")
            return jsonify({"error": "Falta el campo 'image' con datos base64"}), 400

        base64_string = json_data['image']
        base64_length = len(base64_string)
        logger.info(
            f"📊 [/scan-base64] {client_ip} - Base64 recibido: {base64_length} caracteres")

        # Remover prefijo data:image si existe
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]
            logger.info(
                f"🔧 [/scan-base64] {client_ip} - Removido prefijo data:image")

        # Decodificar base64
        image_data = base64.b64decode(base64_string)
        logger.info(
            f"🔓 [/scan-base64] {client_ip} - Base64 decodificado: {len(image_data)} bytes")

        # Crear imagen desde bytes
        img = Image.open(io.BytesIO(image_data))
        logger.info(
            f"🖼️  [/scan-base64] {client_ip} - Imagen creada: {img.size} píxeles, modo: {img.mode}")

        start_time = datetime.now()
        qr_text = decode_qr(img)
        processing_time = (datetime.now() - start_time).total_seconds()

        if qr_text:
            logger.info(
                f"✅ [/scan-base64] {client_ip} - QR detectado en {processing_time:.2f}s: '{qr_text}'")
            return jsonify({"text": qr_text})
        else:
            logger.warning(
                f"❌ [/scan-base64] {client_ip} - No se detectó QR después de {processing_time:.2f}s")
            return jsonify({"error": "No se pudo detectar código QR"}), 404

    except Exception as e:
        logger.error(f"💥 [/scan-base64] {client_ip} - Error: {str(e)}")
        return jsonify({"error": f"Error: {str(e)}"}), 500


@app.route('/scan-url', methods=['POST'])
def scan_qr_from_url():
    """Endpoint para escanear QR desde URL de imagen"""
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    logger.info(f"📥 [/scan-url] Nueva petición desde {client_ip}")
    
    start_time = datetime.now()
    
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            logger.warning(f"❌ [/scan-url] {client_ip} - Falta campo 'url' en JSON")
            return jsonify({'error': 'Falta el campo "url" con la URL de la imagen'}), 400
        
        image_url = data['url']
        logger.info(f"🔗 [/scan-url] {client_ip} - Descargando desde: {image_url}")
        
        # Descargar imagen
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        logger.info(f"📥 [/scan-url] {client_ip} - Imagen descargada: {len(response.content)} bytes")
        
        # Convertir a imagen PIL desde bytes
        img = Image.open(io.BytesIO(response.content))
        logger.info(f"�️  [/scan-url] {client_ip} - Imagen creada: {img.size} píxeles, modo: {img.mode}")
        
        # Procesar QR
        qr_text = decode_qr(img)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if qr_text:
            logger.info(f"✅ [/scan-url] {client_ip} - QR detectado en {processing_time:.2f}s: '{qr_text}'")
            return jsonify({'text': qr_text})
        else:
            logger.warning(f"❌ [/scan-url] {client_ip} - No se detectó QR después de {processing_time:.2f}s")
            return jsonify({'error': 'No se encontró código QR'}), 404
            
    except requests.exceptions.RequestException as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"💥 [/scan-url] {client_ip} - Error descargando imagen en {processing_time:.2f}s: {str(e)}")
        return jsonify({'error': f'Error descargando imagen: {str(e)}'}), 500
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"💥 [/scan-url] {client_ip} - Error procesando URL en {processing_time:.2f}s: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    logger.info(f"💚 [/health] Health check desde {client_ip}")
    return jsonify({"status": "healthy", "service": "qr-scanner", "timestamp": datetime.now().isoformat()})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Iniciando QR Scanner Service en puerto {port}")
    logger.info(f"📋 Endpoints disponibles:")
    logger.info(f"   • POST /scan - Multipart form-data")
    logger.info(f"   • POST /scan-base64 - JSON base64")
    logger.info(f"   • POST /scan-url - JSON con URL de imagen")
    logger.info(f"   • GET /health - Health check")
    app.run(host='0.0.0.0', port=port, debug=False)