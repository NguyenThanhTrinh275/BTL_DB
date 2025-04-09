from flask import Blueprint, render_template, request, redirect, url_for
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__)

@bp.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')  # Định dạng: YYYY-MM-DD

        # Kiểm tra xem email đã tồn tại chưa
        user = User.query.filter_by(Email=email).first()
        if user:
            return render_template('sign_up.html', error='Email already exists')

        # Tạo user mới
        new_user = User(
            Email=email,
            Password=generate_password_hash(password, method='sha256'),
            FirstName=first_name,
            LastName=last_name,
            DateOfBirth=date_of_birth
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template('sign_up.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(Email=email).first()
        if user and check_password_hash(user.Password, password):
            return redirect(url_for('views.home'))
        return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')