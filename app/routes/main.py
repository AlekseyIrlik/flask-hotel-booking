from flask import render_template, request, flash, redirect, url_for, Blueprint
from flask_login import login_required, current_user
from app.extensions import db
from app.models.hotel import Hotel
from app.models.room import Room
from app.models.booking import Booking
from app.forms.booking_forms import BookingForm

main = Blueprint('main', __name__)


@main.route("/")
def index():
    """
    Главная страница.
    """
    # Показываем первые 3 отеля из базы
    popular_hotels = Hotel.query.order_by(
        Hotel.created_at.desc()).limit(3).all()
    return render_template("index.html", popular_hotels=popular_hotels)


@main.route('/catalog')
def catalog():
    """
    Каталог отелей с фильтрацией по городу.
    """
    city = request.args.get('city', '')
    query = Hotel.query

    if city:
        query = query.filter(Hotel.city.ilike(f'%{city}%'))

    hotels = query.all()
    return render_template('catalog.html', hotels=hotels, city=city)


@main.route('/hotel/<int:hotel_id>')
def hotel_detail(hotel_id):
    """
    Страница отеля с номерами.
    """
    hotel = Hotel.query.get_or_404(hotel_id)
    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    return render_template('hotel_detail.html', hotel=hotel, rooms=rooms)


@main.route('/hotel/<int:hotel_id>/room/<int:room_id>/book', methods=['GET', 'POST'])
@login_required
def book_room(hotel_id, room_id):
    """
    Бронирование номера.
    """
    hotel = Hotel.query.get_or_404(hotel_id)
    room = Room.query.filter_by(id=room_id, hotel_id=hotel_id).first_or_404()
    form = BookingForm()

    if form.validate_on_submit():
        # 1. Проверяем даты
        if form.check_in.data >= form.check_out.data:
            flash('Дата выезда должна быть позже даты заезда.', 'danger')

        # 2. Проверяем доступность номера
        elif not room.is_available(form.check_in.data, form.check_out.data):
            flash('К сожалению, номер уже забронирован на эти даты.', 'danger')

        # 3. Проверяем гостей
        elif form.guests.data > room.capacity:
            flash(
                f'В этот номер можно разместить не более {room.capacity} гостей.', 'danger')
        else:
            # Всё ок, создаём бронь
            nights = (form.check_out.data - form.check_in.data).days
            booking = Booking(
                user_id=current_user.id,
                room_id=room.id,
                check_in=form.check_in.data,
                check_out=form.check_out.data,
                guests=form.guests.data,
                total_price=nights * room.price_per_night,
                status='confirmed'
            )
            db.session.add(booking)
            db.session.commit()
            flash('Бронирование успешно создано!', 'success')
            return redirect(url_for('user.my_bookings'))

    return render_template('book_room.html', hotel=hotel, room=room, form=form)


@main.route('/about')
def about():
    """Страница о проекте."""
    return render_template('about.html')


@main.route('/contact')
def contact():
    """Страница контактов."""
    return render_template('contact.html')
