from flask import Blueprint, render_template
from .models import Product, ProductVariant

bp = Blueprint('views', __name__)

@bp.route('/')
def home():
    products = Product.query.all()  # Lấy tất cả sản phẩm từ bảng PRODUCT
    return render_template('home.html', products=products)

@bp.route('/product/<int:product_id>')
def product(product_id):
    product = Product.query.get_or_404(product_id)  # Lấy sản phẩm theo ProductID
    variants = ProductVariant.query.filter_by(ProductID=product_id).all()  # Lấy các biến thể
    return render_template('product.html', product=product, variants=variants)

# @app.route('/cart')
# def cart():
#     return render_template('cart.html')

# @app.route('/info_user')
# def info_user():
#     return render_template('info_user.html')

# @app.route('/shop_manager')
# def shop_manager():
#     return render_template('shop_manager.html')

# @app.route('/payment')
# def payment():
#     return render_template('payment.html')

# @app.route('/product')
# def product():
#     return render_template('product.html')

