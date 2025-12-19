from functools import wraps
from flask import Blueprint, abort, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required
from flask_wtf.csrf import validate_csrf
from wtforms import ValidationError
from datetime import datetime, timedelta

from app.extensions import db
from app.models.booking import Booking
from app.models.hotel import Hotel
from app.models.user import User, UserRole
from app.models.room import Room

admin = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Декоратор для проверки прав администратора."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin.route("/")
@login_required
@admin_required
def dashboard():
    """Панель администратора."""
    # Основная статистика
    total_users = User.query.count()
    total_hotels = Hotel.query.count()
    total_bookings = Booking.query.count()

    # Статистика по статусам бронирований
    pending_bookings = Booking.query.filter_by(status="pending").count()
    confirmed_bookings = Booking.query.filter_by(status="confirmed").count()
    cancelled_bookings = Booking.query.filter_by(status="cancelled").count()

    # Активность за неделю
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = User.query.filter(User.created_at >= week_ago).count()
    recent_bookings = Booking.query.filter(
        Booking.created_at >= week_ago).count()

    # Владельцы отелей
    hotel_owners = User.query.filter_by(role=UserRole.HOTEL_OWNER).count()

    stats = {
        "total_users": total_users,
        "total_hotels": total_hotels,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "confirmed_bookings": confirmed_bookings,
        "cancelled_bookings": cancelled_bookings,
        "recent_users": recent_users,
        "recent_bookings": recent_bookings,
        "hotel_owners": hotel_owners,
    }

    return render_template("admin/dashboard.html", stats=stats)


@admin.route("/users")
@login_required
@admin_required
def users_list():
    """
    Список пользователей.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search_query = request.args.get('search', '').strip()

    query = User.query

    if search_query:
        query = query.filter(
            (User.email.ilike(f'%{search_query}%')) |
            (User.first_name.ilike(f'%{search_query}%')) |
            (User.last_name.ilike(f'%{search_query}%')) |
            (User.phone.ilike(f'%{search_query}%'))
        )

    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template("admin/users.html", users=users, search_query=search_query)


@admin.route("/users/<int:user_id>/set-role", methods=["POST"])
@login_required
@admin_required
def set_user_role(user_id: int):
    """
    Изменение роли пользователя.
    """
    try:
        validate_csrf(request.form.get('csrf_token'))

        role_value = request.form.get("role")
        if role_value not in {r.value for r in UserRole}:
            flash("Некорректная роль", "danger")
            return redirect(url_for("admin.users_list"))

        user = User.query.get_or_404(user_id)

        # Запрет на изменение собственной роли
        if user.id == current_user.id:
            flash("Вы не можете изменить свою собственную роль", "danger")
            return redirect(url_for("admin.users_list"))

        # Запрет на удаление последнего администратора
        if user.role == UserRole.ADMIN and role_value != UserRole.ADMIN.value:
            admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
            if admin_count <= 1:
                flash("Нельзя удалить последнего администратора", "danger")
                return redirect(url_for("admin.users_list"))

        old_role = user.role.value
        user.role = UserRole(role_value)
        db.session.commit()

        flash(
            f"Роль пользователя {user.email} изменена с '{old_role}' на '{role_value}'", "success")

    except ValidationError:
        flash("Ошибка безопасности. Попробуйте еще раз.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при изменении роли: {str(e)}", "danger")

    return redirect(url_for("admin.users_list"))


@admin.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id: int):
    """
    Удаление пользователя.
    """
    try:
        validate_csrf(request.form.get('csrf_token'))

        user = User.query.get_or_404(user_id)

        # Запрет на удаление самого себя
        if user.id == current_user.id:
            flash("Вы не можете удалить свой собственный аккаунт", "danger")
            return redirect(url_for("admin.users_list"))

        # Проверка, есть ли связанные данные
        if user.hotels:
            flash(
                f"Нельзя удалить пользователя {user.email}, так как у него есть отели", "danger")
            return redirect(url_for("admin.users_list"))

        # Проверка бронирований
        user_bookings = Booking.query.filter_by(user_id=user_id).count()
        if user_bookings > 0:
            flash(
                f"Нельзя удалить пользователя {user.email}, так как у него есть бронирования", "danger")
            return redirect(url_for("admin.users_list"))

        email = user.email
        db.session.delete(user)
        db.session.commit()

        flash(f"Пользователь {email} успешно удален", "success")

    except ValidationError:
        flash("Ошибка безопасности. Попробуйте еще раз.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при удалении пользователя: {str(e)}", "danger")

    return redirect(url_for("admin.users_list"))


@admin.route("/hotels")
@login_required
@admin_required
def hotels_list():
    """
    Список отелей.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 15
    search_query = request.args.get('search', '').strip()
    city_filter = request.args.get('city', '').strip()

    query = Hotel.query

    if search_query:
        query = query.filter(
            (Hotel.name.ilike(f'%{search_query}%')) |
            (Hotel.description.ilike(f'%{search_query}%'))
        )

    if city_filter:
        query = query.filter(Hotel.city.ilike(f'%{city_filter}%'))

    hotels = query.order_by(Hotel.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Получаем уникальные города для фильтра
    cities = db.session.query(Hotel.city).distinct().order_by(Hotel.city).all()
    city_list = [city[0] for city in cities if city[0]]

    return render_template("admin/hotels.html",
                           hotels=hotels,
                           search_query=search_query,
                           city_filter=city_filter,
                           cities=city_list)


@admin.route("/bookings")
@login_required
@admin_required
def bookings_list():
    """
    Список бронирований.
    """
    status = request.args.get("status", "all")
    page = request.args.get('page', 1, type=int)
    per_page = 30
    search_query = request.args.get('search', '').strip()

    query = Booking.query.join(User).join(Room).join(Hotel)

    if status and status != "all":
        query = query.filter(Booking.status == status)

    if search_query:
        query = query.filter(
            (User.email.ilike(f'%{search_query}%')) |
            (User.first_name.ilike(f'%{search_query}%')) |
            (User.last_name.ilike(f'%{search_query}%')) |
            (Hotel.name.ilike(f'%{search_query}%')) |
            (Room.name.ilike(f'%{search_query}%'))
        )

    bookings = query.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    statuses = ['all', 'pending', 'confirmed', 'cancelled']

    # Статистика по статусам для отображения
    status_counts = {
        'all': Booking.query.count(),
        'pending': Booking.query.filter_by(status='pending').count(),
        'confirmed': Booking.query.filter_by(status='confirmed').count(),
        'cancelled': Booking.query.filter_by(status='cancelled').count(),
    }

    return render_template(
        "admin/bookings.html",
        bookings=bookings,
        current_status=status,
        statuses=statuses,
        status_counts=status_counts,
        search_query=search_query
    )


@admin.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
@admin_required
def cancel_booking_admin(booking_id: int):
    """
    Отмена бронирования администратором.
    """
    try:
        validate_csrf(request.form.get('csrf_token'))

        booking = Booking.query.get_or_404(booking_id)

        if booking.status == "cancelled":
            flash("Бронирование уже отменено", "info")
        else:
            old_status = booking.status
            booking.status = "cancelled"
            db.session.commit()
            flash(
                f"Бронирование #{booking_id} отменено (было: {old_status})", "success")

    except ValidationError:
        flash("Ошибка безопасности. Попробуйте еще раз.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при отмене бронирования: {str(e)}", "danger")

    status = request.args.get("status", "all")
    return redirect(url_for("admin.bookings_list", status=status))


@admin.route("/bookings/<int:booking_id>/confirm", methods=["POST"])
@login_required
@admin_required
def confirm_booking_admin(booking_id: int):
    """
    Подтверждение бронирования администратором.
    """
    try:
        validate_csrf(request.form.get('csrf_token'))

        booking = Booking.query.get_or_404(booking_id)

        if booking.status == "confirmed":
            flash("Бронирование уже подтверждено", "info")
        elif booking.status == "cancelled":
            flash("Невозможно подтвердить отмененное бронирование", "danger")
        else:
            old_status = booking.status
            booking.status = "confirmed"
            db.session.commit()
            flash(
                f"Бронирование #{booking_id} подтверждено (было: {old_status})", "success")

    except ValidationError:
        flash("Ошибка безопасности. Попробуйте еще раз.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при подтверждении бронирования: {str(e)}", "danger")

    status = request.args.get("status", "all")
    return redirect(url_for("admin.bookings_list", status=status))
