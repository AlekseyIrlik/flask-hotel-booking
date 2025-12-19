#!/usr/bin/env python3
"""
Скрипт инициализации базы данных.
Запускается при старте контейнера, заполняет БД начальными данными.
"""

import sys
import os
import logging


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    from app.models.user import User
    from app.models.hotel import Hotel
    from app.models.room import Room
    from werkzeug.security import generate_password_hash
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    logger.error("Проверьте структуру моделей и зависимости")
    sys.exit(1)


def init_db():
    """Инициализация базы данных начальными данными."""
    try:
        app = create_app()

        with app.app_context():
            logger.info("Начинаем инициализацию базы данных...")

            # 1. Создаем таблицы (если их еще нет)
            # Если используете миграции Alembic, этот шаг можно пропустить
            # db.create_all()

            # 2. Проверяем, есть ли уже админ, чтобы не дублировать
            if User.query.filter_by(email='admin@example.com').first():
                logger.info(
                    "Администратор уже существует, пропускаем создание")
            else:
                admin = User(
                    email='admin@example.com',
                    password_hash=generate_password_hash('AdminPass123!'),
                    first_name='Алексей',
                    last_name='Ирлик',
                    phone='+79990001122',
                    role='admin'  # ИЛИ установите is_admin=True, если это колонка
                )
                db.session.add(admin)
                logger.info("✅ Администратор создан")

            # 3. Добавляем тестового владельца отеля
            owner_email = 'owner@example.com'
            owner = User.query.filter_by(email=owner_email).first()

            if owner:
                logger.info("Владелец отеля уже существует")
            else:
                owner = User(
                    email=owner_email,
                    password_hash=generate_password_hash('OwnerPass123!'),
                    first_name='Иван',
                    last_name='Отельеров',
                    phone='+79991112233',
                    role='hotel_owner'  # ИЛИ is_hotel_owner=True
                )
                db.session.add(owner)
                db.session.flush()  # Получаем ID владельца
                logger.info("✅ Владелец отеля создан")

            # 4. Создаем отель (если еще нет отелей)
            hotel_name = 'Grand Plaza Hotel'
            existing_hotel = Hotel.query.filter_by(name=hotel_name).first()

            if existing_hotel:
                logger.info(f"Отель '{hotel_name}' уже существует")
                hotel = existing_hotel
            else:
                hotel = Hotel(
                    name=hotel_name,
                    description='Роскошный отель в центре города с видом на море. Современные номера, спа-центр, ресторан.',
                    address='ул. Центральная, 1',
                    city='Москва',
                    phone='+74951234567',
                    email='info@grandplaza.ru',
                    owner_id=owner.id if owner else None,
                    amenities='Wi-Fi, Кондиционер, Ресторан, Спа, Бассейн'
                )
                db.session.add(hotel)
                db.session.flush()
                logger.info(f"✅ Отель '{hotel_name}' создан")

            # 5. Добавляем номера в этот отель
            rooms_data = [
                {
                    'name': 'Стандарт',
                    'description': 'Уютный номер с одной двуспальной кроватью, телевизором и мини-баром.',
                    'price_per_night': 3500,
                    'capacity': 2,
                    'amenities': 'Wi-Fi, ТВ, Мини-бар, Кондиционер',
                    'image_url': '/static/img/rooms/standard.jpg'
                },
                {
                    'name': 'Делюкс',
                    'description': 'Просторный номер с видом на город, гостиной зоной и джакузи.',
                    'price_per_night': 5500,
                    'capacity': 2,
                    'amenities': 'Wi-Fi, ТВ, Мини-бар, Кондиционер, Джакузи, Вид на город',
                    'image_url': '/static/img/rooms/deluxe.jpg'
                },
                {
                    'name': 'Люкс Президентский',
                    'description': 'Роскошный двухкомнатный номер с отдельной гостиной, рабочим кабинетом и панорамным видом.',
                    'price_per_night': 12000,
                    'capacity': 4,
                    'amenities': 'Wi-Fi, 2 ТВ, Мини-бар, Кондиционер, Джакузи, Вид на море, Отдельная гостиная',
                    'image_url': '/static/img/rooms/suite.jpg'
                },
            ]

            rooms_created = 0
            for i, room_data in enumerate(rooms_data, 1):
                # Проверяем, существует ли уже такой номер
                existing_room = Room.query.filter_by(
                    name=room_data['name'],
                    hotel_id=hotel.id
                ).first()

                if not existing_room:
                    room = Room(
                        **room_data,
                        hotel_id=hotel.id
                    )
                    db.session.add(room)
                    rooms_created += 1
                    logger.info(f"   Создан номер: {room_data['name']}")

            # 6. Создаем тестового пользователя (не владельца)
            if not User.query.filter_by(email='user@example.com').first():
                test_user = User(
                    email='user@example.com',
                    password_hash=generate_password_hash('UserPass123!'),
                    first_name='Мария',
                    last_name='Тестова',
                    phone='+79992223344',
                    role='user'
                )
                db.session.add(test_user)
                logger.info("✅ Тестовый пользователь создан")

            # 7. Фиксируем все изменения в базе
            db.session.commit()

            if rooms_created > 0:
                logger.info(f"✅ Создано {rooms_created} номера(ов)")

            logger.info("🎉 Инициализация базы данных успешно завершена!")

            # Выводим тестовые учетные данные для удобства
            print("\n" + "="*50)
            print("ТЕСТОВЫЕ УЧЕТНЫЕ ЗАПИСИ:")
            print("="*50)
            print("Администратор:")
            print("  Email: admin@example.com")
            print("  Пароль: AdminPass123!")
            print("\nВладелец отеля:")
            print("  Email: owner@example.com")
            print("  Пароль: OwnerPass123!")
            print("\nОбычный пользователь:")
            print("  Email: user@example.com")
            print("  Пароль: UserPass123!")
            print("="*50 + "\n")

            return True

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации базы данных: {e}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return False


if __name__ == '__main__':
    # Запуск инициализации
    success = init_db()
    sys.exit(0 if success else 1)
