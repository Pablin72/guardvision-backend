from app import create_app
from flask_cors import CORS
from threading import Thread
from app.services.telegram_bot import run_bot
from multiprocessing import Process

from flasgger import Swagger

# Configuración del servidor Flask
app = create_app()
CORS(app)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "swagger_ui": True,
    "specs_route": "/apidocs/",
    "securityDefinitions": {
        "ApiKeyAuth": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header"
        }
    },
    "swagger_ui_bundle_js": "//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js",
    "swagger_ui_standalone_preset_js": "//unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js",
    "swagger_ui_css": "//unpkg.com/swagger-ui-dist@3/swagger-ui.css",
}

swagger = Swagger(app, config=swagger_config, template_file=None)

if __name__ == "__main__":
    # Iniciar el bot de Telegram en un proceso separado
    # Nota: Cambié de Thread a Process para evitar problemas de bloqueo
    bot_process = Process(target=run_bot, daemon=True)
    bot_process.start()

    # Iniciar el servidor Flask
    app.run(host="0.0.0.0", port=5020)
