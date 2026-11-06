from datetime import datetime
from app.extensions import db

class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    @classmethod
    def get_value(cls, key, default=None):
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default

    @classmethod
    def set_value(cls, key, value, description=None):
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = str(value)
            if description:
                setting.description = description
        else:
            setting = cls(setting_key=key, setting_value=str(value), description=description)
            db.session.add(setting)
        db.session.commit()
        return setting

    def __repr__(self):
        return f"<Setting {self.setting_key}={self.setting_value}>"


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    target_table = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)

    @classmethod
    def log(cls, action, admin_id=None, table=None, target_id=None, details=None, ip=None):
        log_entry = cls(
            action=action,
            admin_id=admin_id,
            target_table=table,
            target_id=target_id,
            details=details,
            ip_address=ip
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.target_table}>"


class BackupLog(db.Model):
    __tablename__ = 'backup_logs'

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger, default=0, nullable=False)
    backup_type = db.Column(db.String(20), default='auto', nullable=False)  # auto, manual
    status = db.Column(db.String(20), default='success', nullable=False)  # success, failed
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    @property
    def formatted_size(self):
        size_kb = self.file_size / 1024
        if size_kb > 1024:
            return f"{size_kb / 1024:.2f} MB"
        return f"{size_kb:.1f} KB"

    def __repr__(self):
        return f"<BackupLog {self.file_name} ({self.status})>"
