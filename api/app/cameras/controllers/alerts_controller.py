import multiprocessing
import tempfile
import threading
from flask import Blueprint, request, jsonify
from telegram import Bot
from app import db
from app.cameras.models.CamerasModel import AlertsModel, CamerasModel, ZonesModel
from datetime import datetime, timedelta, date
from sqlalchemy import extract, func

from app.login.utils.token import token_required

from app.services.blob_storage import get_blob_sas_url, upload_video_to_blob
from app.services.telegram_bot import notify_intruder
import uuid
import os

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('/alerts', methods=['GET'])
@token_required
def get_alerts(current_user):
    """
    Obtener todas las alertas de las zonas que pertenecen a las cámaras del usuario autenticado.
    ---
    tags:
      - Alerts
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Lista de alertas
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: ID de la alerta
              zone_id:
                type: integer
                description: ID de la zona asociada a la alerta
              video_url:
                type: string
                description: URL del video asociado a la alerta
              created_at:
                type: string
                format: date-time
                description: Fecha y hora de creación de la alerta
        examples:
          application/json:
            - id: 1
              zone_id: 5
              video_url: "https://example.com/video1.mp4"
              created_at: "2025-04-24T12:00:00Z"
            - id: 2
              zone_id: 8
              video_url: "https://example.com/video2.mp4"
              created_at: "2025-04-24T12:30:00Z"
      401:
        description: No autorizado
    """
    # Obtener todas las cámaras del usuario
    cameras = CamerasModel.query.filter_by(user_id=current_user.id).all()
    
    # Obtener todas las alertas de las zonas que pertenecen a las cámaras del usuario
    alerts = AlertsModel.query.join(ZonesModel).filter(ZonesModel.camera_id.in_([camera.id for camera in cameras])).all()

    # Retornar las alertas en formato JSON
    return jsonify([alert.to_json() for alert in alerts]), 200


@alerts_bp.route('/alerts/<int:id>', methods=['GET'])
@token_required
def get_alert(current_user, id):
    """
    Obtener una alerta específica por ID, solo si pertenece a una cámara del usuario autenticado.
    ---
    tags:
      - Alerts
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de la alerta
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Alerta encontrada
        schema:
          type: object
          properties:
            id:
              type: integer
              description: ID de la alerta
            zone_id:
              type: integer
              description: ID de la zona asociada a la alerta
            video_url:
              type: string
              description: URL del video asociado a la alerta
            created_at:
              type: string
              format: date-time
              description: Fecha y hora de creación de la alerta
        examples:
          application/json:
            id: 1
            zone_id: 5
            video_url: "https://example.com/video1.mp4"
            created_at: "2025-04-24T12:00:00Z"
      404:
        description: Alerta no encontrada
      401:
        description: No autorizado
    """
    # Obtener todas las cámaras del usuario
    cameras = CamerasModel.query.filter_by(user_id=current_user.id).all()

    # Buscar la alerta, asegurándose de que pertenece a una cámara del usuario
    alert = AlertsModel.query.join(ZonesModel).filter(ZonesModel.camera_id.in_([camera.id for camera in cameras])).filter(AlertsModel.id == id).first()
    
    if alert is None:
        return jsonify({'message': 'Alert not found'}), 404
    
    return jsonify(alert.to_json()), 200


TEMP_VIDEO_PATH = os.path.join(tempfile.gettempdir(), "intruder_temp.mp4")  # Ruta temporal dinámica para almacenar el video
# Enviar mensaje de texto a Telegram (sin bloquear)
def send_telegram_video(path, chat_id):
    try:
        notify_intruder(path, chat_id)
    except Exception as e:
        # Loguea el error, pero no bloquees la respuesta al usuario
        print(f"Error al enviar el video por Telegram: {e}")
    finally:
        # esto solo se ejecuta cuando notify_intruder cierra el archivo
        if os.path.exists(path):
            os.remove(path)




@alerts_bp.route('/alerts', methods=['POST'])
@token_required
def create_alert(current_user):
    """
    Crear una nueva alerta subiendo un video MP4.
    ---
    tags:
      - Alerts
    consumes:
      - multipart/form-data
    parameters:
      - name: zone_id
        in: formData
        type: integer
        required: true
        description: ID de la zona asociada a la alerta
      - name: video
        in: formData
        type: file
        required: true
        description: Archivo de video MP4
    security:
      - ApiKeyAuth: []
    responses:
      201:
        description: Alerta creada exitosamente
        schema:
          type: object
      400:
        description: Datos inválidos
      401:
        description: No autorizado
    """
    if 'video' not in request.files or 'zone_id' not in request.form:
        return jsonify({'message': 'Datos inválidos'}), 400

    video_file = request.files['video']
    zone_id = request.form['zone_id']
    
    zone = ZonesModel.query.filter_by(id=zone_id).first()

    if not zone:
        return jsonify({'message': 'Zona no encontrada'}), 404

    # Guardar el video temporalmente
    video_file.save(TEMP_VIDEO_PATH)


    process = multiprocessing.Process(target=send_telegram_video, args=(TEMP_VIDEO_PATH, zone.alert_telegram))
    process.start()

    # Sube a blob y crea la alerta en base de datos
    blob_name = upload_video_to_blob(TEMP_VIDEO_PATH, current_user.id)
    
    # Obtener SAS Url del video subido
    if blob_name:
        blob_url = get_blob_sas_url(blob_name)
    else:
        blob_url = ""
    
    alert = AlertsModel(zone_id=zone_id, video_url=blob_url)
    db.session.add(alert)
    db.session.commit()

    return jsonify(alert.to_json()), 201

@alerts_bp.route('/alerts/<int:id>', methods=['DELETE'])
@token_required
def delete_alert(current_user, id):
    """
    Eliminar una alerta específica por ID, solo si pertenece a una cámara del usuario autenticado.
    ---
    tags:
      - Alerts
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de la alerta
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Alerta eliminada exitosamente
      404:
        description: Alerta no encontrada o no pertenece al usuario
      401:
        description: No autorizado
    """
    # Obtener todas las cámaras del usuario
    cameras = CamerasModel.query.filter_by(user_id=current_user.id).all()

    # Buscar la alerta y verificar que pertenece a una cámara del usuario
    alert = AlertsModel.query.join(ZonesModel).filter(ZonesModel.camera_id.in_([camera.id for camera in cameras])).filter(AlertsModel.id == id).first()

    # Verificar si la alerta fue encontrada
    if alert is None:
        return jsonify({'message': 'Alert not found or does not belong to your cameras'}), 404

    # Eliminar la alerta
    db.session.delete(alert)
    db.session.commit()

    return jsonify({'message': 'Alert deleted'}), 200


@alerts_bp.route('/stats/daily-count', methods=['GET'])
@token_required
def get_daily_alert_count(current_user):
    """
    Obtener el número de alertas por día dentro de un rango de fechas.
    ---
    tags:
      - Stats
    parameters:
      - name: start_date
        in: query
        type: string
        format: date
        required: false
        description: Fecha de inicio (formato YYYY-MM-DD). Por defecto es hace 30 días.
      - name: end_date
        in: query
        type: string
        format: date
        required: false
        description: Fecha de fin (formato YYYY-MM-DD). Por defecto es hoy.
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Conteo diario de alertas
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                format: date
                description: Fecha (YYYY-MM-DD)
              count:
                type: integer
                description: Número de alertas en ese día
      400:
        description: Parámetros inválidos
      401:
        description: No autorizado
    """
    # Obtener parámetros de la solicitud
    try:
        start_date_str = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date_str = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Asegurar que end_date es igual o posterior a start_date
        if end_date < start_date:
            return jsonify({'message': 'La fecha de fin debe ser igual o posterior a la fecha de inicio'}), 400
    except ValueError:
        return jsonify({'message': 'Formato de fecha inválido. Usar YYYY-MM-DD'}), 400
    
    # Obtener todas las cámaras del usuario
    cameras = CamerasModel.query.filter_by(user_id=current_user.id).all()
    camera_ids = [camera.id for camera in cameras]
    
    # Obtener todas las alertas por día
    result = db.session.query(
        func.date(AlertsModel.alert_time).label('date'),
        func.count(AlertsModel.id).label('count')
    ).join(ZonesModel).filter(
        ZonesModel.camera_id.in_(camera_ids),
        func.date(AlertsModel.alert_time) >= start_date,
        func.date(AlertsModel.alert_time) <= end_date
    ).group_by(
        func.date(AlertsModel.alert_time)
    ).order_by(
        func.date(AlertsModel.alert_time)
    ).all()
    
    # Crear un diccionario para almacenar resultados, incluyendo días sin alertas
    daily_counts = {}
    current_date = start_date
    while current_date <= end_date:
        daily_counts[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)
    
    # Llenar con datos reales
    for date_obj, count in result:
        date_str = date_obj.strftime('%Y-%m-%d')
        daily_counts[date_str] = count
    
    # Convertir a lista para la respuesta JSON
    response_data = [{'date': date_str, 'count': count} for date_str, count in daily_counts.items()]
    
    return jsonify(response_data), 200


@alerts_bp.route('/stats/daily-alerts/<string:date>', methods=['GET'])
@token_required
def get_alerts_by_day(current_user, date):
    """
    Obtener todas las alertas de un día específico.
    ---
    tags:
      - Stats
    parameters:
      - name: date
        in: path
        type: string
        format: date
        required: true
        description: Fecha (formato YYYY-MM-DD)
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Lista de alertas del día especificado
      400:
        description: Formato de fecha inválido
      401:
        description: No autorizado
    """
    try:
        # Validar formato de fecha
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        next_date = target_date + timedelta(days=1)
    except ValueError:
        return jsonify({'message': 'Formato de fecha inválido. Usar YYYY-MM-DD'}), 400
    
    # Obtener todas las cámaras del usuario
    cameras = CamerasModel.query.filter_by(user_id=current_user.id).all()
    camera_ids = [camera.id for camera in cameras]
    
    # Obtener alertas del día específico
    alerts = AlertsModel.query.join(ZonesModel).filter(
        ZonesModel.camera_id.in_(camera_ids),
        AlertsModel.alert_time >= datetime.combine(target_date, datetime.min.time()),
        AlertsModel.alert_time < datetime.combine(next_date, datetime.min.time())
    ).all()
    
    return jsonify([alert.to_json() for alert in alerts]), 200


@alerts_bp.route('/stats/person-count', methods=['GET'])
@token_required
def get_daily_person_count(current_user):
    """
    Obtener el conteo diario de personas detectadas dentro de un rango de fechas.
    ---
    tags:
      - Stats
    parameters:
      - name: start_date
        in: query
        type: string
        format: date
        required: false
        description: Fecha de inicio (formato YYYY-MM-DD). Por defecto es hace 30 días.
      - name: end_date
        in: query
        type: string
        format: date
        required: false
        description: Fecha de fin (formato YYYY-MM-DD). Por defecto es hoy.
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Conteo diario de personas detectadas
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                format: date
                description: Fecha (YYYY-MM-DD)
              count:
                type: integer
                description: Número total de personas detectadas en ese día
      400:
        description: Parámetros inválidos
      401:
        description: No autorizado
    """
    # Obtener parámetros de la solicitud
    try:
        start_date_str = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date_str = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Asegurar que end_date es igual o posterior a start_date
        if end_date < start_date:
            return jsonify({'message': 'La fecha de fin debe ser igual o posterior a la fecha de inicio'}), 400
    except ValueError:
        return jsonify({'message': 'Formato de fecha inválido. Usar YYYY-MM-DD'}), 400
    
    # Obtener todas las cámaras del usuario
    cameras = CamerasModel.query.filter_by(user_id=current_user.id).all()
    camera_ids = [camera.id for camera in cameras]
    
    # Obtener el conteo diario de personas
    result = db.session.query(
        func.date(AlertsModel.alert_time).label('date'),
        func.sum(AlertsModel.person_count).label('count')
    ).join(ZonesModel).filter(
        ZonesModel.camera_id.in_(camera_ids),
        func.date(AlertsModel.alert_time) >= start_date,
        func.date(AlertsModel.alert_time) <= end_date
    ).group_by(
        func.date(AlertsModel.alert_time)
    ).order_by(
        func.date(AlertsModel.alert_time)
    ).all()
    
    # Crear un diccionario para almacenar resultados, incluyendo días sin alertas
    daily_counts = {}
    current_date = start_date
    while current_date <= end_date:
        daily_counts[current_date.strftime('%Y-%m-%d')] = 0
        current_date += timedelta(days=1)
    
    # Llenar con datos reales
    for date_obj, count in result:
        date_str = date_obj.strftime('%Y-%m-%d')
        daily_counts[date_str] = count
    
    # Convertir a lista para la respuesta JSON
    response_data = [{'date': date_str, 'count': count} for date_str, count in daily_counts.items()]
    
    return jsonify(response_data), 200


@alerts_bp.route('/stats/alerts-by-zone', methods=['GET'])
@token_required
def get_alerts_by_zone(current_user):
    """
    Obtener el número de alertas agrupadas por zona dentro de un rango de fechas.
    ---
    tags:
      - Stats
    parameters:
      - name: start_date
        in: query
        type: string
        format: date
        required: false
        description: Fecha de inicio (formato YYYY-MM-DD). Por defecto es hace 30 días.
      - name: end_date
        in: query
        type: string
        format: date
        required: false
        description: Fecha de fin (formato YYYY-MM-DD). Por defecto es hoy.
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Conteo de alertas por zona
        schema:
          type: array
          items:
            type: object
            properties:
              zone_id:
                type: integer
                description: ID de la zona
              zone_type:
                type: string
                description: Tipo de zona
              camera_name:
                type: string
                description: Nombre de la cámara
              count:
                type: integer
                description: Número de alertas en esa zona
      400:
        description: Parámetros inválidos
      401:
        description: No autorizado
    """
    # Obtener parámetros de la solicitud
    try:
        start_date_str = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date_str = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Asegurar que end_date es igual o posterior a start_date
        if end_date < start_date:
            return jsonify({'message': 'La fecha de fin debe ser igual o posterior a la fecha de inicio'}), 400
    except ValueError:
        return jsonify({'message': 'Formato de fecha inválido. Usar YYYY-MM-DD'}), 400
    
    # Obtener todas las cámaras del usuario
    cameras = CamerasModel.query.filter_by(user_id=current_user.id).all()
    camera_ids = [camera.id for camera in cameras]
    
    # Obtener alertas agrupadas por zona
    result = db.session.query(
        ZonesModel.id.label('zone_id'),
        ZonesModel.type.label('zone_type'),
        CamerasModel.camera_name.label('camera_name'),
        func.count(AlertsModel.id).label('count')
    ).join(ZonesModel, AlertsModel.zone_id == ZonesModel.id
    ).join(CamerasModel, ZonesModel.camera_id == CamerasModel.id
    ).filter(
        ZonesModel.camera_id.in_(camera_ids),
        func.date(AlertsModel.alert_time) >= start_date,
        func.date(AlertsModel.alert_time) <= end_date
    ).group_by(
        ZonesModel.id, ZonesModel.type, CamerasModel.camera_name
    ).order_by(
        func.count(AlertsModel.id).desc()
    ).all()
    
    # Preparar respuesta
    response_data = [
        {
            'zone_id': zone_id,
            'zone_type': zone_type,
            'camera_name': camera_name,
            'count': count
        } for zone_id, zone_type, camera_name, count in result
    ]
    
    return jsonify(response_data), 200


@alerts_bp.route('/stats/hourly-distribution', methods=['GET'])
@token_required
def get_hourly_distribution(current_user):
    """
    Obtener la distribución de alertas por hora del día dentro de un rango de fechas.
    ---
    tags:
      - Stats
    parameters:
      - name: start_date
        in: query
        type: string
        format: date
        required: false
        description: Fecha de inicio (formato YYYY-MM-DD). Por defecto es hace 30 días.
      - name: end_date
        in: query
        type: string
        format: date
        required: false
        description: Fecha de fin (formato YYYY-MM-DD). Por defecto es hoy.
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Distribución de alertas por hora
        schema:
          type: array
          items:
            type: object
            properties:
              hour:
                type: integer
                description: Hora del día (0-23)
              count:
                type: integer
                description: Número de alertas en esa hora
      400:
        description: Parámetros inválidos
      401:
        description: No autorizado
    """
    # Obtener parámetros de la solicitud
    try:
        start_date_str = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date_str = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Asegurar que end_date es igual o posterior a start_date
        if end_date < start_date:
            return jsonify({'message': 'La fecha de fin debe ser igual o posterior a la fecha de inicio'}), 400
    except ValueError:
        return jsonify({'message': 'Formato de fecha inválido. Usar YYYY-MM-DD'}), 400
    
    # Obtener todas las cámaras del usuario
    cameras = CamerasModel.query.filter_by(user_id=current_user.id).all()
    camera_ids = [camera.id for camera in cameras]
    
    # Obtener la distribución de alertas por hora
    result = db.session.query(
        func.extract('hour', AlertsModel.alert_time).label('hour'),
        func.count(AlertsModel.id).label('count')
    ).join(ZonesModel).filter(
        ZonesModel.camera_id.in_(camera_ids),
        func.date(AlertsModel.alert_time) >= start_date,
        func.date(AlertsModel.alert_time) <= end_date
    ).group_by(
        func.extract('hour', AlertsModel.alert_time)
    ).order_by(
        func.extract('hour', AlertsModel.alert_time)
    ).all()
    
    # Crear un diccionario para almacenar resultados, incluyendo horas sin alertas
    hourly_counts = {}
    for hour in range(24):
        hourly_counts[hour] = 0
    
    # Llenar con datos reales
    for hour, count in result:
        hourly_counts[int(hour)] = count
    
    # Convertir a lista para la respuesta JSON
    response_data = [{'hour': hour, 'count': count} for hour, count in hourly_counts.items()]
    
    return jsonify(response_data), 200


