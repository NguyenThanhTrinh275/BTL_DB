import psycopg2
from psycopg2.extras import RealDictCursor
from website.config import Config

def get_db_connection():
    try:
        conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=RealDictCursor)
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

# Hàm kiểm tra email đã tồn tại chưa
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


def add_to_cart(user_id, product_id, color, size, quantity, price):
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
                p.Description AS name,
                cc.Color,
                cc.Size,
                cc.Quantity,
                cc.TotalMoney,
                pv.Price,
                pv.StockQuantity
            FROM CART_CONTAIN_PRODUCT_VARIANT cc
            JOIN PRODUCT p ON cc.ProductID = p.ProductID
            JOIN PRODUCT_VARIANT pv ON cc.ProductID = pv.ProductID AND cc.Color = pv.Color AND cc.Size = pv.Size
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
                'quantity': item['quantity'],
                'price': item['price'],
                'total_money': item['totalmoney'],
                'stock': item['stockquantity']
            }
            for item in items
        ]
    except Exception as e:
        print(f"Error fetching cart: {e}")
        return []
    finally:
        close_db_connection(conn, cur)

def get_user_info(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                u.UserID,
                u.FirstName,
                u.LastName,
                u.Email,
                up.PhoneNumber,
                u.DateOfBirth
            FROM "USER" u
            JOIN USER_PHONE up ON u.UserID = up.UserID
            WHERE u.UserID = %s
        """, (user_id,))
        user_info = cur.fetchone()
        return {
            'user_id': user_info['userid'],
            'first_name': user_info['firstname'],
            'last_name': user_info['lastname'],
            'email': user_info['email'],
            'phone_number': user_info['phonenumber'],
            'date_of_birth': user_info['dateofbirth']
        }
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return None
    finally:
        close_db_connection(conn, cur)

# # Hàm tạo đơn hàng (đã có từ trước, giữ nguyên)
# def create_order(user_id):
#     conn = get_db_connection()
#     if not conn:
#         return None
#     try:
#         cur = conn.cursor()
#         cur.execute("CALL create_order(%s, NULL)", (user_id,))
#         conn.commit()
#         cur.execute("SELECT currval(pg_get_serial_sequence('orders', 'order_id'))")
#         order_id = cur.fetchone()['currval']
#         return order_id
#     finally:
#         close_db_connection(conn, cur)

# # Hàm thêm chi tiết đơn hàng (đã có từ trước, giữ nguyên)
# def add_order_detail(order_id, product_id, quantity, unit_price):
#     conn = get_db_connection()
#     if not conn:
#         return False
#     try:
#         cur = conn.cursor()
#         cur.execute(
#             "INSERT INTO order_details (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
#             (order_id, product_id, quantity, unit_price)
#         )
#         conn.commit()
#         return True
#     except Exception as e:
#         print(f"Error adding order detail: {e}")
#         conn.rollback()
#         return False
#     finally:
#         close_db_connection(conn, cur)