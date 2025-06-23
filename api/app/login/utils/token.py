import base64
from dotenv import load_dotenv
from flask import request, jsonify
import jwt
import os
from functools import wraps

from app.login.models.UsersModel import UsersModel
from cryptography.fernet import Fernet


# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener la SECRET_KEY desde el entorno
SECRET_KEY = os.getenv('SECRET_KEY')


FERNET_KEY = os.getenv('FERNET_KEY')
cipher = Fernet(FERNET_KEY)

# Configuración JWT (Secreta y Expiración)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Leer el header de Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Eliminar el prefijo "Bearer" si está presente
            token = auth_header.split(" ")[1] if "Bearer " in auth_header else auth_header

            # Decodificar el token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            encrypted_id = data['id'].encode('utf-8')
            user_id = cipher.decrypt(encrypted_id).decode('utf-8')

            current_user = UsersModel.query.get(user_id)
            
            if not current_user:
                return jsonify({'message': 'User not found!'}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({'message': 'An error occurred while processing the token!', 'error': str(e)}), 500

        # Pasar el usuario actual a la función decorada
        return f(current_user, *args, **kwargs)
    return decorated
