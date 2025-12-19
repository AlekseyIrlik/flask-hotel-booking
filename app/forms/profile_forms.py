from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

from app.models.user import User


class EditProfileForm(FlaskForm):
    """Форма редактирования профиля."""
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])

    phone = StringField('Телефон', validators=[
        DataRequired(message='Телефон обязателен'),
        Length(min=10, max=20, message='Телефон должен быть от 10 до 20 символов')
    ])

    first_name = StringField('Имя', validators=[
        DataRequired(message='Имя обязательно'),
        Length(min=2, max=50, message='Имя должно быть от 2 до 50 символов')
    ])

    last_name = StringField('Фамилия', validators=[
        DataRequired(message='Фамилия обязательна'),
        Length(min=2, max=50, message='Фамилия должна быть от 2 до 50 символов')
    ])

    submit = SubmitField('Сохранить изменения')


class ChangePasswordForm(FlaskForm):
    """Форма смены пароля."""
    current_password = PasswordField('Текущий пароль', validators=[
        DataRequired(message='Введите текущий пароль')
    ])

    new_password = PasswordField('Новый пароль', validators=[
        DataRequired(message='Введите новый пароль'),
        Length(min=8, message='Пароль должен быть не менее 8 символов'),
        EqualTo('confirm_password', message='Пароли должны совпадать')
    ])

    confirm_password = PasswordField('Подтвердите новый пароль', validators=[
        DataRequired(message='Подтвердите новый пароль')
    ])

    submit = SubmitField('Сменить пароль')
