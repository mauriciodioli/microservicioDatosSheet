# Usa una imagen base con Python 3.12
FROM python:3.12

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Asegúrate de que python y pip apunten a Python 3.12
RUN ln -sf /usr/local/bin/python3.12 /usr/local/bin/python
RUN ln -sf /usr/local/bin/pip3.12 /usr/local/bin/pip

# Instala Python y pip (esto no debería ser necesario si ya usas python:3.12)
RUN apt-get update && apt-get install -y python3 python3-pip

# Verifica la versión de Python
RUN python --version

# Instala/actualiza typing-extensions antes de las dependencias
RUN pip install --upgrade typing-extensions

# Copia los archivos de requisitos a la imagen
COPY requirements.txt .

# Instala las dependencias necesarias
RUN pip3 install --no-cache-dir -r requirements.txt

# Actualiza pyRofex
RUN pip3 install -U pyRofex

# Desinstala la librería websocket y luego la vuelve a instalar
RUN pip3 uninstall -y websocket && pip3 install websocket-client

# Copia el contenido de tu proyecto a la imagen
COPY . .

# Establece las variables de entorno necesarias
ENV FLASK_APP=app/app.py
ENV FLASK_ENV=development

# Comando por defecto para ejecutar la aplicación
CMD ["flask", "run", "--host=0.0.0.0"]
