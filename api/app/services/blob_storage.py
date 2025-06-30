from azure.storage.blob import BlobServiceClient, ContainerSasPermissions, generate_container_sas, generate_blob_sas, BlobSasPermissions, ContentSettings
import os
from dotenv import load_dotenv
import logging
import datetime



load_dotenv()

# Configuración de la conexión
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("application.log"),  # Guardar en un archivo
        logging.StreamHandler()  # Mostrar en consola
    ]
)


# Subir video al Blob Storage
def upload_video_to_blob(video_path, user_id):
    """
    Sube un video al Blob Storage en la ruta: <user_id>/<YYYY-MM-DD>/<YYYY-MM-DD_HH-MM-SS>.mp4
    """
    # Obtener fecha y hora actual
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    datetime_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    blob_name = f"{user_id}/{date_str}/{datetime_str}.mp4"

    logging.info(f"Iniciando subida del video {video_path} al blob {blob_name}.")
    try:
        # Crear el cliente del servicio Blob
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        # Verificar si el contenedor existe
        if not container_client.exists():
            logging.error(f"El contenedor {CONTAINER_NAME} no existe.")
            return False, None

        # Subir el archivo
        with open(video_path, "rb") as data:
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=True, content_settings=ContentSettings(content_type="video/mp4"))
            logging.info(f"Video {blob_name} subido exitosamente al contenedor {CONTAINER_NAME}.")

        return blob_name
    except Exception as e:
        logging.error(f"Error al subir el video al Blob Storage: {e}")
        return False, None


# Eliminar video del Blob Storage
def delete_video_from_blob(blob_name):
    logging.info(f"Iniciando eliminación del video {blob_name}.")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        blob_client = container_client.get_blob_client(blob_name)
        blob_client.delete_blob()
        logging.info(f"Video {blob_name} eliminado exitosamente del contenedor {CONTAINER_NAME}.")

        return True
    except Exception as e:
        logging.error(f"Error al eliminar el video del Blob Storage: {e}")
        return False


# Obtener video del Blob Storage
def download_video_from_blob(blob_name, download_path):
    logging.info(f"Iniciando descarga del video {blob_name} a {download_path}.")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        blob_client = container_client.get_blob_client(blob_name)
        with open(download_path, "wb") as file:
            download_stream = blob_client.download_blob()
            file.write(download_stream.readall())
            logging.info(f"Video {blob_name} descargado exitosamente en {download_path}.")

        return True
    except Exception as e:
        logging.error(f"Error al descargar el video del Blob Storage: {e}")
        return False


# Listar todos los videos en el Blob Storage
def list_videos_in_blob():
    logging.info(f"Listando videos en el contenedor {CONTAINER_NAME}.")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)

        blob_list = container_client.list_blobs()
        videos = [blob.name for blob in blob_list]
        logging.info(f"Videos encontrados: {videos}")

        return videos
    except Exception as e:
        logging.error(f"Error al listar los videos del Blob Storage: {e}")
        return []
    
def get_blob_sas_url(blob_path):
    logging.info(f"Generando SAS URL para el blob {blob_path}.")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

        # Generar un SAS token con permisos de lectura
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=CONTAINER_NAME,
            blob_name=blob_path,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.datetime.now() + datetime.timedelta(days=30) 
        )

        sas_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob_path}?{sas_token}"
        logging.info(f"SAS URL generada: {sas_url}")

        return sas_url
    except Exception as e:
        logging.error(f"Error al generar la SAS URL: {e}")
        return None
    