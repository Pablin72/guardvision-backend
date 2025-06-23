# Usa la imagen oficial de PostgreSQL
FROM postgres:16

# Establece las variables de entorno para PostgreSQL
ENV POSTGRES_USER=guardvision
ENV POSTGRES_PASSWORD=guardvision2024
ENV POSTGRES_DB=guardvision-database

# Copia el script SQL al contenedor
COPY init.sql /docker-entrypoint-initdb.d/

# Expone el puerto 5432 para conexiones externas
EXPOSE 5432



