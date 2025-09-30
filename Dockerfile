FROM python:3.12-slim

# Instalar dependencias del sistema y herramientas de desarrollo
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libzbar-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libdmtx0t64 \
    libdmtx-dev \
    build-essential \
    python3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Actualizar pip y instalar setuptools (incluye distutils)
RUN pip install --upgrade pip setuptools wheel

# Copiar e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicación
COPY app.py .

# Exponer puerto
EXPOSE 5000

# Ejecutar aplicación
CMD ["python", "app.py"]