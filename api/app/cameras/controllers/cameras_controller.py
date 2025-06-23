from flask import Blueprint, request, jsonify
from app import db
from app.cameras.models.CamerasModel import CamerasModel
from app.login.utils.token import token_required

from cryptography.fernet import Fernet
import os

cameras_bp = Blueprint('cameras', __name__)

FERNET_KEY = os.getenv('FERNET_KEY')

cipher = Fernet(FERNET_KEY)

def encrypt_data(data: str) -> str:
    """
    Encripta un dato sensible.
    """
    return cipher.encrypt(data.encode()).decode()


@cameras_bp.route('/cameras', methods=['GET'])
@token_required
def get_cameras(current_user):
    """
    Obtener todas las cámaras del usuario autenticado.
    ---
    tags:
      - Cameras
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Lista de cámaras del usuario
        schema:
          type: array
          items:
            type: object
      401:
        description: No autorizado
    """
    cameras = CamerasModel.query.filter_by(user_id=current_user.id).all()
    return jsonify([camera.to_json() for camera in cameras]), 200


@cameras_bp.route('/cameras/<int:id>', methods=['GET'])
@token_required
def get_camera(current_user, id):
    """
    Obtener una cámara específica por ID, solo si pertenece al usuario autenticado.
    ---
    tags:
      - Cameras
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de la cámara
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Cámara encontrada
        schema:
          type: object
      404:
        description: Cámara no encontrada o no pertenece al usuario
      401:
        description: No autorizado
    """
    # Filtrar la cámara por id y user_id del usuario actual
    camera = CamerasModel.query.filter_by(id=id, user_id=current_user.id).first()

    if not camera:
        return jsonify({'error': 'Cámara no encontrada o no pertenece al usuario.'}), 404

    return jsonify(camera.to_json()), 200


@cameras_bp.route('/cameras', methods=['POST'])
@token_required
def create_camera(current_user):
    """
    Crear una nueva cámara para el usuario autenticado.
    ---
    tags:
      - Cameras
    security:
      - ApiKeyAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            camera_name:
              type: string
            ip_address:
              type: string
            username:
              type: string
            password:
              type: string
            rtsp_url:
              type: string
            location:
              type: string
            status:
              type: string
    responses:
      201:
        description: Cámara creada exitosamente
        schema:
          type: object
      400:
        description: Datos inválidos
      401:
        description: No autorizado
    """
    data = request.json

    # Encriptar la contraseña y la url RTSP antes de guardarla

    # Encriptar la contraseña y la URL RTSP antes de guardarlas
    if 'password' in data:
        data['password'] = encrypt_data(data['password'])
    if 'rtsp_url' in data:
        data['rtsp_url'] = encrypt_data(data['rtsp_url'])


    camera = CamerasModel(
        user_id=current_user.id,
        camera_name=data.get('camera_name'),
        ip_address=data.get('ip_address'),
        username=data.get('username'),
        password=data.get('password'),
        rtsp_url=data.get('rtsp_url'),
        location=data.get('location'),
        status=data.get('status', 'active')
    )
    db.session.add(camera)
    db.session.commit()
    return jsonify(camera.to_json()), 201


@cameras_bp.route('/cameras/<int:id>', methods=['PUT'])
@token_required
def update_camera(current_user, id):
    """
    Actualizar una cámara existente del usuario autenticado.
    ---
    tags:
      - Cameras
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de la cámara
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            camera_name:
              type: string
            ip_address:
              type: string
            username:
              type: string
            password:
              type: string
            rtsp_url:
              type: string
            location:
              type: string
            status:
              type: string
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Cámara actualizada exitosamente
        schema:
          type: object
      404:
        description: Cámara no encontrada o no pertenece al usuario
      401:
        description: No autorizado
    """
    camera = CamerasModel.query.filter_by(id=id, user_id=current_user.id).first()

    if not camera:
        return jsonify({'error': 'Cámara no encontrada o no pertenece al usuario.'}), 404

    data = request.json

    # Encriptar la contraseña y la URL RTSP antes de guardarlas
    if 'password' in data:
        data['password'] = encrypt_data(data['password'])
    if 'rtsp_url' in data:
        data['rtsp_url'] = encrypt_data(data['rtsp_url'])

    camera.camera_name = data.get('camera_name', camera.camera_name)
    camera.ip_address = data.get('ip_address', camera.ip_address)
    camera.username = data.get('username', camera.username)
    camera.password = data.get('password', camera.password)
    camera.rtsp_url = data.get('rtsp_url', camera.rtsp_url)
    camera.location = data.get('location', camera.location)
    camera.status = data.get('status', camera.status)
    db.session.commit()
    return jsonify(camera.to_json()), 200


@cameras_bp.route('/cameras/<int:id>', methods=['DELETE'])
@token_required
def delete_camera(current_user, id):
    """
    Eliminar una cámara específica por ID, solo si pertenece al usuario autenticado.
    ---
    tags:
      - Cameras
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de la cámara
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Cámara eliminada exitosamente
        schema:
          type: object
      404:
        description: Cámara no encontrada o no pertenece al usuario
      401:
        description: No autorizado
    """
    # Buscar la cámara por ID y asegurarse de que pertenece al usuario actual
    camera = CamerasModel.query.filter_by(id=id, user_id=current_user.id).first()

    if not camera:
        return jsonify({'error': 'Cámara no encontrada o no pertenece al usuario.'}), 404

    # Eliminar la cámara
    db.session.delete(camera)
    db.session.commit()
    return jsonify({'message': 'Cámara eliminada exitosamente.'}), 200

