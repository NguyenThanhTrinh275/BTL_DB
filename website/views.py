from flask import render_template
from website import app

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('sign_up.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/info_user')
def info_user():
    return render_template('info_user.html')

@app.route('/shop_manager')
def shop_manager():
    return render_template('shop_manager.html')


@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/product')
def product():
    return render_template('product.html')

