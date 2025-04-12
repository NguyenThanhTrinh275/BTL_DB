from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from website.models import get_products
# , get_product_by_id, create_order, add_order_detail

views = Blueprint('views', __name__)

@views.route('/')
def home():
    products = get_products()
    return render_template('home.html', products=products)

# @views.route('/product/<int:product_id>')
# def product_detail(product_id):
#     product = get_product_by_id(product_id)
#     if not product:
#         flash('Product not found', 'error')
#         return redirect(url_for('views.home'))
#     return render_template('product.html', product=product)

# @views.route('/cart/add/<int:product_id>', methods=['POST'])
# def add_to_cart(product_id):
#     if 'user_id' not in session:
#         flash('Please login to add items to cart', 'error')
#         return redirect(url_for('auth.login'))
    
#     product = get_product_by_id(product_id)
#     if not product:
#         flash('Product not found', 'error')
#         return redirect(url_for('views.home'))
    
#     quantity = int(request.form.get('quantity', 1))
#     if quantity > product['stock']:
#         flash('Not enough stock', 'error')
#         return redirect(url_for('views.product_detail', product_id=product_id))
    
#     # Tạo đơn hàng nếu chưa có
#     order_id = create_order(session['user_id'])
#     if not order_id:
#         flash('Failed to create order', 'error')
#         return redirect(url_for('views.product_detail', product_id=product_id))
    
#     # Thêm chi tiết đơn hàng
#     success = add_order_detail(order_id, product_id, quantity, product['price'])
#     if success:
#         flash('Item added to cart', 'success')
#     else:
#         flash('Failed to add item to cart', 'error')
    
#     return redirect(url_for('views.product_detail', product_id=product_id))

# Thêm route cho giỏ hàng
@views.route('/cart')
def cart():
    # if 'user_id' not in session:
    #     flash('Vui lòng đăng nhập để xem giỏ hàng', 'error')
    #     return redirect(url_for('auth.login'))
    # Logic hiển thị giỏ hàng sẽ được thêm sau
    return render_template('cart.html')

# Thêm route cho quản lý cửa hàng
@views.route('/shop_manager')
def shop_manager():
    # if 'user_id' not in session:
    #     flash('Vui lòng đăng nhập để quản lý cửa hàng', 'error')
    #     return redirect(url_for('auth.login'))
    # Logic quản lý cửa hàng sẽ được thêm sau
    return render_template('shop_manager.html')

# Thêm route cho thông tin cá nhân
@views.route('/info_user')
def info_user():
    # if 'user_id' not in session:
    #     flash('Vui lòng đăng nhập để xem thông tin cá nhân', 'error')
    #     return redirect(url_for('auth.login'))
    # Logic hiển thị thông tin cá nhân sẽ được thêm sau
    return render_template('info_user.html')