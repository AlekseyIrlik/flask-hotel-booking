from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length


class RoomForm(FlaskForm):
    name = StringField('Название номера', validators=[
                       DataRequired(), Length(max=100)])
    description = TextAreaField('Описание', validators=[DataRequired()])
    price_per_night = IntegerField('Цена за ночь (руб)',
                                   validators=[DataRequired(), NumberRange(min=100, max=100000)])
    capacity = IntegerField('Вместимость',
                            validators=[DataRequired(), NumberRange(min=1, max=10)])
    amenities = StringField('Удобства (через запятую)',
                            validators=[Length(max=300)])
    image_url = StringField('URL фото', validators=[Length(max=200)])
    submit = SubmitField('Сохранить')
