from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Email


class HotelForm(FlaskForm):
    name = StringField('Название отеля', validators=[
                       DataRequired(), Length(min=3, max=150)])
    description = TextAreaField('Описание', validators=[Length(max=1000)])
    address = StringField('Адрес', validators=[
                          DataRequired(), Length(max=300)])
    city = StringField('Город', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Телефон', validators=[Length(max=20)])
    email = StringField('Email', validators=[Email(), Length(max=150)])
    submit = SubmitField('Сохранить')
