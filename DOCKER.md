# 🐳 QR Scanner Service - Docker Setup

## 📋 Archivos Docker Creados

- `Dockerfile` - Imagen optimizada del servicio QR
- `docker-compose.yml` - Servicio QR independiente
- `docker-compose.n8n.yml` - Stack completo con n8n
- `.dockerignore` - Optimización de build
- Scripts de utilidad (*.sh)

## 🚀 Opciones de Despliegue

### 1. Solo QR Scanner Service

```bash
# Iniciar servicio independiente
./start-stack.sh

# Probar servicio
./test-docker.sh

# Detener
./stop-stack.sh
```

**Acceso:** http://localhost:5000

### 2. QR Scanner + n8n (Stack Completo)

```bash
# Iniciar stack completo
./start-n8n-stack.sh

# Detener
docker compose -f docker-compose.n8n.yml down
```

**Acceso:**
- QR Scanner: http://localhost:5000
- n8n: http://localhost:5678

## 🔧 Configuración para n8n

### Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|---------|-------------|
| `/scan` | POST | Escaneo normal |
| `/scan-debug` | POST | Escaneo con información de técnica |
| `/health` | GET | Health check |

### Configuración HTTP Request Node

```yaml
URL: http://qr-scanner:5000/scan-debug
Method: POST
Body Type: Form-Data
Fields:
  - Name: file
  - Type: Binary Data
  - Value: {{ $binary.data }}
```

### Ejemplo de Respuesta

```json
{
  "text": "{\"vehicle_id\": \"VEH004\", \"name\": \"Vehículo VEH004\"}",
  "technique": "pil_high_contrast"
}
```

## 🧪 Testing

### Prueba Manual con cURL

```bash
# Health check
curl http://localhost:5000/health

# Escanear imagen
curl -X POST -F "file=@qr.jpg" http://localhost:5000/scan-debug
```

### Prueba desde n8n

1. Importar workflow: `n8n/workflows/qr-scanner-example.json`
2. Activar workflow
3. Enviar POST con imagen a webhook
4. Recibir respuesta procesada

## 🔒 Características de Seguridad

- ✅ Usuario no-root en contenedor
- ✅ Health checks configurados
- ✅ Imagen base oficial Python slim
- ✅ Limpieza de cache apt
- ✅ Variables de entorno seguras

## 📊 Monitoreo

```bash
# Ver logs
docker logs qr-scanner-service

# Estado del contenedor
docker ps --filter "name=qr-scanner"

# Recursos utilizados
docker stats qr-scanner-service
```

## 🔄 Actualizaciones

```bash
# Rebuild después de cambios
docker compose build --no-cache
docker compose up -d
```

## 🌐 Configuración de Red

### Red Interna (con n8n)

- Network: `n8n-network`
- Hostname interno: `qr-scanner`
- Puerto interno: 5000

### Red Externa

- Puerto expuesto: 5000
- Acceso: localhost:5000

## 📋 Variables de Entorno

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `FLASK_ENV` | production | Modo de Flask |
| `PYTHONUNBUFFERED` | 1 | Logs en tiempo real |
| `FLASK_APP` | app.py | Archivo principal |

## 🚨 Troubleshooting

### Contenedor no inicia

```bash
# Ver logs detallados
docker logs qr-scanner-service --details

# Verificar build
docker compose build --no-cache
```

### Health check falla

```bash
# Verificar endpoint manualmente
docker exec qr-scanner-service curl localhost:5000/health
```

### Problemas de red con n8n

```bash
# Verificar conectividad interna
docker exec n8n curl http://qr-scanner:5000/health
```