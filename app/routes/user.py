from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import validate_csrf
from wtforms import ValidationError
from flask_wtf import FlaskForm
from datetime import datetime

from app.extensions import db
from app.forms.auth_forms import LoginForm, RegistrationForm
from app.forms.profile_forms import EditProfileForm, ChangePasswordForm
from app.forms.hotel_forms import HotelForm
from app.forms.room_forms import RoomForm
from app.models.booking import Booking
from app.models.hotel import Hotel
from app.models.room import Room
from app.models.user import User, UserRole

user = Blueprint("user", __name__)


@user.route("/register", methods=["GET", "POST"])
def register():
    """Регистрация нового пользователя."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Проверяем уникальность email/телефона
        existing_user = User.query.filter(
            (User.email == form.email.data) | (User.phone == form.phone.data)
        ).first()

        if existing_user:
            flash("Пользователь с таким email или телефоном уже существует", "danger")
            return redirect(url_for("user.register"))

        # Создаём пользователя
        user = User(
            email=form.email.data,
            phone=form.phone.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=UserRole(form.role.data)
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Регистрация прошла успешно! Теперь вы можете войти.", "success")
        return redirect(url_for("user.login"))

    return render_template("user/register.html", form=form)


@user.route("/login", methods=["GET", "POST"])
def login():
    """Вход в систему."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            flash("Вы успешно вошли!", "success")
            return redirect(url_for("main.index"))
        else:
            flash("Неверный email или пароль", "danger")

    return render_template("user/login.html", form=form)


@user.route("/logout")
@login_required
def logout():
    """Выход из системы."""
    logout_user()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("main.index"))


@user.route("/profile")
@login_required
def profile():
    """Простой профиль пользователя."""
    return render_template("user/profile.html", user=current_user)


@user.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Редактирование профиля."""
    form = EditProfileForm(obj=current_user)

    if form.validate_on_submit():
        # Проверка уникальности email
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Пользователь с таким email уже существует', 'danger')
                return redirect(url_for('user.edit_profile'))

        # Проверка уникальности телефона
        if form.phone.data != current_user.phone:
            existing_user = User.query.filter_by(phone=form.phone.data).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Пользователь с таким телефоном уже существует', 'danger')
                return redirect(url_for('user.edit_profile'))

        # Обновление данных
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data

        db.session.commit()
        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('user.profile'))

    return render_template("user/edit_profile.html", form=form)


@user.route("/profile/security", methods=["GET", "POST"])
@login_required
def security():
    """Смена пароля."""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Пароль успешно изменен', 'success')
            return redirect(url_for('user.profile'))
        else:
            flash('Текущий пароль указан неверно', 'danger')

    return render_template("user/security.html", form=form)


@user.route("/profile/delete", methods=["POST"])
@login_required
def delete_account():
    """Удаление аккаунта."""
    try:
        validate_csrf(request.form.get('csrf_token'))

        # Проверяем активные бронирования
        active_bookings = Booking.query.filter_by(
            user_id=current_user.id,
            status='confirmed'
        ).filter(Booking.check_out >= datetime.now().date()).count()

        if active_bookings > 0:
            flash('Невозможно удалить аккаунт с активными бронированиями', 'danger')
            return redirect(url_for('user.security'))

        # Проверяем отели владельца
        if current_user.is_hotel_owner:
            hotels_count = Hotel.query.filter_by(
                owner_id=current_user.id).count()
            if hotels_count > 0:
                flash('Невозможно удалить аккаунт владельца отелей', 'danger')
                return redirect(url_for('user.security'))

        # Удаляем пользователя
        email = current_user.email
        db.session.delete(current_user)
        db.session.commit()

        logout_user()
        flash(f'Ваш аккаунт {email} был успешно удален', 'success')
        return redirect(url_for('main.index'))

    except ValidationError:
        flash('Ошибка безопасности', 'danger')
        return redirect(url_for('user.security'))
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении аккаунта: {str(e)}', 'danger')
        return redirect(url_for('user.security'))


@user.route("/my-bookings")
@login_required
def my_bookings():
    """Мои бронирования."""
    bookings = (
        Booking.query.filter_by(user_id=current_user.id)
        .join(Room, Room.id == Booking.room_id)
        .join(Hotel, Hotel.id == Room.hotel_id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return render_template("user/my_bookings.html", bookings=bookings)


@user.route("/booking/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking(booking_id):
    """Отмена бронирования."""
    booking = Booking.query.get_or_404(booking_id)

    # Проверяем, что бронирование принадлежит текущему пользователю
    if booking.user_id != current_user.id:
        abort(403)

    # Меняем статус
    booking.status = "cancelled"
    db.session.commit()

    flash("Бронирование отменено", "success")
    return redirect(url_for("user.my_bookings"))


@user.route("/hotels")
@login_required
def my_hotels():
    """Мои отели (для владельцев)."""
    if not current_user.is_hotel_owner:
        abort(403)

    hotels = Hotel.query.filter_by(owner_id=current_user.id).all()
    return render_template("user/my_hotels.html", hotels=hotels)


@user.route("/hotels/create", methods=["GET", "POST"])
@login_required
def create_hotel():
    """Создание отеля."""
    if not current_user.is_hotel_owner:
        abort(403)

    form = HotelForm()
    if form.validate_on_submit():
        hotel = Hotel(
            name=form.name.data,
            description=form.description.data,
            address=form.address.data,
            city=form.city.data,
            phone=form.phone.data,
            email=form.email.data,
            owner_id=current_user.id
        )
        db.session.add(hotel)
        db.session.commit()
        flash("Отель успешно создан", "success")
        return redirect(url_for("user.my_hotels"))
    return render_template("user/hotel_form.html", form=form, title="Создать отель")


@user.route("/hotels/<int:hotel_id>/edit", methods=["GET", "POST"])
@login_required
def edit_hotel(hotel_id):
    """Редактирование отеля."""
    hotel = Hotel.query.get_or_404(hotel_id)
    if hotel.owner_id != current_user.id or not current_user.is_hotel_owner:
        abort(403)

    form = HotelForm(obj=hotel)
    if form.validate_on_submit():
        hotel.name = form.name.data
        hotel.description = form.description.data
        hotel.address = form.address.data
        hotel.city = form.city.data
        hotel.phone = form.phone.data
        hotel.email = form.email.data
        db.session.commit()
        flash("Отель обновлен", "success")
        return redirect(url_for("user.my_hotels"))
    return render_template("user/hotel_form.html", form=form, title="Редактировать отель")


@user.route("/hotels/<int:hotel_id>/delete", methods=["POST"])
@login_required
def delete_hotel(hotel_id):
    """Удаление отеля."""
    try:
        validate_csrf(request.form.get('csrf_token'))
        hotel = Hotel.query.get_or_404(hotel_id)
        if hotel.owner_id != current_user.id or not current_user.is_hotel_owner:
            abort(403)

        # Проверяем бронирования
        if Booking.query.join(Room).filter(Room.hotel_id == hotel_id).count() > 0:
            flash("Нельзя удалить отель с бронированиями", "danger")
            return redirect(url_for("user.my_hotels"))

        db.session.delete(hotel)
        db.session.commit()
        flash("Отель удален", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка: {str(e)}", "danger")
    return redirect(url_for("user.my_hotels"))


@user.route("/hotel/<int:hotel_id>/rooms")
@login_required
def hotel_rooms(hotel_id):
    """Номера в отеле."""
    hotel = Hotel.query.get_or_404(hotel_id)

    if hotel.owner_id != current_user.id:
        abort(403)

    rooms = Room.query.filter_by(hotel_id=hotel_id).all()
    return render_template("user/hotel_rooms.html", hotel=hotel, rooms=rooms)


@user.route("/hotel/<int:hotel_id>/rooms/create", methods=["GET", "POST"])
@login_required
def create_room(hotel_id):
    """Создание номера."""
    hotel = Hotel.query.get_or_404(hotel_id)
    if hotel.owner_id != current_user.id or not current_user.is_hotel_owner:
        abort(403)

    form = RoomForm()
    if form.validate_on_submit():
        room = Room(
            name=form.name.data,
            description=form.description.data,
            price_per_night=form.price_per_night.data,
            capacity=form.capacity.data,
            amenities=form.amenities.data,
            image_url=form.image_url.data,
            hotel_id=hotel_id
        )
        db.session.add(room)
        db.session.commit()
        flash("Номер создан", "success")
        return redirect(url_for("user.hotel_rooms", hotel_id=hotel_id))
    return render_template("user/room_form.html", form=form, title="Создать номер", hotel=hotel)


@user.route("/hotel/<int:hotel_id>/rooms/<int:room_id>/edit", methods=["GET", "POST"])
@login_required
def edit_room(hotel_id, room_id):
    """Редактирование номера."""
    hotel = Hotel.query.get_or_404(hotel_id)
    room = Room.query.get_or_404(room_id)
    if hotel.owner_id != current_user.id or not current_user.is_hotel_owner or room.hotel_id != hotel_id:
        abort(403)

    form = RoomForm(obj=room)
    if form.validate_on_submit():
        room.name = form.name.data
        room.description = form.description.data
        room.price_per_night = form.price_per_night.data
        room.capacity = form.capacity.data
        room.amenities = form.amenities.data
        room.image_url = form.image_url.data
        db.session.commit()
        flash("Номер обновлен", "success")
        return redirect(url_for("user.hotel_rooms", hotel_id=hotel_id))
    return render_template("user/room_form.html", form=form, title="Редактировать номер", hotel=hotel)


@user.route("/hotel/<int:hotel_id>/rooms/<int:room_id>/delete", methods=["POST"])
@login_required
def delete_room(hotel_id, room_id):
    """Удаление номера."""
    try:
        validate_csrf(request.form.get('csrf_token'))
        hotel = Hotel.query.get_or_404(hotel_id)
        room = Room.query.get_or_404(room_id)
        if hotel.owner_id != current_user.id or not current_user.is_hotel_owner or room.hotel_id != hotel_id:
            abort(403)

        # Проверяем бронирования
        if Booking.query.filter_by(room_id=room_id).count() > 0:
            flash("Нельзя удалить номер с бронированиями", "danger")
            return redirect(url_for("user.hotel_rooms", hotel_id=hotel_id))

        db.session.delete(room)
        db.session.commit()
        flash("Номер удален", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка: {str(e)}", "danger")
    return redirect(url_for("user.hotel_rooms", hotel_id=hotel_id))
