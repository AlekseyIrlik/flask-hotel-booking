from flask import Flask, render_template
from sqlalchemy import event
from sqlalchemy.engine import Engine
import os

from .config import Config
from .extensions import csrf, db, login_manager
from .routes.main import main
from .routes.user import user
from .routes.admin import admin


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Включаем поддержку foreign keys для SQLite"""
    if dbapi_connection.__class__.__module__ == 'sqlite3':
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        # Для лучшей производительности
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    # Создаем директорию instance если её нет
    os.makedirs(app.instance_path, exist_ok=True)

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Настройка Flask-Login
    login_manager.login_view = "user.login"
    login_manager.login_message = "Пожалуйста, войдите для доступа к этой странице."
    login_manager.login_message_category = "info"

    # Регистрация blueprints
    app.register_blueprint(user)
    app.register_blueprint(main)
    app.register_blueprint(admin)

    # Создание таблиц
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("База данных SQLite успешно инициализирована")
        except Exception as e:
            app.logger.error(f"Ошибка создания базы данных SQLite: {e}")
            # Не падаем при ошибке, продолжаем работу

    return app
