from flask import Blueprint, request, jsonify, g
from app import db
from app.cameras.models.CamerasModel import ZonesModel, CamerasModel
from app.login.utils.token import token_required

zones_bp = Blueprint('zones', __name__)

@zones_bp.route('/zones', methods=['GET'])
@token_required
def get_zones(current_user):
    """
    Obtener todas las zonas asociadas a las cámaras del usuario autenticado.
    ---
    tags:
      - Zones
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Lista de zonas del usuario
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: ID de la zona
              camera_id:
                type: integer
                description: ID de la cámara asociada
              coords:
                type: array
                items:
                  type: object
                  properties:
                    x:
                      type: integer
                    y:
                      type: integer
              type:
                type: string
                description: Tipo de la zona
              alert_threshold:
                type: integer
                description: Umbral de alerta
              schedule_start:
                type: string
                format: time
                description: Hora de inicio del horario
              schedule_end:
                type: string
                format: time
                description: Hora de fin del horario
              alert_telegram:
                type: string
                description: Correo electrónico para alertas
              alert_email:
                type: string
                description: Correo electrónico para alertas
        examples:
          application/json:
            - id: 1
              camera_id: 5
              coords:
                - x: 50
                  y: 83
                - x: 149
                  y: 274
              type: critical
              alert_threshold: 10
              schedule_start: "00:00"
              schedule_end: "23:59"
              alert_telegram: "123456789"
              alert_email: "example@example.com"
            - id: 2
              camera_id: 8
              coords:
                - x: 328
                  y: 126
                - x: 293
                  y: 319
              type: warning
              alert_threshold: 5
              schedule_start: "08:00"
              schedule_end: "20:00"
              alert_telegram: "123456789"
              alert_email: "example@example.com"
      401:
        description: No autorizado
    """

    print("Current User ID:", current_user.id)  # Debugging line

    # Filtrar las zonas relacionadas con las cámaras del usuario
    zones = ZonesModel.query.join(CamerasModel).filter(CamerasModel.user_id == current_user.id).all()

    print("Zona:", zones)
    return jsonify([zone.to_json() for zone in zones]), 200

@zones_bp.route('/camera/zones/<int:camera_id>', methods=['GET'])
@token_required
def get_camera_zones(current_user, camera_id):
    """
    Obtener todas las zonas de una cámara específica del usuario autenticado.
    ---
    tags:
      - Zones
    parameters:
      - name: camera_id
        in: path
        type: integer
        required: true
        description: ID de la cámara
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Lista de zonas de la cámara
        schema:
          type: array
          items:
            type: object
        examples:
          application/json:
            - id: 1
              camera_id: 5
              coords:
                - x: 50
                  y: 83
                - x: 149
                  y: 274
              type: critical
              alert_threshold: 10
              schedule_start: "00:00"
              schedule_end: "23:59"
              alert_telegram: "123456789"
              alert_email: "example@example.com"
      401:
        description: No autorizado
      404:
        description: Cámara no encontrada o no pertenece al usuario
    """
    # Filtrar las zonas relacionadas con las cámaras del usuario
    zones = ZonesModel.query.join(CamerasModel).filter(CamerasModel.user_id == current_user.id, ZonesModel.camera_id == camera_id).all()
    return jsonify([zone.to_json() for zone in zones]), 200

@zones_bp.route('/zones/<int:id>', methods=['GET'])
@token_required
def get_zone(current_user, id):
    """
    Obtener una zona específica por ID, solo si pertenece a una cámara del usuario autenticado.
    ---
    tags:
      - Zones
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de la zona
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Zona encontrada
        schema:
          type: object
          properties:
            id:
              type: integer
              description: ID de la zona
            camera_id:
              type: integer
              description: ID de la cámara asociada
            coords:
              type: array
              items:
                type: object
                properties:
                  x:
                    type: integer
                  y:
                    type: integer
            type:
              type: string
              description: Tipo de la zona
            alert_threshold:
              type: integer
              description: Umbral de alerta
            schedule_start:
              type: string
              format: time
              description: Hora de inicio del horario
            schedule_end:
              type: string
              format: time
              description: Hora de fin del horario
            alert_telegram:
              type: string
              description: Chat id de Telegram para alertas
            alert_email:
              type: string
              description: Correo electrónico para alertas
        examples:
          application/json:
            id: 1
            camera_id: 5
            coords:
              - x: 50
                y: 83
              - x: 149
                y: 274
            type: critical
            alert_threshold: 10
            schedule_start: "00:00"
            schedule_end: "23:59"
            alert_telegram: "123456789"
            alert_email: "example@example.com"
      401:
        description: No autorizado
      404:
        description: Zona no encontrada o no pertenece al usuario
    """
    # Filtrar la zona por el `id` y asegurarse de que pertenece a una cámara del usuario
    zone = ZonesModel.query.join(CamerasModel).filter(ZonesModel.id == id, CamerasModel.user_id == current_user.id).first_or_404()
    return jsonify(zone.to_json()), 200

@zones_bp.route('/zones', methods=['POST'])
@token_required
def create_zones(current_user):
    """
    Crear una o varias zonas para cámaras del usuario autenticado.
    ---
    tags:
      - Zones
    security:
      - ApiKeyAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            zones:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  coords:
                    type: array
                    items:
                      type: object
                      properties:
                        x:
                          type: integer
                        y:
                          type: integer
                  type:
                    type: string
                  alertThreshold:
                    type: integer
                  scheduleStart:
                    type: string
                  scheduleEnd:
                    type: string
                  alertEmail:
                    type: string
                  alertTelegram:
                    type: string
                  alertSentFlags:
                    type: array
                    items:
                      type: integer
        examples:
          application/json:
            value:
              zones:
                - id: 1
                  coords:
                    - x: 50
                      y: 83
                    - x: 149
                      y: 274
                    - x: 223
                      y: 182
                    - x: 145
                      y: 71
                    - x: 52
                      y: 171
                  type: critical
                  alertThreshold: 10
                  scheduleStart: "00:00"
                  scheduleEnd: "23:59"
                  alertEmail: "alexis151270sassa"
                  alertTelegram: "123456789"
                - id: 2
                  coords:
                    - x: 328
                      y: 126
                    - x: 293
                      y: 319
                    - x: 300
                      y: 356
                    - x: 551
                      y: 128
                  type: critical
                  alertThreshold: 10
                  scheduleStart: "00:00"
                  scheduleEnd: "23:59"
                  alertEmail: "b"
                  alertTelegram: "123456789"
                  alertSentFlags: [4]
                - id: 2
                  coords:
                    - x: 98
                      y: 326
                    - x: 81
                      y: 378
                    - x: 169
                      y: 401
                    - x: 200
                      y: 340
                    - x: 181
                      y: 304
                    - x: 83
                      y: 304
                  type: critical
                  alertThreshold: 10
                  scheduleStart: "00:00"
                  scheduleEnd: "23:59"
                  alertEmail: "example@example.com"
                  alertTelegram: "123456789"
                  alertSentFlags: [16]
    responses:
      201:
        description: Zonas creadas exitosamente
        schema:
          type: array
          items:
            type: object
      400:
        description: Datos inválidos
      401:
        description: No autorizado
      404:
        description: Cámara no encontrada o no pertenece al usuario
    """
    data = request.json
    if not data or 'zones' not in data:
        return jsonify({'error': 'Invalid data format'}), 400

    created_zones = []

    for zone_data in data['zones']:
        camera_id = zone_data.get('id')
        # Verificar que la cámara pertenece al usuario
        camera = CamerasModel.query.filter_by(id=camera_id, user_id=current_user.id).first()
        if not camera:
            return jsonify({'error': f'Camera {camera_id} not found or not authorized'}), 404

        zone = ZonesModel(
            camera_id=camera_id,
            coords=zone_data.get('coords'),
            type=zone_data.get('type'),
            alert_threshold=zone_data.get('alertThreshold'),
            schedule_start=zone_data.get('scheduleStart'),
            schedule_end=zone_data.get('scheduleEnd'),
            alert_telegram=zone_data.get('alertTelegram'),
            alert_email=zone_data.get('alertEmail'),
        )
        db.session.add(zone)
        created_zones.append(zone)

    db.session.commit()
    return jsonify([zone.to_json() for zone in created_zones]), 201

@zones_bp.route('/zones/<int:id>', methods=['PUT'])
@token_required
def update_zone(current_user, id):
    """
    Actualizar una zona existente del usuario autenticado.
    ---
    tags:
      - Zones
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de la zona
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            coords:
              type: array
              items:
                type: object
            type:
              type: string
            alert_threshold:
              type: integer
            schedule_start:
              type: string
            schedule_end:
              type: string
            alert_telegram:
              type: string
            alert_email:
              type: string
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Zona actualizada exitosamente
        schema:
          type: object
      401:
        description: No autorizado
      404:
        description: Zona no encontrada o no pertenece al usuario
    """
    # Asegurarse de que la zona pertenece a una cámara del usuario
    zone = ZonesModel.query.join(CamerasModel).filter(ZonesModel.id == id, CamerasModel.user_id == current_user.id).first_or_404()
    data = request.json
    zone.coords = data.get('coords', zone.coords)
    zone.type = data.get('type', zone.type)
    zone.alert_threshold = data.get('alert_threshold', zone.alert_threshold)
    zone.schedule_start = data.get('schedule_start', zone.schedule_start)
    zone.schedule_end = data.get('schedule_end', zone.schedule_end)
    zone.alert_telegram = data.get('alert_telegram', zone.alert_telegram)
    zone.alert_email = data.get('alert_email', zone.alert_email)
    db.session.commit()
    return jsonify(zone.to_json()), 200

@zones_bp.route('/zones/<int:id>', methods=['DELETE'])
@token_required
def delete_zone(current_user, id):
    """
    Eliminar una zona específica por ID, solo si pertenece a una cámara del usuario autenticado.
    ---
    tags:
      - Zones
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de la zona
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Zona eliminada exitosamente
        schema:
          type: object
      401:
        description: No autorizado
      404:
        description: Zona no encontrada o no pertenece al usuario
    """
    # Asegurarse de que la zona pertenece a una cámara del usuario
    zone = ZonesModel.query.join(CamerasModel).filter(ZonesModel.id == id, CamerasModel.user_id == current_user.id).first_or_404()
    db.session.delete(zone)
    db.session.commit()
    return jsonify({'message': 'Zone deleted'}), 200
