# Usa una imagen base oficial de Python
FROM python:3.12

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de requisitos a la imagen
COPY requirements.txt .

# Instala las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el contenido de tu proyecto a la imagen
COPY . .

# Establece las variables de entorno necesarias
ENV FLASK_APP=app/app.py
ENV FLASK_ENV=development

# Expone el puerto en el que se ejecutará la aplicación
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["flask", "run", "--host=0.0.0.0"]
