from app import db
from datetime import datetime, timezone


class CamerasModel(db.Model):
    __tablename__ = 'cameras'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    camera_name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rtsp_url = db.Column(db.String(255))
    location = db.Column(db.String(100))
    status = db.Column(db.String(10), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    zones = db.relationship('ZonesModel', backref='camera', cascade="all, delete", lazy=True)

    def __repr__(self):
        return f'<Camera {self.camera_name}>'

    def to_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'camera_name': self.camera_name,
            'ip_address': self.ip_address,
            'username': self.username,
            'password': self.password,
            'rtsp_url': self.rtsp_url,
            'location': self.location,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ZonesModel(db.Model):
    __tablename__ = 'zones'

    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id', ondelete="CASCADE"), nullable=False)
    coords = db.Column(db.JSON, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    alert_threshold = db.Column(db.Integer, nullable=False)
    schedule_start = db.Column(db.Time, nullable=False)
    schedule_end = db.Column(db.Time, nullable=False)
    alert_telegram = db.Column(db.String(255), nullable=True)
    alert_email = db.Column(db.String(255), nullable=True)

    alerts = db.relationship('AlertsModel', backref='zone', cascade="all, delete", lazy=True)

    def __repr__(self):
        return f'<Zone {self.type}>'

    def to_json(self):
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'coords': self.coords,
            'type': self.type,
            'alert_threshold': self.alert_threshold,
            'schedule_start': self.schedule_start.isoformat() if self.schedule_start else None,
            'schedule_end': self.schedule_end.isoformat() if self.schedule_end else None,
            'alert_telegram': self.alert_telegram,
            'alert_email': self.alert_email
        }


class AlertsModel(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id', ondelete="CASCADE"), nullable=False)
    alert_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    video_url = db.Column(db.String(255), nullable=False)
    person_count = db.Column(db.Integer, default=1, nullable=False)

    def __repr__(self):
        return f'<Alert {self.id}>'

    def to_json(self):
        
        alert_time_str = self.alert_time.isoformat() + "Z"  # Z indica UTC
        
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'alert_time': alert_time_str,
            'video_url': self.video_url,
            'person_count': self.person_count
        }
