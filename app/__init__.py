from flask import Flask, render_template

from .config import Config
from .extensions import csrf, db, login_manager, migrate
from .routes.main import main
from .routes.user import user
from .routes.admin import admin


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Настройка Flask-Login
    login_manager.login_view = "user.login"
    login_manager.login_message = "Пожалуйста, войдите для доступа к этой странице."
    login_manager.login_message_category = "info"

    # Регистрация blueprints (ТОЛЬКО user, main и admin)
    app.register_blueprint(user)
    app.register_blueprint(main)
    app.register_blueprint(admin)


    # Создание таблиц
    with app.app_context():
        try:
            db.create_all()
            print("База данных успешно инициализирована")
        except Exception as e:
            print(f"Ошибка создания базы данных: {e}")

    return app
