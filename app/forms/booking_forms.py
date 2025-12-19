from datetime import date, timedelta

from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange


class BookingForm(FlaskForm):
    """
    Форма бронирования номера.

    ВАЖНО: значения по умолчанию для дат задаём через callables (lambda),
    чтобы они вычислялись при каждом создании формы, а не один раз при
    импорте модуля. Иначе при долго работающем приложении «сегодня» устареет.
    """

    check_in = DateField(
        "Дата заезда",
        validators=[DataRequired()],
        default=lambda: date.today() + timedelta(days=1),
    )
    check_out = DateField(
        "Дата выезда",
        validators=[DataRequired()],
        default=lambda: date.today() + timedelta(days=2),
    )
    guests = IntegerField(
        "Количество гостей",
        validators=[DataRequired(), NumberRange(min=1, max=10)],
        default=1,
    )
    special_requests = TextAreaField("Особые пожелания")
    submit = SubmitField("Забронировать")

