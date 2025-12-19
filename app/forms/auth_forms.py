from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Телефон', validators=[
                        DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Пароль', validators=[
                             DataRequired(), Length(min=6)])
    password_confirm = PasswordField('Подтвердите пароль',
                                     validators=[DataRequired(), EqualTo('password')])
    first_name = StringField(
        'Имя', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Фамилия', validators=[
                            DataRequired(), Length(min=2, max=50)])
    role = SelectField('Тип аккаунта',
                       choices=[('user', 'Пользователь'),
                                ('hotel_owner', 'Владелец отеля')],
                       validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')
