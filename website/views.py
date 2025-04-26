from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from .models import *
from decimal import Decimal

views = Blueprint('views', __name__)

# Thêm route cho việc truy cập trang chủ
@views.route('/', methods=['GET', 'POST'])
def home():
    product_types = ['Áo', 'Quần', 'Phụ kiện khác']
    type_mapping = {
        'Áo': 'ao',
        'Quần': 'quan',
        'Phụ kiện khác': 'pk'
    }
    shops = get_shops_with_products()
    products = get_products()

    if request.method == 'POST':
        selected_types = request.form.getlist('product_types') 
        selected_shops = request.form.getlist('shop_ids') 
        sort_order = request.form.get('sort_order')
        selected_shops = [int(shop_id) for shop_id in selected_shops if shop_id.isdigit()]
        db_selected_types = [type_mapping[ptype] for ptype in selected_types if ptype in type_mapping]

        if db_selected_types or selected_shops:
            products = get_filtered_products(
                product_types=db_selected_types if db_selected_types else None,
                shop_ids=selected_shops if selected_shops else None
            )
        
        if sort_order == 'asc':
            products = sorted(products, key=lambda x: x['price'])
        elif sort_order == 'desc':
            products = sorted(products, key=lambda x: x['price'], reverse=True)

    return render_template(
        'home.html',
        products=products,
        shops=shops,
        product_types=product_types
    )

# Thêm route cho thông tin cá nhân
@views.route('/info_user')
def info_user():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem thông tin cá nhân', 'error')
        return redirect(url_for('auth.login'))

    user_info = get_user_info(session['user_id'])
    addresses = get_user_addresses(session['user_id'])
    return render_template('info_user.html', user_info=user_info, addresses=addresses)

# Thêm route cho việc thêm địa chỉ
@views.route('/info_user/add_address', methods=['POST'])
def add_address():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để thêm địa chỉ', 'error')
        return redirect(url_for('auth.login'))

    home_number = request.form.get('home_number')
    street = request.form.get('street')
    district = request.form.get('district')
    city = request.form.get('city')
    province = request.form.get('province')
    is_default = request.form.get('is_default') == 'on'

    if not all([home_number, street, district, city, province]):
        flash('Vui lòng điền đầy đủ thông tin địa chỉ', 'error')
        return redirect(url_for('views.info_user'))

    success = add_user_address(session['user_id'], home_number, street, district, city, province, is_default)
    if success:
        flash('Thêm địa chỉ thành công', 'success')
    else:
        flash('Thêm địa chỉ thất bại', 'error')
    return redirect(url_for('views.info_user'))

# Thêm route cho việc xóa địa chỉ
@views.route('/info_user/delete_address', methods=['POST'])
def delete_address():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xóa địa chỉ', 'error')
        return redirect(url_for('auth.login'))

    home_number = request.form.get('home_number')
    street = request.form.get('street')
    district = request.form.get('district')
    city = request.form.get('city')
    province = request.form.get('province')

    success = delete_user_address(session['user_id'], home_number, street, district, city, province)
    if success:
        flash('Xóa địa chỉ thành công', 'success')
    else:
        flash('Xóa địa chỉ thất bại', 'error')
    return redirect(url_for('views.info_user'))

# Thêm route cho việc sửa địa chỉ
@views.route('/info_user/update_address', methods=['POST'])
def update_address():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để sửa địa chỉ', 'error')
        return redirect(url_for('auth.login'))

    old_home_number = request.form.get('old_home_number')
    old_street = request.form.get('old_street')
    old_district = request.form.get('old_district')
    old_city = request.form.get('old_city')
    old_province = request.form.get('old_province')

    new_home_number = request.form.get('home_number')
    new_street = request.form.get('street')
    new_district = request.form.get('district')
    new_city = request.form.get('city')
    new_province = request.form.get('province')

    if not all([old_home_number, old_street, old_district, old_city, old_province, new_home_number, new_street, new_district, new_city, new_province]):
        flash('Vui lòng điền đầy đủ thông tin địa chỉ', 'error')
        return redirect(url_for('views.info_user'))

    success = update_user_address(session['user_id'], old_home_number, old_street, old_district, old_city, old_province, new_home_number, new_street, new_district, new_city, new_province)
    if success:
        flash('Sửa địa chỉ thành công', 'success')
    else:
        flash('Sửa địa chỉ thất bại', 'error')
    return redirect(url_for('views.info_user'))

# Thêm route cho việc thiết lập địa chỉ mặc định
@views.route('/info_user/set_default_address', methods=['POST'])
def set_default():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để thiết lập địa chỉ mặc định', 'error')
        return redirect(url_for('auth.login'))

    home_number = request.form.get('home_number')
    street = request.form.get('street')
    district = request.form.get('district')
    city = request.form.get('city')
    province = request.form.get('province')

    success = set_default_address(session['user_id'], home_number, street, district, city, province)
    if success:
        flash('Thiết lập địa chỉ mặc định thành công', 'success')
    else:
        flash('Thiết lập địa chỉ mặc định thất bại', 'error')
    return redirect(url_for('views.info_user'))

# Thêm route cho việc truy cập trang sản phẩm
@views.route('/product/<int:product_id>')
def product_detail(product_id):
    print(f"Fetching product with ID: {product_id}")  # Debug
    product = get_product_by_id(product_id)
    print(f"Product data: {product}")  # Debug
    if not product:
        return redirect(url_for('views.home'))
    return render_template('product.html', product=product)

# Thêm route cho việc truy cập giỏ hàng
@views.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem giỏ hàng', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST' and request.form.get('action') == 'place_order':
        cart_items = get_cart(session['user_id'])
        if not cart_items:
            flash('Giỏ hàng trống, không thể đặt hàng', 'error')
            return redirect(url_for('views.cart'))
        return redirect(url_for('views.payment'))
    
    cart_items = get_cart(session['user_id'])
    total_money = sum(Decimal(str(item['total_money'])) for item in cart_items)
    total_products = sum(item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_money=total_money, total_products=total_products)

# Thêm route cho việc thêm sản phẩm vào giỏ hàng
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
    success = add_to_cart_func(session['user_id'], product_id, choice, quantity)
    if success:
        flash('Đã thêm sản phẩm vào giỏ hàng', 'success')
    else:
        flash('Không thể thêm sản phẩm vào giỏ hàng', 'error')

    return redirect(url_for('views.product_detail', product_id=product_id))

# Thêm route cho việc xoá sản phẩm khỏi giỏ hàng
@views.route('/cart/delete', methods=['POST'])
def delete_from_cart():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xóa sản phẩm khỏi giỏ hàng', 'error')
        return redirect(url_for('auth.login'))

    product_id = int(request.form.get('product_id'))
    color = request.form.get('color')
    size = request.form.get('size')
    cart_id = int(request.form.get('cart_id'))

    success = delete_from_cart_func(cart_id, product_id, color, size)
    if success:
        flash('Đã xóa sản phẩm khỏi giỏ hàng', 'success')
    else:
        flash('Không thể xóa sản phẩm khỏi giỏ hàng', 'error')

    return redirect(url_for('views.cart'))

# Thêm route cho việc thanh toán
@views.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để thanh toán', 'error')
        return redirect(url_for('auth.login'))
    
    user_info = get_user_info(session['user_id'])
    if not user_info:
        flash('Không thể lấy thông tin người dùng', 'error')
        return redirect(url_for('views.cart'))
    
    # Lấy địa chỉ mặc định
    addresses = get_user_addresses(session['user_id'])
    default_address = next((addr for addr in addresses if addr['is_default']), None)
    
    # Lấy giỏ hàng
    cart_items = get_cart(session['user_id'])
    if not cart_items:
        flash('Giỏ hàng trống, không thể thanh toán', 'error')
        return redirect(url_for('views.cart'))
    
    total_money = sum(Decimal(str(item['total_money'])) for item in cart_items)
    total_products = sum(item['quantity'] for item in cart_items)
    
    if request.method == 'POST':
        payment_method = request.form.get('payment')
        if not payment_method:
            flash('Vui lòng chọn phương thức thanh toán', 'error')
            return redirect(url_for('views.payment'))
        
        if not default_address:
            flash('Vui lòng chọn địa chỉ giao hàng mặc định', 'error')
            return redirect(url_for('views.payment'))

        order_id = create_order(
            user_id=session['user_id'],
            cart_id=cart_items[0]['cart_id'],
            payment_method=payment_method,
            total_money=total_money,
            total_products=total_products,
            home_number=default_address['home_number'],
            street=default_address['street'],
            district=default_address['district'],
            city=default_address['city'],
            province=default_address['province']
        )
        
        if order_id:
            success = True
            for item in cart_items:
                success = True
                success = success and add_order_detail(
                    order_id=order_id,
                    product_id=item['product_id'],
                    color=item['color'],
                    size=item['size'],
                    quantity=item['quantity']
                )
                if not success:
                    flash('Lỗi khi thêm chi tiết đơn hàng', 'error')
                    return redirect(url_for('views.payment'))
                
                success = success and delete_from_cart_func(
                    cart_id=item['cart_id'],
                    product_id=item['product_id'],
                    color=item['color'],
                    size=item['size']
                )
                if not success:
                    print('Lỗi khi xóa sản phẩm khỏi giỏ hàng')
                    return redirect(url_for('views.payment'))
            
            flash('Đặt hàng thành công!', 'success')
            return redirect(url_for('views.home'))
        else:
            flash('Lỗi khi tạo đơn hàng', 'error')
    
    return render_template(
        'payment.html',
        user_info=user_info,
        default_address=default_address,
        cart_items=cart_items,
        total_money=total_money,
        total_products=total_products
    )






# Kiểm tra tồn tại của shop và đăng kí shop
@views.route('/shop_manager', methods=['GET', 'POST'])
def shop_manager():
    user_id = session.get('user_id')
    if not user_id:
        flash('Vui lòng đăng nhập để quản lý cửa hàng', 'error')
        return redirect(url_for('auth.login'))

    shop = get_shop_by_user_id(user_id)

    if shop:
        products = get_products_by_userid(user_id)
        for product in products:
            product['variants'] = get_variants_by_product_id(product['productid'])
            product['image'] = get_product_image(product['productid'])

        income = get_seller_income(user_id)
        return render_template('shop_manager.html', shop=shop,  products=products, income=income)
    return render_template('shop_manager.html', shop=None)

# Đăng ký cửa hàng
@views.route('/reg_shop', methods=['GET', 'POST'])
def reg_shop():
    user_id = session.get('user_id')

    if request.method == 'POST':
        name = request.form['name']
        tax_number = request.form['tax_number']
        address = request.form['address']
        phone_num = request.form['phone_number']
        income = 0

        shop_id = reg_shop_func(user_id, name, address, income, tax_number, phone_num)
        if shop_id:
            flash('Đăng ký cửa hàng thành công', 'success')
            return redirect(url_for('views.shop_manager'))
        else:
            flash('Đăng ký cửa hàng thất bại', 'error')

    return render_template('reg_shop.html')


# Đăng ký sản phẩm
@views.route('/reg_products', methods=['GET', 'POST'])
def reg_products():    
    if request.method == 'POST':
        user_id = session.get('user_id')

        product_img = request.form['product_image']
        description = request.form['product_name']
        type = request.form['category']
        variant_pic_text = request.form['variant_image[]']
        colors = request.form['variant_color[]']
        size = request.form['variant_size[]']
        price = request.form['variant_price[]']
        stock_quantity = request.form['variant_quantity[]']

        shop_id = get_shop_id_by_user_id(user_id)
        if not product_img or not description or not type or not variant_pic_text or not colors or not size or not price or not stock_quantity:
            return render_template('reg_products.html') 

        product_id = create_product(shop_id, product_img, type, description, variant_pic_text, colors, size, price, stock_quantity)
        if product_id:
            flash('Sản phẩm đăng ký thành công', 'success')
            return redirect(url_for('views.shop_manager'))  
        else:
            flash('Đăng ký sản phẩm thất bại', 'error')

    return render_template('reg_products.html')

# Cập nhật BIẾN THỂ sản phẩm
@views.route('/update_product/<int:product_id>', methods=['GET', 'POST'])
def update_product_route(product_id):
    product = get_product_by_id(product_id)
    if request.method == 'POST':
        new_pic = request.form.get('variant_image[]')
        new_color = request.form.get('variant_color[]')
        new_size = request.form.get('variant_size[]')
        new_price = request.form.get('variant_price[]', type=int)
        new_stock_quantity = request.form.get('variant_quantity[]', type=int)
        
        if not new_price or not new_color or not new_size or not new_stock_quantity:
            return render_template('update_product.html', product=product)
        
        new_variant = update_product_func(product_id, new_color, new_size, new_price, new_stock_quantity, new_pic)
        if new_variant:
            print(f'Thêm BIẾN THỂ thành công', 'success')
            return redirect(url_for('views.shop_manager'))  
        else:
            print(f'Đăng ký sản phẩm thất bại', 'error')

    return render_template('update_product.html', product=product)

# Hàm CHỈNH SỬA sản phẩm
@views.route('modify/<int:product_id>', methods=['GET', 'POST'])
def modify_product_route(product_id):
    product = get_product_by_id(product_id)
    variants = get_variants_by_product_id(product_id)
    if request.method == 'POST':
        for variant in variants:

            modified_quantity = request.form.get(f"stock_quantity_{variant['color']}_{variant['size']}", variant['quantity'])
            modified_price = request.form.get(f"price_{variant['color']}_{variant['size']}", variant['price'])

            if int(modified_quantity) < 0 or float(modified_price) < 0:
                flash("Không thể là giá trị âm", 'error')
                return redirect(url_for('views.modify_product_route', product_id=product_id))

            modify_product_func(product_id, variant['color'], variant['size'], modified_quantity, modified_price)
        
        return redirect(url_for('views.shop_manager'))
    return render_template('modify.html', product=product, variants=variants)

# Hàm xoá BIẾN THỂ sản phẩm 
@views.route('/delete_product/<int:product_id>', methods=['GET', 'POST'])
def delete_product_route(product_id):
    product = get_product_by_id(product_id)
    variants = get_variants_by_product_id(product_id)

    if request.method == 'POST':
        selected_variants = request.form.getlist('delete_variant') 

        if selected_variants:
            for variant in selected_variants:
                color, size = variant.split('|')
                delete_variant_func(product_id, color, size)

        return redirect(url_for('views.shop_manager'))
    return render_template('delete.html', product=product, variants=variants)
