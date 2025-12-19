from datetime import datetime

from ..extensions import db


class Booking(db.Model):
    """
    Модель бронирования номера.

    Важно:
    - у брони есть внешний ключ на пользователя (user_id) и номер (room_id);
    - через relationships доступны booking.user и booking.room,
      что необходимо для шаблонов (например, booking.room.hotel.name).
    """

    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Отношения для удобного доступа в Python и шаблонах Jinja2
    user = db.relationship("User", backref="bookings", lazy=True)
    room = db.relationship("Room", backref="bookings", lazy=True)

    def __repr__(self) -> str:
        return f"<Booking {self.id} - Room {self.room_id}>"

