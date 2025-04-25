import psycopg2
from psycopg2.extras import RealDictCursor
from website.config import Config


# Hàm kết nối đến cơ sở dữ liệu PostgreSQL
def get_db_connection():
    try:
        conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
        conn.set_client_encoding('UTF8')
        print("Kết nối cơ sở dữ liệu thành công!")
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
def close_db_connection(conn, cursor=None):
    if cursor:
        cursor.close()
    if conn:
        conn.close()

# Hàm đăng kí và đăng nhập tài khoản người dùng
def check_email_exists(email):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT check_email_exists(%s)", (email,))
        exists = cur.fetchone()['check_email_exists']
        return exists
    finally:
        close_db_connection(conn, cur)
# Hàm đăng ký người dùng
def register_user(first_name, last_name, email, password, phone_number, date_of_birth):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        # Thêm người dùng vào bảng USER
        cur.execute(
            'CALL insert_user(%s, %s, %s, %s, %s, %s)',
            (password, first_name, last_name, email, date_of_birth, None)
        )
        cur.execute('SELECT currval(pg_get_serial_sequence(\'"USER"\', \'userid\')) AS user_id')
        user_id = cur.fetchone()['user_id']
        cur.execute('CALL insert_user_phone(%s, %s)', (user_id, phone_number))
        
        conn.commit()
        return user_id
    except Exception as e:
        print(f"Error registering user: {e}")
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)
# Hàm đăng nhập
def login_user(email, password):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM  login_user(%s, %s)", (email, password))
        user = cur.fetchone()
        return user
    finally:
        close_db_connection(conn, cur)


# Hàm lấy danh sách sản phẩm (đã có từ trước, giữ nguyên)
def get_products():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM get_products()')
        products = cur.fetchall()
        return [
            {
                'id': product['product_id'],
                'name': product['name'],
                'price': product['price'],
                'image': product['image']
            }
            for product in products
        ]
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

# Hàm lấy sản phẩm theo ID (đã có từ trước, giữ nguyên)
def get_product_by_id(product_id):
    # Kiểm tra đầu vào
    if not isinstance(product_id, int) or product_id <= 0:
        print("Error: Invalid product_id")
        return None

    conn = get_db_connection()
    if not conn:
        print("Error: Database connection failed")
        return None

    try:
        cur = conn.cursor()

        # Truy vấn sản phẩm và biến thể
        cur.execute('SELECT * FROM get_product_and_variants(%s)', (product_id,))
        variants = cur.fetchall()

        if not variants:
            return None

        # Truy vấn hình ảnh bằng UNION
        cur.execute('SELECT * FROM get_product_images(%s)', (product_id,))
        images = cur.fetchall()

        # Xử lý danh sách hình ảnh
        all_images = [image['image'] for image in images if image['image'] is not None]
        if not all_images:
            all_images = ['default.png']

        # Cấu trúc kết quả
        product = {
            'id': variants[0]['product_id'],
            'name': variants[0]['name'],
            'variants': [
                {
                    'choice': variant['choice'],
                    'price': variant['price'],
                    'stock': variant['stock']
                }
                for variant in variants
            ],
            'images': all_images
        }
        return product

    except Exception as e:
        print(f"Error fetching product by ID: {e}")
        return None

    finally:
        close_db_connection(conn, cur)

# Hàm thêm sản phẩm vào giỏ hàng
def add_to_cart_func(user_id, product_id, choice, quantity):
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()

        # Lấy CartID từ VENDEE_AND_CART
        cur.execute("""
            SELECT CartID FROM VENDEE_AND_CART WHERE UserID = %s
        """, (user_id,))
        cart = cur.fetchone()
        if not cart:
            return False
        cart_id = cart['cartid']

        color, size = choice.split(', ')
        cur.execute(
            'CALL insert_or_update_cart_product_variant(%s, %s, %s, %s, %s)',
            (product_id, color, size, cart_id, quantity)
        )
        conn.commit()
        return True

    except Exception as e:
        print(f"Error in add_to_cart: {e}")
        conn.rollback()
        return False

    finally:
        close_db_connection(conn, cur)

# Hàm lấy giỏ hàng của người dùng
def get_cart(user_id):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM get_cart_items(%s)', (user_id,))
        items = cur.fetchall()
        return [
            {
                'product_id': item['product_id'],
                'name': item['name'],
                'color': item['color'],
                'size': item['size'],
                'total_money': item['total_money'],
                'quantity': item['quantity'],
                'image': item['image'],
                'cart_id': item['cart_id'],
                'price': item['price']
            }
            for item in items
        ]
    except Exception as e:
        print(f"Error fetching cart: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

# Hàm xóa sản phẩm khỏi giỏ hàng
def delete_from_cart_func(cart_id, product_id, color, size):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            'CALL delete_cart_product_variant(%s, %s, %s, %s)',
            (cart_id, product_id, color, size)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting from cart: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# Hàm lấy thông tin người dùng
def get_user_info(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM get_user_by_id(%s)', (user_id,))
        user_info = cur.fetchone()
        cur.execute('SELECT * FROM get_user_phones(%s)', (user_id,))
        phones = cur.fetchall()
        return {
            'first_name': user_info['firstname'],
            'last_name': user_info['lastname'],
            'email': user_info['email'],
            'phone_number': phones[0]['phone_number'] if phones else None,
            'date_of_birth': user_info['dateofbirth'],
            'total_spending': user_info['totalspending']
        }
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm lấy danh sách địa chỉ của người dùng
def get_user_addresses(user_id):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM get_user_addresses(%s)', (user_id,))
        addresses = cur.fetchall()
        return [
            {
                'home_number': address['homenumber'],
                'street': address['street'],
                'district': address['district'],
                'city': address['city'],
                'province': address['province'],
                'is_default': address['isdefault']
            }
            for address in addresses
        ]
    except Exception as e:
        print(f"Error fetching addresses: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

# Hàm thêm địa chỉ mới
def add_user_address(user_id, home_number, street, district, city, province, is_default=False):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            'CALL add_user_address(%s, %s, %s, %s, %s, %s, %s)',
            (user_id, home_number, street, district, city, province, is_default)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding address: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# Hàm xóa địa chỉ
def delete_user_address(user_id, home_number, street, district, city, province):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            'CALL delete_user_address(%s, %s, %s, %s, %s, %s)',
            (user_id, home_number, street, district, city, province)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting address: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# Hàm sửa địa chỉ
def update_user_address(user_id, old_home_number, old_street, old_district, old_city, old_province, new_home_number, new_street, new_district, new_city, new_province):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            'CALL update_user_address(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (user_id, old_home_number, old_street, old_district, old_city, old_province,
             new_home_number, new_street, new_district, new_city, new_province)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating address: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# Hàm thiết lập địa chỉ mặc định
def set_default_address(user_id, home_number, street, district, city, province):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            'CALL set_default_address(%s, %s, %s, %s, %s, %s)',
            (user_id, home_number, street, district, city, province)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error setting default address: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# Hàm tạo order
def create_order(user_id, cart_id, payment_method, total_money, total_products, home_number, street, district, city, province):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            'CALL insert_order(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
            (payment_method, total_money, total_products, home_number, street, district, city, province, cart_id, None)
        )
        cur.execute('SELECT currval(pg_get_serial_sequence(\'"ORDER"\', \'orderid\')) AS orderid')
        order_id = cur.fetchone()['orderid']
        conn.commit()
        return order_id
    except Exception as e:
        print(f"Error creating order: {e}")
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm thêm chi tiết đơn hàng
def add_order_detail(order_id, product_id, color, size, quantity):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            'CALL insert_order_product_variant(%s, %s, %s, %s, %s)',
            (product_id, color, size, order_id, quantity)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding order detail: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# Hàm lấy danh sách shop có sản phẩm
def get_shops_with_products():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM get_shops_with_products()')
        shops = cur.fetchall()
        return [
            {
                'shopid': shop['shopid'],
                'name': shop['name']
            }
            for shop in shops
        ]
    except Exception as e:
        print(f"Error fetching shops: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

# Hàm lọc sản phẩm theo loại và shop
def get_filtered_products(product_types=None, shop_ids=None):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            'SELECT * FROM get_filtered_products(%s, %s)',
            (product_types if product_types else None, shop_ids if shop_ids else None)
        )
        products = cur.fetchall()
        return [
            {
                'id': product['product_id'],
                'name': product['name'],
                'price': product['price'],
                'image': product['image']
            }
            for product in products
        ]
    except Exception as e:
        print(f"Error fetching filtered products: {e}")
        return []
    finally:
        close_db_connection(conn, cur)











# Hàm lấy hình ảnh đăng ký của sản phẩm
def get_product_image(product_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT get_product_image(%s)", (product_id,))
        image = cur.fetchone()
        return image
    except Exception as e:
        print(f"Error fetching product image: {e}")
        return 'default_image.jpg'
    finally:
        close_db_connection(conn, cur)

# Hàm lấy BIẾN THỂ của sản phẩm
def get_variants_by_product_id(product_id):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM get_variants_by_product_id(%s)", (product_id,))
        variants = cur.fetchall()
        return [
            {
                'image': variant['image'],
                'color': variant['color'],
                'size': variant['size'],
                'price': variant['price'],
                'quantity': variant['quantity']
            }
            for variant in variants
        ]
    except Exception as e:
        print(f"Error fetching variants: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

# Hàm lấy sản phẩm theo UserID
def get_products_by_userid(user_id):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        # Gọi stored procedure để lấy sản phẩm và biến thể
        cur.execute("SELECT * FROM get_products_by_userid(%s)", (user_id,))
        products = cur.fetchall()

        result = []
        for product in products:
            variants = product['variants']
            product_dict = {
                'productid': product['productid'],
                'name': product['name'],
                'image': product['image'] if product['image'] else 'default.png',
                'variants': [
                    {
                        'color': variant['color'],
                        'size': variant['size'],
                        'price': float(variant['price']),
                        'quantity': variant['quantity']
                    }
                    for variant in variants
                ]
            }
            result.append(product_dict)

        return result
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

# Hàm truy xuất shop theo UserID 
def get_shop_by_user_id(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        # Gọi stored procedure để lấy thông tin cửa hàng
        cur.execute("SELECT * FROM get_shop_by_user_id(%s)", (user_id,))
        shop = cur.fetchone()

        if shop:
            return shop
        return None
    except Exception as e:
        print(f"Error fetching shop: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

# Đăng ký shop cho UserID chưa có shop
def reg_shop_func(user_id, name, address, income, tax_number, phone_num):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        # Gọi stored procedure để đăng ký cửa hàng và nhận shop_id
        cur.execute("SELECT * FROM reg_shop_func(%s, %s, %s, %s, %s, %s) as shop_id", (user_id, name, address, income, tax_number, phone_num))
        shop_id = cur.fetchone()['shop_id']  

        conn.commit()
        return shop_id
    except Exception as e:
        print(f"Gặp lỗi khi đăng ký {e}")
        return None
    finally:
        close_db_connection(conn, cur)


# Hàm truy xuất shop_id từ Vender
def get_shop_id_by_user_id(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT get_shop_id_by_user_id(%s) as shopid", (user_id,))

        shop = cur.fetchone()
        if shop:
            return shop['shopid']
        return None
    except Exception as e:
        print(f"Error fetching shop_id: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm đăng ký sản phẩm
def create_product(shop_id, type, description, pic_text, color, size, price, stock_quantity):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()

        cur.execute("CALL create_product(%s, %s, %s, %s, %s, %s, %s, %s)", (shop_id, type, description, pic_text, color, size, price, stock_quantity))

        conn.commit()
        return True  
    except Exception as e:
        print(f"Error registering product: {e}")
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm update BIẾN THỂ cho sản phẩm
def update_product_func(product_id, new_color, new_size, new_price, new_stock_quantity, new_pic):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()

        cur.execute('CALL update_product_func(%s, %s, %s, %s, %s, %s)', (product_id, new_color, new_size, new_price, new_stock_quantity, new_pic))

        conn.commit()
        print(f'Cập nhật BIẾN THỂ thành công!', 'success')
        return product_id
    except Exception as e:
        print(f'Cập nhật thất bại: {e}', 'error')
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm CHỈNH SỬA sản phẩm
def modify_product_func(product_id, color, size, modified_quantity, modified_price):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()

        cur.execute("CALL modify_product_func(%s, %s, %s, %s, %s)", (product_id, color, size, modified_quantity, modified_price))

        conn.commit()
        return product_id
    except Exception as e:
        print(f"Error modifying product: {e}")
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm xoá BIẾN THỂ của sản phẩm
def delete_variant_func(product_id, color, size):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()

        # Xóa biến thể khỏi bảng PRODUCT_VARIANT
        cur.execute("CALL delete_variant_func(%s, %s, %s)", (product_id, color, size))

        conn.commit()

    except Exception as e:
        print(f"Error deleting product variant: {e}")
        conn.rollback()
        raise e
    finally:
        close_db_connection(conn, cur)


# Hàm HIỂN THỊ doanh thu
def get_seller_income(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(' SELECT get_seller_income(%s) AS income', (user_id,))
        conn.commit()

        # column_names = [desc[0] for desc in cur.description]
        # print(f"Column names: {column_names}")

        ans = cur.fetchone()
        return ans['income'] if ans else 0
    except Exception as e:
        print(f"Lỗi khi truy xuất doanh thu cho:", {e})        
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)
    
    