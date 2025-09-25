#!/bin/bash
echo "🚀 Iniciando QR Scanner (Modo Desarrollo)..."
echo "📁 Los logs se guardarán en ./logs/"

# Crear directorio de logs si no existe
mkdir -p logs

docker compose up --build -d

echo "⏳ Esperando servicio..."
sleep 8

if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Servicio listo en http://localhost:5000"
    echo ""
    echo "📋 Endpoints disponibles:"
    echo "   • GET  /health"
    echo "   • POST /scan (multipart)"
    echo "   • POST /scan-base64 (JSON)"
    echo ""
    echo "🧪 Prueba con:"
    echo "curl -X POST -F \"file=@wsp.jpeg\" http://localhost:5000/scan"
    echo ""
    echo "📊 Ver logs en tiempo real:"
    echo "docker logs -f qr-scanner-dev"
    echo "tail -f logs/qr_scanner.log"
else
    echo "❌ Error iniciando servicio"
    echo "🔍 Ver logs: docker logs qr-scanner-dev"
fi