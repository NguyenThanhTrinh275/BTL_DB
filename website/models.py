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
        cur.execute("SELECT 1 FROM \"USER\" WHERE Email = %s", (email,))
        exists = cur.fetchone() is not None
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
            """
            INSERT INTO "USER" (FirstName, LastName, Email, "Password", DateOfBirth)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING UserID
            """,
            (first_name, last_name, email, password, date_of_birth)
        )
        user_id = cur.fetchone()['userid']
        
        # Thêm số điện thoại vào bảng USER_PHONE
        cur.execute(
            """
            INSERT INTO USER_PHONE (UserID, PhoneNumber)
            VALUES (%s, %s)
            """,
            (user_id, phone_number)
        )
        
        # Thêm người dùng vào bảng NonAdmin
        cur.execute(
            """
            INSERT INTO NonAdmin (UserID)
            VALUES (%s)
            """,
            (user_id,)
        )
        
        # Tạo CartID và thêm vào bảng VENDEE_AND_CART
        cur.execute(
            """
            INSERT INTO VENDEE_AND_CART (UserID, TotalSpending, CartID)
            VALUES (%s, %s, %s)
            """,
            (user_id, 0.00, user_id)  # CartID tạm thời dùng UserID
        )
        
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
        cur.execute(
            """
            SELECT UserID, FirstName, LastName, Email
            FROM "USER"
            WHERE Email = %s AND "Password" = %s
            """,
            (email, password)
        )
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
        cur.execute("""
            SELECT DISTINCT ON (p.ProductID)
                p.ProductID AS productid,
                p.Description AS name,
                (SELECT MIN(pv2.Price)
                 FROM PRODUCT_VARIANT pv2
                 WHERE pv2.ProductID = p.ProductID
                 AND pv2.StockQuantity > 0) AS price,
                (SELECT pi.Images 
                 FROM PRODUCT_IMAGES pi 
                 WHERE pi.ProductID = p.ProductID 
                 LIMIT 1) AS image
            FROM PRODUCT p
            LEFT JOIN PRODUCT_VARIANT pv ON p.ProductID = pv.ProductID
            WHERE EXISTS (
                SELECT 1
                FROM PRODUCT_VARIANT pv3
                WHERE pv3.ProductID = p.ProductID
                AND pv3.StockQuantity > 0
            )
            ORDER BY p.ProductID
        """)
        products = cur.fetchall()
        return [
            {
                'id': product['productid'],
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
        cur.execute("""
            SELECT 
                p.ProductID AS productid,
                p.Description AS name,
                pv.Color || ', ' || pv."Size" AS choice,
                pv.Price AS price,
                pv.StockQuantity AS stock
            FROM PRODUCT p
            LEFT JOIN PRODUCT_VARIANT pv ON p.ProductID = pv.ProductID
            WHERE p.ProductID = %s AND pv.StockQuantity > 0
            ORDER BY pv.Color, pv."Size"
        """, (product_id,))
        variants = cur.fetchall()

        if not variants:
            return None

        # Truy vấn hình ảnh bằng UNION
        cur.execute("""
            SELECT Images AS image FROM PRODUCT_IMAGES WHERE ProductID = %s
            UNION
            SELECT Image AS image FROM PRODUCT_VARIANT WHERE ProductID = %s
        """, (product_id, product_id))
        images = cur.fetchall()

        # Xử lý danh sách hình ảnh
        all_images = [image['image'] for image in images if image['image'] is not None]
        if not all_images:
            all_images = ['default.png']

        # Cấu trúc kết quả
        product = {
            'id': variants[0]['productid'],
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
        # Có thể ghi log lỗi thay vì chỉ in
        return None

    finally:
        close_db_connection(conn, cur)

# Hàm thêm sản phẩm vào giỏ hàng
def add_to_cart_func(user_id, product_id, choice, quantity, price):
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
        # Kiểm tra xem biến thể đã tồn tại trong giỏ hàng chưa
        cur.execute("""
            SELECT Quantity, TotalMoney
            FROM CART_CONTAIN_PRODUCT_VARIANT
            WHERE CartID = %s AND ProductID = %s AND Color = %s AND "Size" = %s
        """, (cart_id, product_id, color, size))
        existing_item = cur.fetchone()

        total_money = price * quantity
        if existing_item:
            # Cập nhật số lượng và tổng tiền
            new_quantity = existing_item['quantity'] + quantity
            new_total_money = price * new_quantity
            cur.execute("""
                UPDATE CART_CONTAIN_PRODUCT_VARIANT
                SET Quantity = %s, TotalMoney = %s
                WHERE CartID = %s AND ProductID = %s AND Color = %s AND "Size" = %s
            """, (new_quantity, new_total_money, cart_id, product_id, color, size))
        else:
            # Thêm mới vào giỏ hàng
            cur.execute("""
                INSERT INTO CART_CONTAIN_PRODUCT_VARIANT (CartID, ProductID, Color, "Size", Quantity, TotalMoney)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (cart_id, product_id, color, size, quantity, total_money))

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
        cur.execute("""
            SELECT 
                cc.CartID,
                cc.ProductID,
                pv.image,
                p.Description AS name,
                cc.Color,
                cc."Size" AS size,
                cc.Quantity,
                cc.TotalMoney,
                pv.Price AS price
            FROM CART_CONTAIN_PRODUCT_VARIANT cc
            JOIN PRODUCT p ON cc.ProductID = p.ProductID
            JOIN PRODUCT_VARIANT pv ON cc.ProductID = pv.ProductID AND cc.Color = pv.Color AND cc."Size" = pv."Size"
            JOIN VENDEE_AND_CART vc ON cc.CartID = vc.CartID
            WHERE vc.UserID = %s
        """, (user_id,))
        items = cur.fetchall()
        return [
            {
                'product_id': item['productid'],
                'name': item['name'],
                'color': item['color'],
                'size': item['size'],
                'total_money': item['totalmoney'],
                'quantity': item['quantity'],
                'image': item['image'],
                'cart_id': item['cartid'],
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
        cur.execute("""
            DELETE FROM CART_CONTAIN_PRODUCT_VARIANT
            WHERE CartID = %s AND ProductID = %s AND Color = %s AND "Size" = %s
        """, (cart_id, product_id, color, size))
        conn.commit()
        return cur.rowcount > 0  
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
        cur.execute("""
            SELECT 
                u.FirstName,
                u.LastName,
                u.Email,
                up.PhoneNumber,
                u.DateOfBirth,
                vc.TotalSpending
            FROM "USER" u
            JOIN USER_PHONE up ON u.UserID = up.UserID
            JOIN VENDEE_AND_CART vc ON u.UserID = vc.UserID
            WHERE u.UserID = %s
        """, (user_id,))
        user_info = cur.fetchone()
        return {
            'first_name': user_info['firstname'],
            'last_name': user_info['lastname'],
            'email': user_info['email'],
            'phone_number': user_info['phonenumber'],
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
        cur.execute("""
            SELECT HomeNumber, Street, District, City, Province, IsDefault
            FROM VENDEE_ADDRESS
            WHERE UserID = %s
        """, (user_id,))
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
        # Nếu địa chỉ mới được đặt làm mặc định, bỏ mặc định của các địa chỉ khác
        if is_default:
            cur.execute("""
                UPDATE VENDEE_ADDRESS
                SET IsDefault = FALSE
                WHERE UserID = %s
            """, (user_id,))
        # Thêm địa chỉ mới
        cur.execute("""
            INSERT INTO VENDEE_ADDRESS (UserID, HomeNumber, Street, District, City, Province, IsDefault)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, home_number, street, district, city, province, is_default))
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
        cur.execute("""
            DELETE FROM VENDEE_ADDRESS
            WHERE UserID = %s AND HomeNumber = %s AND Street = %s AND District = %s AND City = %s AND Province = %s
        """, (user_id, home_number, street, district, city, province))
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
        cur.execute("""
            UPDATE VENDEE_ADDRESS
            SET HomeNumber = %s, Street = %s, District = %s, City = %s, Province = %s
            WHERE UserID = %s AND HomeNumber = %s AND Street = %s AND District = %s AND City = %s AND Province = %s
        """, (new_home_number, new_street, new_district, new_city, new_province, user_id, old_home_number, old_street, old_district, old_city, old_province))
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
        # Bỏ mặc định của tất cả địa chỉ khác
        cur.execute("""
            UPDATE VENDEE_ADDRESS
            SET IsDefault = FALSE
            WHERE UserID = %s
        """, (user_id,))
        # Đặt địa chỉ này làm mặc định
        cur.execute("""
            UPDATE VENDEE_ADDRESS
            SET IsDefault = TRUE
            WHERE UserID = %s AND HomeNumber = %s AND Street = %s AND District = %s AND City = %s AND Province = %s
        """, (user_id, home_number, street, district, city, province))
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
        total_price = total_money + 30000
        cur.execute(
            """
            INSERT INTO "ORDER" (
                PaymentMethod, TotalMoney, TotalProduct,
                HomeNumber, Street, District, City, Province, Subtotal, CartID, ShipByID, Status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING OrderID
            """,
            (
                payment_method,
                total_price,
                total_products,
                home_number,
                street,
                district,
                city,
                province,
                total_money,
                cart_id,
                11,
                'Pending'
            )
        )
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
def add_order_detail(order_id, product_id, color, size, quantity, total_money):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ORDER_CONTAIN_PRODUCT_VARIANT (OrderID, ProductID, Color, "Size", Quantity)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (order_id, product_id, color, size, quantity)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding order detail: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# Hàm cập nhật tổng chi tiêu của người dùng
def update_vendee_spending(user_id, amount):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE VENDEE_AND_CART
            SET TotalSpending = TotalSpending + %s
            WHERE UserID = %s
        """, (float(amount), user_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating vendee spending: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

# Hàm cập nhật thu nhập của người bán hàng
def update_vender_income(vender_id, amount):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE VENDER
            SET Income = COALESCE(Income, 0) + %s
            WHERE UserID = %s
        """, (float(amount), vender_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating vender income: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

def update_product_stock(product_id, color, size, quantity):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE PRODUCT_VARIANT
            SET StockQuantity = StockQuantity - %s
            WHERE ProductID = %s AND Color = %s AND "Size" = %s
        """, (quantity, product_id, color, size))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        print(f"Error updating product stock: {e}")
        conn.rollback()
        return False
    finally:
        close_db_connection(conn, cur)

def get_vender_id_by_product(product_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT v.UserID
            FROM VENDER v
            JOIN SHOP s ON v.UserID = s.UserID
            JOIN PRODUCT p ON s.ShopID = p.ShopID
            WHERE p.ProductID = %s
        """, (product_id,))
        vender = cur.fetchone()
        return vender['userid'] if vender else None
    except Exception as e:
        print(f"Error fetching vender ID: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm lấy danh sách shop có sản phẩm
def get_shops_with_products():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT s.ShopID, s."Name" AS name
            FROM SHOP s
            JOIN PRODUCT p ON s.ShopID = p.ShopID
            WHERE EXISTS (
                SELECT 1
                FROM PRODUCT_VARIANT pv
                WHERE pv.ProductID = p.ProductID
                AND pv.StockQuantity > 0
            )
            ORDER BY s."Name"
        """)
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
        query = """
            SELECT DISTINCT ON (p.ProductID)
                p.ProductID AS productid,
                p.Description AS name,
                (SELECT MIN(pv2.Price)
                 FROM PRODUCT_VARIANT pv2
                 WHERE pv2.ProductID = p.ProductID
                 AND pv2.StockQuantity > 0) AS price,
                (SELECT pi.Images 
                 FROM PRODUCT_IMAGES pi 
                 WHERE pi.ProductID = p.ProductID 
                 LIMIT 1) AS image
            FROM PRODUCT p
            LEFT JOIN PRODUCT_VARIANT pv ON p.ProductID = pv.ProductID
            JOIN SHOP s ON p.ShopID = s.ShopID
            WHERE EXISTS (
                SELECT 1
                FROM PRODUCT_VARIANT pv3
                WHERE pv3.ProductID = p.ProductID
                AND pv3.StockQuantity > 0
            )
        """
        params = []

        # Thêm điều kiện lọc theo loại sản phẩm
        if product_types:
            query += ' AND p."Type" IN %s'
            params.append(tuple(product_types))

        # Thêm điều kiện lọc theo shop
        if shop_ids:
            query += " AND s.ShopID IN %s"
            params.append(tuple(shop_ids))

        query += " ORDER BY p.ProductID"

        cur.execute(query, params)
        products = cur.fetchall()
        return [
            {
                'id': product['productid'],
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





# hàm lấy BIẾN THỂ của sản phẩm
def get_variants_by_product_id(product_id):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT pv.Color AS color,
                   pv."Size" AS size,
                   pv.Price AS price,
                   pv.StockQuantity AS quantity,
                   pv.Image AS image
            FROM PRODUCT_VARIANT pv
            WHERE pv.ProductID = %s
        """, (product_id,))
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
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT ShopID FROM shop WHERE UserID = %s", (user_id,))
        shop = cur.fetchone()
        if not shop:
            return None

        shop_id = shop['shopid']

        cur.execute("""
            SELECT p.ProductID, 
                    p.Description AS name, 
                    pv.Price AS price,
                    (SELECT array_agg(pv2.Color)
                    FROM PRODUCT_VARIANT pv2
                    WHERE pv2.ProductID = p.ProductID
                    AND pv2.StockQuantity > 0
                    ) AS colors,
                    pv.StockQuantity AS quantity, 
                   (SELECT pi.Images FROM PRODUCT_IMAGES pi WHERE pi.ProductID = p.ProductID LIMIT 1) AS image
            FROM PRODUCT p
            LEFT JOIN PRODUCT_VARIANT pv ON p.ProductID = pv.ProductID
            WHERE p.ShopID = %s AND pv.StockQuantity > 0
        """, (shop_id,))
    
        products = cur.fetchall()
        return products
    except Exception as e:
        print(f"Error fetching producst: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

# Hàm lấy sản phẩm theo ID (đã có từ trước, giữ nguyên)
def get_product_by_id_func(product_id):
    conn = get_db_connection()  
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM product WHERE productid = %s
            """, (product_id,)
        )
        product = cur.fetchone()
        if product:
            return product
        else:
            return None
    except Exception as e:
        print(f"Error fetching product: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm truy xuất shop theo UserID 
def get_shop_by_user_id(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM shop WHERE userid = %s", (user_id,))
        shop = cur.fetchone()
        
        if shop:
            return shop
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
        cur.execute(
            """
            INSERT INTO VOUCHER_CREATOR
            DEFAULT VALUES RETURNING creatorid; 
            """
        )
        creator_id = cur.fetchone()['creatorid']

        cur.execute(
            """
            INSERT INTO VENDER (UserID, Income, TaxNumber, CreatorId)
            VALUES (%s, %s, %s, %s) RETURNING UserID
            """, 
            (user_id, income, tax_number, creator_id)
        )
        vender_user_id = cur.fetchone()['userid']

        cur.execute(
            """
            INSERT INTO shop (Address, PhoneNumber, "Name", UserID) 
            VALUES (%s, %s, %s, %s) RETURNING ShopID
            """,
            (address, phone_num, name, vender_user_id)
        )
        shop_id = cur.fetchone()['shopid'] 

        conn.commit()
        return shop_id
    except Exception as e:
        print(f"Gặp lỗi khi đăng ký {e}")
        conn.rollback()
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
        cur.execute(
            """
            SELECT shopid 
            FROM shop 
            WHERE userid = %s
            """, 
            (user_id,)
        )
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

        cur.execute(
            """
            INSERT INTO PRODUCT ("Type", Description, ShopID) 
            VALUES (%s, %s, %s) RETURNING ProductID;
            """, 
            (type, description, shop_id)
        )
        product_id = cur.fetchone()['productid']  

        cur.execute(
            """
            INSERT INTO PRODUCT_VARIANT (Color, "Size", ProductID, Price, StockQuantity, Image) 
            VALUES (%s, %s, %s, %s, %s, %s);
            """, 
            (color, size, product_id, price, stock_quantity, pic_text)
        )

        conn.commit()
        return product_id  
    except Exception as e:
        print(f"Error registering product: {e}")
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm update SỐ LƯỢNG sản phẩm
def update_product(product_id, new_stock_quantity):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        
        cur.execute(
            "UPDATE product_variant SET StockQuantity = %s WHERE ProductID = %s",
            (new_stock_quantity, product_id)
            )
        conn.commit()
        print(f'Cập nhật số lượng thành công!', 'success')
    except Exception as e:
        print(f'Cập nhật thất bại: {e}', 'error')
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm xoá sản phẩm 
def delete_product(product_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()

        cur.execute(
            """
            DELETE FROM PRODUCT_VARIANT
            WHERE ProductID = %s;
            """,
            (product_id,)
        )
        
        cur.execute(
            """
            DELETE FROM PRODUCT
            WHERE ProductID = %s;
            """,
            (product_id,)
        )

        conn.commit()
        return product_id
    except Exception as e:
        print(f"Error deleting product: {e}")
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)

# Hàm HIỂN THỊ doanh thu
def get_seller_income(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT COALESCE(Income, 0) AS income
            FROM VENDER
            WHERE userid = %s;
            """,
            (user_id,)
        )

        row = cur.fetchone()
        return row['income'] if row else 0
    except Exception as e:
        print(f"Không thể truy xuất doanh thu: {e}")
        conn.rollback()
        return None
    finally:
        close_db_connection(conn, cur)
    
    