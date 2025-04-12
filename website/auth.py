from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from website.models import check_email_exists, register_user, login_user
from datetime import datetime

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']  # HTML form dùng name="username" cho email
        password = request.form['password']
        
        user = login_user(email, password)
        if user:
            session['user_id'] = user['userid']
            session['user_name'] = f"{user['firstname']} {user['lastname']}"
            return redirect(url_for('views.home'))  # Chuyển hướng đến trang chủ
        else:
            flash('Email hoặc mật khẩu không đúng', 'error')
    
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        date_of_birth = request.form['date_of_birth']
        
        if password != confirm_password:
            flash('Mật khẩu và xác nhận mật khẩu không khớp', 'error')
            return redirect(url_for('auth.register'))
        
        if check_email_exists(email):
            flash('Email đã được đăng ký', 'error')
            return redirect(url_for('auth.register'))
        
        # Kiểm tra số điện thoại (10 chữ số)
        if not (len(phone) == 10 and phone.isdigit()):
            flash('Số điện thoại phải có đúng 10 chữ số', 'error')
            return redirect(url_for('auth.register'))
        
        # Kiểm tra ngày sinh hợp lệ (không được là ngày trong tương lai)
        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            today = datetime.today().date()
            if dob > today:  # Ngày sinh không được là ngày trong tương lai
                flash('Ngày sinh không được là ngày trong tương lai', 'error')
                return redirect(url_for('auth.register'))
        except ValueError:
            flash('Ngày sinh không hợp lệ', 'error')
            return redirect(url_for('auth.register'))
        
        # Đăng ký người dùng và đăng nhập tự động
        user_id = register_user(first_name, last_name, email, password, phone, date_of_birth)
        if user_id:
            # Đăng nhập tự động sau khi đăng ký thành công
            user = login_user(email, password)
            if user:
                session['user_id'] = user['userid']
                session['user_name'] = f"{user['firstname']} {user['lastname']}"
                flash('Đăng ký và đăng nhập thành công!', 'success')
                return redirect(url_for('views.home'))  # Chuyển hướng đến trang chủ
            else:
                flash('Đăng ký thành công nhưng đăng nhập thất bại. Vui lòng đăng nhập lại.', 'error')
                return redirect(url_for('auth.login'))
        else:
            flash('Đăng ký thất bại. Vui lòng thử lại.', 'error')
    
    return render_template('register.html')

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('Đăng xuất thành công', 'success')
    return redirect(url_for('views.home'))