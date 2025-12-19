from datetime import datetime

from ..extensions import db


class Room(db.Model):
    """
    Модель номера в отеле.

    ВАЖНО: здесь нет булевого поля is_available.
    Вместо этого используется метод is_available, который проверяет
    наличие пересекающихся бронирований по датам. Ранее совпадение
    имени колонки и метода приводило к тому, что метод «затирал» колонку
    SQLAlchemy, что является грубой архитектурной ошибкой.
    """

    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey("hotels.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price_per_night = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=1)
    amenities = db.Column(db.String(300))
    image_url = db.Column(db.String(500))
    # Если понадобится «ручное» выключение номера из продажи,
    # лучше добавить поле вроде is_active / is_published, а не дублировать логику доступности по датам.

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def is_available(self, check_in, check_out):
        """
        Проверяет, свободен ли номер на указанные даты.

        Логика:
        - ищем хотя бы одно бронирование, которое пересекается по датам
          с заданным интервалом;
        - игнорируем отменённые бронирования (status != 'cancelled').
        """
        from .booking import Booking

        conflicting_booking = Booking.query.filter(
            Booking.room_id == self.id,
            Booking.status != "cancelled",
            Booking.check_in < check_out,
            Booking.check_out > check_in,
        ).first()
        return conflicting_booking is None

    def __repr__(self) -> str:
        return f"<Room {self.name}>"

