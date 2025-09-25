#!/bin/bash
echo "📊 QR Scanner - Visualización de Logs"
echo "======================================"
echo ""
echo "Selecciona opción:"
echo "1. Ver logs de Docker en tiempo real"
echo "2. Ver logs del archivo en tiempo real" 
echo "3. Ver últimas 50 líneas de Docker"
echo "4. Ver últimas 50 líneas del archivo"
echo "5. Ver todos los logs de Docker"
echo ""

read -p "Opción (1-5): " option

case $option in
    1)
        echo "📡 Logs de Docker en tiempo real (Ctrl+C para salir):"
        docker logs -f qr-scanner-dev
        ;;
    2)
        echo "📄 Logs del archivo en tiempo real (Ctrl+C para salir):"
        tail -f logs/qr_scanner.log
        ;;
    3)
        echo "📋 Últimas 50 líneas de Docker:"
        docker logs --tail 50 qr-scanner-dev
        ;;
    4)
        echo "📋 Últimas 50 líneas del archivo:"
        tail -50 logs/qr_scanner.log
        ;;
    5)
        echo "📚 Todos los logs de Docker:"
        docker logs qr-scanner-dev
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac