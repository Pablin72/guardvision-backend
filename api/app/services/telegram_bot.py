from threading import Thread
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import InputFile
import asyncio
import logging

from dotenv import load_dotenv
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("application.log"),  # Guardar en un archivo
        logging.StreamHandler()  # Mostrar en consola
    ]
)


# Cargar variables de entorno desde el archivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN=os.getenv('TELEGRAM_BOT_TOKEN')

BOT_USERNAME = os.getenv('BOT_USERNAME')

CHAT_ID = "1170100910"

application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_name = update.message.from_user.first_name
    await update.message.reply_text(
        f"¡Hola {user_name}! Tu Chat ID es: {chat_id}. Por favor, proporciónalo en la aplicación para recibir notificaciones."
    )

# Función para inicializar y correr el bot
application.add_handler(CommandHandler("start", start))

def run_bot():
    # 1) Elimina cualquier webhook (y borra updates pendientes)
    application.bot.delete_webhook(drop_pending_updates=True)

    # 2) Crea un loop nuevo y arranca polling descartando también los updates
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        application.run_polling(drop_pending_updates=True)
    )
    
# Función para enviar un video por Telegram
async def send_intruder_video(video_path, chat_id):
    try:
        # Enviar mensaje de texto primero
        await application.bot.send_message(
            chat_id=chat_id,
            text="¡Alerta! Se detectó un intruso. Enviando video..."
        )
        logging.info(f"Iniciando envío del video {video_path} al chat ID: {chat_id}.")
        with open(video_path, 'rb') as video_file:
            await application.bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption="¡Se ha detectado un intruso!"
            )
        logging.info("Video enviado exitosamente.")
    except Exception as e:
        logging.error(f"Error al enviar el video por Telegram: {e}")

# Wrapper para llamar a la función async desde Flask
def notify_intruder(video_path, chat_id):
    logging.info(f"Notificación de intruso iniciada con el video: {video_path}.")
    asyncio.run(send_intruder_video(video_path, chat_id))