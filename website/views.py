from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from website.models import get_products, get_product_by_id, get_cart, get_user_info
# create_order, add_order_detail

views = Blueprint('views', __name__)

@views.route('/')
def home():
    products = get_products()
    return render_template('home.html', products=products)

@views.route('/product/<int:product_id>')
def product_detail(product_id):
    print(f"Fetching product with ID: {product_id}")  # Debug
    product = get_product_by_id(product_id)
    print(f"Product data: {product}")  # Debug
    if not product:
        return redirect(url_for('views.home'))
    return render_template('product.html', product=product)


@views.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem giỏ hàng', 'error')
        return redirect(url_for('auth.login'))
    cart_items = get_cart(session['user_id'])
    return render_template('cart.html', cart_items=cart_items)


@views.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để thêm sản phẩm vào giỏ hàng', 'error')
        return redirect(url_for('auth.login'))

    product = get_product_by_id(product_id)
    if not product:
        flash('Sản phẩm không tồn tại', 'error')
        return redirect(url_for('views.home'))

    # Get form data
    choice = request.form.get('choice')
    quantity = int(request.form.get('quantity', 1))

    # Find the selected variant
    selected_variant = next((v for v in product['variants'] if v['choice'] == choice), None)
    if not selected_variant:
        flash('Biến thể sản phẩm không hợp lệ', 'error')
        return redirect(url_for('views.product_detail', product_id=product_id))

    # Check stock
    if quantity > selected_variant['stock']:
        flash('Số lượng vượt quá hàng tồn kho', 'error')
        return redirect(url_for('views.product_detail', product_id=product_id))

    # Add to cart
    success = add_to_cart(session['user_id'], product_id, choice, quantity)
    if success:
        flash('Đã thêm sản phẩm vào giỏ hàng', 'success')
    else:
        flash('Không thể thêm sản phẩm vào giỏ hàng', 'error')

    return redirect(url_for('views.product_detail', product_id=product_id))



# Thêm route cho thông tin cá nhân
@views.route('/info_user')
def info_user():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem thông tin cá nhân', 'error')
        return redirect(url_for('auth.login'))

    user_info = get_user_info(session['user_id'])
    return render_template('info_user.html')



@views.route('/shop_manager')
def shop_manager():
    # if 'user_id' not in session:
    #     flash('Vui lòng đăng nhập để quản lý cửa hàng', 'error')
    #     return redirect(url_for('auth.login'))
    # Logic quản lý cửa hàng sẽ được thêm sau
    return render_template('shop_manager.html')