import base64
from flask import Blueprint, request, jsonify
from app import db
from app.login.models.UsersModel import UsersModel
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from app.login.utils.token import token_required
import bcrypt
from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet

# Configuración del Blueprint
users_bp = Blueprint('users', __name__)

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener la SECRET_KEY desde el entorno
SECRET_KEY = os.getenv('SECRET_KEY')

FERNET_KEY = os.getenv('FERNET_KEY')

cipher = Fernet(FERNET_KEY)


# Crear Usuario
@users_bp.route('/register', methods=['POST'])
def register_user():
    """
    Registrar un nuevo usuario.
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            lastname:
              type: string
            email:
              type: string
            password:
              type: string
    responses:
      201:
        description: Usuario creado exitosamente
      400:
        description: Faltan campos requeridos
      500:
        description: No se pudo crear el usuario
    """
    data = request.get_json()

    if not data or not all(k in data for k in ('name', 'lastname', 'email', 'password')):
        return jsonify({'message': 'Missing fields!'}), 400

    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


    new_user = UsersModel(
        name=data['name'],
        lastname=data['lastname'],
        email=data['email'],
        password=hashed_password
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'User could not be created!', 'error': str(e)}), 500

# Iniciar Sesión
@users_bp.route('/login', methods=['POST'])
def login_user():
    """
    Iniciar sesión de usuario.
    ---
    tags:
      - Users
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login exitoso, retorna token JWT
        schema:
          type: object
          properties:
            message:
              type: string
            token:
              type: string
      400:
        description: Faltan email o password
      401:
        description: Email o password inválidos
    """
    print(f"SECRET_KEY: {os.getenv('SECRET_KEY')}")
    
    data = request.get_json()

    if not data or not all(k in data for k in ('email', 'password')):
        return jsonify({'message': 'Missing email or password!'}), 400

    user = UsersModel.query.filter_by(email=data['email']).first()

    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({'message': 'Invalid email or password!'}), 401
    
    # Encriptar el ID del usuario
    encrypted_id = cipher.encrypt(str(user.id).encode('utf-8'))


    # Generar el token JWT   
    token = jwt.encode({
        'id':  encrypted_id.decode('utf-8'),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({'message': 'Login successful!', 'token': token}), 200

# Obtener Usuario Actual (Requiere Token)
@users_bp.route('/current_user', methods=['GET'])
@token_required
def get_current_user(current_user):
    """
    Obtener información del usuario autenticado.
    ---
    tags:
      - Users
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Información del usuario actual
        schema:
          type: object
      401:
        description: No autorizado
    """
    return jsonify(current_user.to_json()), 200

# Cambiar Contraseña
@users_bp.route('/change_password', methods=['POST'])
@token_required
def change_password(current_user):
    """
    Cambiar la contraseña del usuario autenticado.
    ---
    tags:
      - Users
    security:
      - ApiKeyAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            old_password:
              type: string
            new_password:
              type: string
    responses:
      200:
        description: Contraseña actualizada exitosamente
      400:
        description: Faltan campos requeridos
      401:
        description: Contraseña antigua incorrecta o no autorizado
      500:
        description: No se pudo actualizar la contraseña
    """
    data = request.get_json()

    if not data or not all(k in data for k in ('old_password', 'new_password')):
        return jsonify({'message': 'Missing fields!'}), 400

    if not bcrypt.checkpw(data['old_password'].encode('utf-8'), current_user.password.encode('utf-8')):
        return jsonify({'message': 'Old password is incorrect!'}), 401


    current_user.password = bcrypt.hashpw(data['new_password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        db.session.commit()
        return jsonify({'message': 'Password updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Password could not be updated!', 'error': str(e)}), 500

# Eliminar Cuenta
@users_bp.route('/delete_account', methods=['DELETE'])
@token_required
def delete_account(current_user):
    """
    Eliminar la cuenta del usuario autenticado.
    ---
    tags:
      - Users
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Cuenta eliminada exitosamente
      500:
        description: No se pudo eliminar la cuenta
    """
    try:
        db.session.delete(current_user)
        db.session.commit()
        return jsonify({'message': 'Account deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Account could not be deleted!', 'error': str(e)}), 500
