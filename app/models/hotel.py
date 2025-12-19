from ..extensions import db
from datetime import datetime


class Hotel(db.Model):
    __tablename__ = 'hotels'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи (используем строки для ленивых импортов)
    owner = db.relationship('User', backref='hotels')
    rooms = db.relationship('Room', backref='hotel',
                            lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Hotel {self.name}>'
