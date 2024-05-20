from chartmaker import db
from datetime import datetime, timedelta

class UserData(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), nullable=False)
    df_data = db.Column(db.PickleType, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
