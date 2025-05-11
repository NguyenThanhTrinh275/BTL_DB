--
-- SELECT * FROM get_user_by_id(2);
CREATE OR REPLACE FUNCTION get_user_by_id(p_user_id INTEGER)
RETURNS TABLE (
    FirstName TEXT,
    LastName TEXT,
    Email TEXT,
    DateOfBirth DATE,
	TotalSpending DECIMAL(15,2)
) AS $$
BEGIN
    RETURN QUERY
	SELECT 
		u.FirstName,
        u.LastName,
        u.Email,
        u.DateOfBirth,
        vc.TotalSpending
    FROM "USER" u
    JOIN VENDEE_AND_CART vc ON u.UserID = vc.UserID
    WHERE u.UserID = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- 
-- SELECT * FROM get_user_phones(1);
CREATE OR REPLACE FUNCTION get_user_phones(p_user_id INTEGER)
RETURNS TABLE (phone_number VARCHAR(15)) AS $$
BEGIN
    RETURN QUERY
    SELECT PhoneNumber
    FROM USER_PHONE
    WHERE UserID = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- 
-- Chỉ hiển thị các sản phẩm có ít nhất một biến thể (PRODUCT_VARIANT) còn tồn kho (StockQuantity > 0).
-- SELECT * FROM get_products();
CREATE OR REPLACE FUNCTION get_products()
RETURNS TABLE (
    product_id INTEGER,
    name TEXT,
    price DECIMAL(15,2),
    image TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (p.ProductID)
        p.ProductID AS product_id,
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
    ORDER BY p.ProductID;
END;
$$ LANGUAGE plpgsql;

-- trả về danh sách các biến thể còn hàng của một sản phẩm
-- SELECT * FROM get_product_and_variants(1);
CREATE OR REPLACE FUNCTION get_product_and_variants(p_product_id INTEGER)
RETURNS TABLE (
    product_id INTEGER,
    name TEXT,
    choice TEXT,
    price DECIMAL(15,2),
    stock INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.ProductID AS product_id,
        p.Description AS name,
        pv.Color || ', ' || pv."Size" AS choice,
        pv.Price AS price,
        pv.StockQuantity AS stock
    FROM PRODUCT p
    LEFT JOIN PRODUCT_VARIANT pv ON p.ProductID = pv.ProductID
    WHERE p.ProductID = p_product_id AND pv.StockQuantity > 0
    ORDER BY pv.Color, pv."Size";
END;
$$ LANGUAGE plpgsql;

-- trả về tất cả hình ảnh của một sản phẩm, bao gồm ảnh chung từ PRODUCT_IMAGES
-- và ảnh của từng biến thể từ PRODUCT_VARIANT.
-- SELECT * FROM get_product_images(1);
CREATE OR REPLACE FUNCTION get_product_images(p_product_id INTEGER)
RETURNS TABLE (
    image TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT pi.Images
    FROM PRODUCT_IMAGES pi
    WHERE pi.ProductID = p_product_id
    UNION
    SELECT pv.Image
    FROM PRODUCT_VARIANT pv
    WHERE pv.ProductID = p_product_id;
END;
$$ LANGUAGE plpgsql;

-- 
-- trả về danh sách các sản phẩm có trong giỏ hàng của một người dùng
-- SELECT * FROM get_cart_items(9);
CREATE OR REPLACE FUNCTION get_cart_items(p_user_id INTEGER)
RETURNS TABLE (
    cart_id INTEGER,
    product_id INTEGER,
    image TEXT,
    name TEXT,
    color VARCHAR(100),
    size VARCHAR(10),
    quantity INTEGER,
    total_money DECIMAL(15,2),
    price DECIMAL(15,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cc.CartID,
        cc.ProductID,
        pv.Image,
        p.Description AS name,
        cc.Color,
        cc."Size",
        cc.Quantity,
        cc.TotalMoney,
        pv.Price
    FROM CART_CONTAIN_PRODUCT_VARIANT cc
    JOIN PRODUCT p ON cc.ProductID = p.ProductID
    JOIN PRODUCT_VARIANT pv ON cc.ProductID = pv.ProductID AND cc.Color = pv.Color AND cc."Size" = pv."Size"
    JOIN VENDEE_AND_CART vc ON cc.CartID = vc.CartID
    WHERE vc.UserID = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- 
-- kiểm tra xem email được cung cấp có tồn tại trong bảng "USER" hay không,
-- trả về TRUE nếu có, FALSE nếu không.
-- Trả về false
-- SELECT check_email_exists('example@example.com');
-- Trả về true
-- SELECT check_email_exists('hai.ng@example.com');
CREATE OR REPLACE FUNCTION check_email_exists(p_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM "USER" WHERE Email = p_email
    );
END;
$$ LANGUAGE plpgsql;

-- 
-- xác thực tài khoản người dùng bằng email và mật khẩu.
-- Nếu đúng, trả về thông tin UserID, FirstName, LastName, Email; nếu sai, trả về kết quả rỗng
-- True
-- SELECT login_user('haib.ng@example.com', '123');
-- False
-- SELECT login_user('abc.ng@example.com', '123');
CREATE OR REPLACE FUNCTION login_user(p_email TEXT, p_password TEXT)
RETURNS TABLE (
    UserID INTEGER,
    FirstName TEXT,
    LastName TEXT,
    Email TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.UserID, u.FirstName, u.LastName, u.Email
    FROM "USER" u
    WHERE u.Email = p_email AND u."Password" = p_password;
END;
$$ LANGUAGE plpgsql;
-- 
-- trả về tất cả các địa chỉ giao hàng của một người dùng
-- SELECT * FROM get_user_addresses(12);
CREATE OR REPLACE FUNCTION get_user_addresses(p_user_id INTEGER)
RETURNS TABLE (
    homenumber VARCHAR(200),
    street VARCHAR(255),
    district VARCHAR(255),
    city VARCHAR(255),
    province VARCHAR(255),
    isdefault BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT v.HomeNumber, v.Street, v.District, v.City, v.Province, v.IsDefault
    FROM VENDEE_ADDRESS v
    WHERE v.UserID = p_user_id;
END;
$$ LANGUAGE plpgsql;
-- 
-- trả về UserID của người bán (VENDER) sở hữu sản phẩm có ProductID được cung cấp,
-- thông qua liên kết giữa VENDER, SHOP, và PRODUCT.
-- SELECT get_vender_id_by_product(1);
CREATE OR REPLACE FUNCTION get_vender_id_by_product(p_product_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    vender_id INTEGER;
BEGIN
    SELECT v.UserID
    INTO vender_id
    FROM VENDER v
    JOIN SHOP s ON v.UserID = s.UserID
    JOIN PRODUCT p ON s.ShopID = p.ShopID
    WHERE p.ProductID = p_product_id;
    
    RETURN vender_id;
END;
$$ LANGUAGE plpgsql;

-- 
-- trả về danh sách các cửa hàng (ShopID, tên Shop) 
-- đang có ít nhất một sản phẩm còn hàng (StockQuantity > 0) trong kho.
-- SELECT get_shops_with_products();
CREATE OR REPLACE FUNCTION get_shops_with_products()
RETURNS TABLE (
    shopid INTEGER,
    name VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT s.ShopID, s."Name" AS name
    FROM SHOP s
    JOIN PRODUCT p ON s.ShopID = p.ShopID
    WHERE EXISTS (
        SELECT 1
        FROM PRODUCT_VARIANT pv
        WHERE pv.ProductID = p.ProductID
        AND pv.StockQuantity > 0
    )
    ORDER BY s."Name";
END;
$$ LANGUAGE plpgsql;

-- giúp lấy CartID từ VENDEE_AND_CART cho một UserID
-- SELECT get_cart_id_from_user_id(1);
CREATE OR REPLACE FUNCTION get_cart_id_from_user_id(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_cart_id INTEGER;
BEGIN
    SELECT CartID INTO v_cart_id
    FROM VENDEE_AND_CART
    WHERE UserID = p_user_id;
    
    RETURN v_cart_id;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN NULL;
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error in get_cart_id_from_user_id: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- 
-- giúp tra cứu CartID dựa trên UserID, và xử lý các tình huống không có dữ liệu hoặc lỗi.
-- SELECT get_cart_id_from_user_id(1);
CREATE OR REPLACE FUNCTION get_cart_items_with_stock(p_cart_id INTEGER)
RETURNS TABLE (
    product_id INTEGER,
    color VARCHAR(100),
    size VARCHAR(10),
    requested_quantity INTEGER,
    available_quantity INTEGER,
    product_name TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.ProductID, 
        c.Color, 
        c."Size", 
        c.Quantity AS requested_quantity, 
        pv.StockQuantity AS available_quantity,
        p.Description AS product_name
    FROM CART_CONTAIN_PRODUCT_VARIANT c
    JOIN PRODUCT_VARIANT pv 
        ON c.ProductID = pv.ProductID 
        AND c.Color = pv.Color 
        AND c."Size" = pv."Size"
    JOIN PRODUCT p 
        ON c.ProductID = p.ProductID
    WHERE c.CartID = p_cart_id;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error in get_cart_items_with_stock: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

--
-- Function này giúp lấy ảnh của sản phẩm từ bảng PRODUCT_IMAGES
-- SELECT get_product_image(1);
CREATE OR REPLACE FUNCTION get_product_image(p_product_id INTEGER)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_image TEXT;
BEGIN
    -- Truy vấn lấy ảnh đầu tiên (LIMIT 1) cho ProductID
    SELECT Images
    INTO v_image
    FROM PRODUCT_IMAGES
    WHERE ProductID = p_product_id
    LIMIT 1;

    -- Nếu không tìm thấy ảnh, gán giá trị mặc định
    IF v_image IS NULL THEN
        RAISE NOTICE 'No image found for ProductID %', p_product_id;
        v_image := 'default_image.jpg';
    END IF;

    RETURN v_image;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error in get_product_image for ProductID %: %', p_product_id, SQLERRM;
        RETURN 'default_image.jpg';
END;
$$;

--
-- Function này lấy tất cả các biến thể của một sản phẩm (dựa trên ProductID)
-- và trả về thông tin về màu sắc, kích thước, giá, số lượng tồn kho và ảnh của mỗi biến thể.
-- SELECT * FROM get_variants_by_product_id(1);
CREATE OR REPLACE FUNCTION get_variants_by_product_id(product_id INTEGER)
RETURNS TABLE (
    color VARCHAR(100),
    size VARCHAR(10),
    price DECIMAL(15,2),
    quantity INTEGER,
    image TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pv.Color AS color,
        pv."Size" AS size,
        pv.Price AS price,
        pv.StockQuantity AS quantity,
        pv.Image AS image
    FROM PRODUCT_VARIANT pv
    WHERE pv.ProductID = product_id;
END;
$$ LANGUAGE plpgsql;

-- lấy tất cả các sản phẩm của 1 người đang bán
-- SELECT * FROM get_products_by_userid(1);
CREATE OR REPLACE FUNCTION get_products_by_userid(user_id INTEGER)
RETURNS TABLE (
    productid INTEGER,
    name TEXT,
    image TEXT,
    variants JSONB
) AS $$
DECLARE
    shop_id INTEGER;
    product_record RECORD;
    variant_record RECORD;
    variants JSONB;
BEGIN
    -- Lấy ShopID từ UserID
    SELECT ShopID INTO shop_id
    FROM shop
    WHERE UserID = user_id;

    IF shop_id IS NULL THEN
        RETURN;  -- Nếu không có ShopID thì không trả về gì
    END IF;

    -- Duyệt qua các sản phẩm của ShopID này
    FOR product_record IN
        SELECT DISTINCT ON (p.ProductID)
            p.ProductID AS productid,
            p.Description AS name,
            (SELECT pi.Images 
             FROM PRODUCT_IMAGES pi 
             WHERE pi.ProductID = p.ProductID 
             LIMIT 1) AS image
        FROM PRODUCT p
        WHERE p.ShopID = shop_id
    LOOP
        -- Lấy các biến thể của sản phẩm
        variants := '[]'::jsonb;
        FOR variant_record IN
            SELECT 
                pv.Color AS color,
                pv."Size" AS size,
                pv.Price AS price,
                pv.StockQuantity AS quantity,
                pv.Image AS image
            FROM PRODUCT_VARIANT pv
            WHERE pv.ProductID = product_record.productid AND pv.StockQuantity > 0
        LOOP
            -- Thêm các biến thể vào mảng variants
            variants := variants || jsonb_build_object(
                'color', variant_record.color,
                'size', variant_record.size,
                'price', variant_record.price,
                'quantity', variant_record.quantity
            );
        END LOOP;

        -- Trả về sản phẩm và các biến thể
        RETURN QUERY SELECT 
            product_record.productid, 
            product_record.name, 
            COALESCE(product_record.image, 'default.png') AS image, 
            variants;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

--
-- trả về thu nhập của người bán tương ứng từ bảng VENDER
-- SELECT get_seller_income(1);
CREATE OR REPLACE FUNCTION get_seller_income(user_id INTEGER)
RETURNS DECIMAL(15,2) AS $$
DECLARE
    income DECIMAL(15,2);
BEGIN
    SELECT COALESCE(VENDER.Income, 0) INTO income
    FROM VENDER
    WHERE VENDER.UserID = user_id;

    RETURN income;
END;
$$ LANGUAGE plpgsql;

-- Hàm reg_shop_func tạo các bản ghi trong các bảng VOUCHER_CREATOR, VENDER, và SHOP,
-- sau đó trả về ShopID của cửa hàng mới được tạo.
-- SELECT reg_shop_func(12, 'Shop ABC', '123 Street, City', 1000000.00, '1234567890', '0901234567');
CREATE OR REPLACE FUNCTION reg_shop_func(
    user_id INTEGER, 
    name VARCHAR(100), 
    address VARCHAR(255), 
    income DECIMAL(15,2), 
    tax_number CHAR(20), 
    phone_num VARCHAR(15)
)
RETURNS INTEGER AS $$	
DECLARE
    creator_id TEXT;
    vender_user_id INTEGER;
    shop_id INTEGER;
BEGIN
    -- Tạo bản ghi trong VOUCHER_CREATOR và lấy creator_id
    INSERT INTO VOUCHER_CREATOR DEFAULT VALUES
    RETURNING CreatorID INTO creator_id;

    -- Tạo bản ghi trong VENDER và lấy vender_user_id
    INSERT INTO VENDER (UserID, Income, TaxNumber, CreatorID)
    VALUES (user_id, income, tax_number, creator_id)
    RETURNING UserID INTO vender_user_id;

    -- Tạo bản ghi trong SHOP và lấy shop_id
    INSERT INTO shop (Address, PhoneNumber, "Name", UserID)
    VALUES (address, phone_num, name, vender_user_id)
    RETURNING ShopID INTO shop_id;

    -- Trả về ShopID
    RETURN shop_id;
END;
$$ LANGUAGE plpgsql;

--
-- trả về shop_id của người dùng có user_id
-- SELECT get_shop_id_by_user_id(1);
CREATE OR REPLACE FUNCTION get_shop_id_by_user_id(user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    shop_id INTEGER;
BEGIN
    -- Truy vấn để lấy shop_id từ bảng shop
    SELECT shopid
    INTO shop_id
    FROM shop
    WHERE userid = user_id;

    -- Nếu không tìm thấy shop_id, trả về NULL
    IF NOT FOUND THEN
        shop_id := NULL;
    END IF;

    -- Trả về shop_id
    RETURN shop_id;
END;
$$ LANGUAGE plpgsql;

-- trả về các chi tiết như mã cửa hàng, tên cửa hàng, địa chỉ và số điện thoại của chủ shop
-- SELECT * FROM get_shop_by_user_id(1);
CREATE OR REPLACE FUNCTION get_shop_by_user_id(user_id INTEGER)
RETURNS TABLE (
    shopid INTEGER,
    userid INTEGER,
    shop_name VARCHAR(100),
    shop_address VARCHAR(255),
    shop_phone VARCHAR(15)
) AS $$
BEGIN
    -- Truy vấn thông tin cửa hàng từ bảng SHOP theo UserID
    RETURN QUERY
    SELECT 
        s.ShopID, 
        s.UserID, 
        s."Name" AS shop_name, 
        s.Address AS shop_address, 
        s.PhoneNumber AS shop_phone
    FROM shop s
    WHERE s.UserID = user_id;
END;
$$ LANGUAGE plpgsql;

---------------------------------------------------------------------------------------------------
-- Trigger Trigger Trigger Trigger Trigger Trigger Trigger Trigger Trigger Trigger Trigger --
-- tự động tính TotalMoney = Quantity × Price mỗi khi thêm mới hoặc cập nhật
-- một dòng trong bảng CART_CONTAIN_PRODUCT_VARIANT.
-- INSERT INTO CART_CONTAIN_PRODUCT_VARIANT (ProductID, Color, "Size", CartID, Quantity)
-- VALUES (1, 'Black', 'M', 4, 2); 
CREATE OR REPLACE FUNCTION trg_cart_item_money()
RETURNS TRIGGER AS $$
BEGIN
    NEW.TotalMoney := NEW.Quantity * (
        SELECT Price
        FROM PRODUCT_VARIANT v
        WHERE v.ProductID = NEW.ProductID
        AND v.Color = NEW.Color
        AND v."Size" = NEW."Size"
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER biu_cart_money
    BEFORE INSERT OR UPDATE ON CART_CONTAIN_PRODUCT_VARIANT
    FOR EACH ROW EXECUTE FUNCTION trg_cart_item_money();

---
-- Mỗi khi có đơn hàng mới được thêm vào, cập nhật, hoặc xóa đi trong bảng "ORDER",
-- thì tổng số tiền (TotalSpending) của người mua (VENDEE_AND_CART) sẽ tự động được tính lại.
-- INSERT INTO "ORDER" (PaymentMethod, TotalMoney, TotalProduct, HomeNumber, Street, District, City, Province, CartID)
-- VALUES ('Credit Card', 500000, 2, '123A', 'Le Loi', 'District 1', 'Ho Chi Minh City', 'South', 9);
CREATE OR REPLACE FUNCTION trg_vendee_spending()
RETURNS TRIGGER AS $$
DECLARE
    v_spend NUMERIC;
BEGIN
    SELECT COALESCE(SUM(TotalMoney), 0)
    INTO v_spend
    FROM "ORDER"
    WHERE CartID = COALESCE(NEW.CartID, OLD.CartID);

    UPDATE VENDEE_AND_CART
    SET TotalSpending = v_spend
    WHERE CartID = COALESCE(NEW.CartID, OLD.CartID);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER afu_vendee_spend
    AFTER INSERT OR UPDATE OR DELETE ON "ORDER"
    FOR EACH ROW EXECUTE FUNCTION trg_vendee_spending();

-- 
-- sau mỗi lần INSERT, UPDATE, hoặc DELETE trên bảng ORDER_CONTAIN_PRODUCT_VARIANT.
-- Trigger sẽ gọi function fn_recalc_all_vender_income, chức năng là tính lại tổng thu nhập (Income)
-- cho tất cả người bán (VENDER), bằng cách cộng tổng số tiền (Quantity × Price) 
-- từ các sản phẩm đã bán ra liên kết với từng người bán qua bảng SHOP và PRODUCT.
-- INSERT INTO ORDER_CONTAIN_PRODUCT_VARIANT (ProductID, Color, "Size", OrderID, Quantity)
-- VALUES (1, 'Black', 'M', 1, 2);
CREATE OR REPLACE FUNCTION fn_recalc_all_vender_income()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE VENDER v
    SET Income = COALESCE((
        SELECT SUM(o.Quantity * pv.Price)
        FROM ORDER_CONTAIN_PRODUCT_VARIANT o
        JOIN PRODUCT_VARIANT pv
            ON pv.ProductID = o.ProductID
            AND pv.Color = o.Color
            AND pv."Size" = o."Size"
        JOIN PRODUCT p ON p.ProductID = pv.ProductID
        JOIN SHOP s ON s.ShopID = p.ShopID
        WHERE s.UserID = v.UserID
    ), 0);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER st_recalc_vender_income
    AFTER INSERT OR UPDATE OR DELETE ON ORDER_CONTAIN_PRODUCT_VARIANT
    FOR EACH STATEMENT EXECUTE FUNCTION fn_recalc_all_vender_income();

-- 
-- giảm số lượng tồn kho (StockQuantity) của sản phẩm trong bảng PRODUCT_VARIANT,
-- theo ProductID, Color, và Size của sản phẩm được thêm hoặc cập nhật trong giỏ hàng.
-- INSERT INTO ORDER_CONTAIN_PRODUCT_VARIANT (ProductID, Color, "Size", OrderID, Quantity)
-- VALUES (1, 'Black', 'M', 4, 2);
CREATE OR REPLACE FUNCTION trg_update_product_stock()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE PRODUCT_VARIANT
    SET StockQuantity = StockQuantity - NEW.Quantity
    WHERE ProductID = NEW.ProductID
    AND Color = NEW.Color
    AND "Size" = NEW."Size";
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER aft_insert_order_variant
    AFTER INSERT ON ORDER_CONTAIN_PRODUCT_VARIANT
    FOR EACH ROW EXECUTE FUNCTION trg_update_product_stock();

-- trigger không cho phép thay đổi giá quá 50% 
CREATE OR REPLACE FUNCTION trg_check_price_change()
RETURNS trigger AS $$
DECLARE
    price_change_ratio NUMERIC;
BEGIN
    -- Only check when the price is actually changed
    IF NEW.Price IS DISTINCT FROM OLD.Price THEN
        -- Calculate the price change ratio
        price_change_ratio := NEW.Price / OLD.Price;

        -- If price increase more than 50% or decrease more than 50%
        IF price_change_ratio > 1.5 OR price_change_ratio < 0.5 THEN
            RAISE EXCEPTION
                'Price change is too large! Old price: %, New price: % (Allowed: ±50%%)',
                OLD.Price, NEW.Price;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER check_price_change
BEFORE UPDATE ON PRODUCT_VARIANT
FOR EACH ROW
EXECUTE FUNCTION trg_check_price_change();


-- Procedure Procedure Procedure Procedure Procedure Procedure Procedure ---------

--1)
-- Procedure Thoa man yeu cau
CREATE OR REPLACE PROCEDURE get_products_filtered(
    IN p_product_types VARCHAR(100)[],
    IN p_shop_ids INTEGER[],
    IN p_min_price DECIMAL,
    IN p_max_price DECIMAL,
    IN p_sort_order VARCHAR,
    INOUT p_result refcursor
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Xác thực tham số đầu vào
    IF p_min_price < 0 THEN
        RAISE EXCEPTION 'Giá tối thiểu không thể âm: %', p_min_price;
    END IF;
    IF p_max_price < 0 THEN
        RAISE EXCEPTION 'Giá tối đa không thể âm: %', p_max_price;
    END IF;
    IF p_max_price < p_min_price THEN
        RAISE EXCEPTION 'Giá tối đa phải lớn hơn giá tối thiểu: min = %, max = %', p_min_price, p_max_price;
    END IF;

    -- Mở con trỏ để trả về kết quả
    OPEN p_result FOR
    WITH ProductMinPrice AS (
        -- Lấy giá thấp nhất của các biến thể sản phẩm có hàng tồn kho
        SELECT 
            p.ProductID,
            p.Description AS name,
            p."Type",
            s.ShopID,
            s."Name" AS shop_name,
            MIN(pv.Price) AS min_price
        FROM PRODUCT p
        JOIN PRODUCT_VARIANT pv ON p.ProductID = pv.ProductID
        JOIN SHOP s ON p.ShopID = s.ShopID
        WHERE pv.StockQuantity > 0
        GROUP BY p.ProductID, p.Description, p."Type", s.ShopID, s."Name"
        HAVING MIN(pv.Price) BETWEEN p_min_price AND p_max_price
    )
    SELECT 
        pmp.ProductID AS product_id,
        pmp.name,
        pmp.min_price AS price,
        pmp."Type" AS product_type,
        pmp.ShopID AS shop_id,
        pmp.shop_name,
        COALESCE((
            SELECT pi.Images 
            FROM PRODUCT_IMAGES pi 
            WHERE pi.ProductID = pmp.ProductID 
            LIMIT 1
        ), 'default.png') AS image
    FROM ProductMinPrice pmp
    WHERE 
        (p_product_types IS NULL OR pmp."Type" = ANY(p_product_types))
        AND (p_shop_ids IS NULL OR pmp.ShopID = ANY(p_shop_ids))
    ORDER BY 
        CASE WHEN p_sort_order = 'asc' THEN pmp.min_price END ASC,
        CASE WHEN p_sort_order = 'desc' THEN pmp.min_price END DESC;
END;
$$;

--2)
-- thêm một người dùng mới vào bảng "USER", sau đó tự động tạo bản ghi tương ứng
-- trong bảng NonAdmin và VENDEE_AND_CART với TotalSpending = 0.
CREATE OR REPLACE PROCEDURE insert_user(
    p_password TEXT,
    p_first_name TEXT,
    p_last_name TEXT,
    p_email TEXT,
    p_date_of_birth DATE,
    OUT p_user_id INTEGER
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO "USER" ("Password", FirstName, LastName, Email, DateOfBirth)
    VALUES (p_password, p_first_name, p_last_name, p_email, p_date_of_birth)
    RETURNING UserID INTO p_user_id;
    
    INSERT INTO NonAdmin (UserID) VALUES (p_user_id);
    INSERT INTO VENDEE_AND_CART (UserID, TotalSpending, CartID)
    VALUES (p_user_id, 0.00, p_user_id);
END;
$$;

-- CALL insert_user('pass123', 'John', 'Doe', 'john.doe@example.com', '1990-01-01', NULL);

--3)
CREATE OR REPLACE PROCEDURE insert_user_phone(
    p_user_id INTEGER,
    p_phone_number VARCHAR(15)
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO USER_PHONE (UserID, PhoneNumber)
    VALUES (p_user_id, p_phone_number);
END;
$$;
-- CALL insert_user_phone(1, '0912345670');

--4)
-- hêm một đơn hàng mới vào bảng "ORDER", với thông tin về phương thức thanh toán,
-- tổng tiền, tổng số sản phẩm, địa chỉ giao hàng và CartID tương ứng.
CREATE OR REPLACE PROCEDURE insert_order(
    p_payment_method VARCHAR(50),
    p_total_money DECIMAL(15,2),
    p_total_product INTEGER,
    p_home_number VARCHAR(200),
    p_street VARCHAR(255),
    p_district VARCHAR(255),
    p_city VARCHAR(255),
    p_province VARCHAR(255),
    p_cart_id INTEGER,
    OUT p_order_id INTEGER
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO "ORDER" (PaymentMethod, TotalMoney, TotalProduct, HomeNumber, Street, District, City, Province, CartID)
    VALUES (p_payment_method, p_total_money, p_total_product, p_home_number, p_street, p_district, p_city, p_province, p_cart_id)
    RETURNING OrderID INTO p_order_id;
END;
$$;
-- CALL insert_order('PAID', 1500000.00, 3, '123A', 'Nguyen Trai', 'District 1', 'HCMC', 'HCMC', 12, NULL);

--5)
-- 
--Procedure tạo các product variant liên quan đến các order
CREATE OR REPLACE PROCEDURE insert_order_product_variant(
    p_product_id INTEGER,
    p_color VARCHAR(100),
    p_size VARCHAR(10),
    p_order_id INTEGER,
    p_quantity INTEGER
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO ORDER_CONTAIN_PRODUCT_VARIANT (ProductID, Color, "Size", OrderID, Quantity)
    VALUES (p_product_id, p_color, p_size, p_order_id, p_quantity);
END;
$$;

-- CALL insert_order_product_variant(
--    1,            -- p_product_id
--    'Black',      -- p_color
--    'M',          -- p_size
--    1,            -- p_order_id
--  2             -- p_quantity
--);


--6)
-- Procedure để chèn hoặc cập nhật giỏ hàng
CREATE OR REPLACE PROCEDURE insert_or_update_cart_product_variant(
    p_product_id INTEGER,
    p_color VARCHAR(100),
    p_size VARCHAR(10),
    p_cart_id INTEGER,
    p_quantity INTEGER
)
LANGUAGE plpgsql AS $$
DECLARE
    v_existing_quantity INTEGER;
BEGIN
    -- Kiểm tra xem sản phẩm đã có trong giỏ hàng chưa
    SELECT Quantity
    INTO v_existing_quantity
    FROM CART_CONTAIN_PRODUCT_VARIANT
    WHERE CartID = p_cart_id
    AND ProductID = p_product_id
    AND Color = p_color
    AND "Size" = p_size;
    
    IF v_existing_quantity IS NOT NULL THEN
        -- Cập nhật số lượng
        UPDATE CART_CONTAIN_PRODUCT_VARIANT
        SET Quantity = v_existing_quantity + p_quantity
        WHERE CartID = p_cart_id
        AND ProductID = p_product_id
        AND Color = p_color
        AND "Size" = p_size;
    ELSE
        -- Chèn mới
        INSERT INTO CART_CONTAIN_PRODUCT_VARIANT (ProductID, Color, "Size", CartID, Quantity)
        VALUES (p_product_id, p_color, p_size, p_cart_id, p_quantity);
    END IF;
END;
$$;
--CALL insert_or_update_cart_product_variant(1, 'Black', 'M', '14', 1);


--7)
--Procedure để xóa product variant khỏi giỏ hàng khi người dùng thao tác
CREATE OR REPLACE PROCEDURE delete_cart_product_variant(
    p_cart_id INTEGER,
    p_product_id INTEGER,
    p_color VARCHAR(100),
    p_size VARCHAR(10)
)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM CART_CONTAIN_PRODUCT_VARIANT
    WHERE CartID = p_cart_id AND ProductID = p_product_id AND Color = p_color AND "Size" = p_size;
END;
$$;

--CALL delete_cart_product_variant(12, 1, 'White','S');

--8)
--Procedure trong việc thêm địa chỉ của người mua hàng, nếu người mua hàng chọn đó là địa chỉ mặc định, sẽ gán mặc định cho địa chỉ cũ nếu có
CREATE OR REPLACE PROCEDURE add_user_address(
    p_user_id INTEGER,
    p_home_number VARCHAR(200),
    p_street VARCHAR(255),
    p_district VARCHAR(255),
    p_city VARCHAR(255),
    p_province VARCHAR(255),
    p_is_default BOOLEAN
)
LANGUAGE plpgsql AS $$
BEGIN
    -- Set false for other address if new is default
    IF p_is_default THEN
        UPDATE VENDEE_ADDRESS
        SET IsDefault = FALSE
        WHERE UserID = p_user_id;
    END IF;
    
    -- add new address
    INSERT INTO VENDEE_ADDRESS (UserID, HomeNumber, Street, District, City, Province, IsDefault)
    VALUES (p_user_id, p_home_number, p_street, p_district, p_city, p_province, p_is_default);
END;
$$;
--CALL add_user_address(14, '27A', 'An Lac Street','8', 'HCMC', 'HCMC', True);
--CALL add_user_address(14, '11A', 'An Lac Street','8', 'HCMC', 'HCMC', True);

-- 9)
--Procedure trong việc thêm địa chỉ của người mua hàng, nếu người mua hàng chọn đó là địa chỉ mặc định, sẽ gán mặc định cho địa chỉ cũ nếu có
CREATE OR REPLACE PROCEDURE delete_user_address(
    p_user_id INTEGER,
    p_home_number VARCHAR(200),
    p_street VARCHAR(255),
    p_district VARCHAR(255),
    p_city VARCHAR(255),
    p_province VARCHAR(255)
)
LANGUAGE plpgsql AS $$
DECLARE
    v_is_default BOOLEAN;
BEGIN
    -- Step 1: Check if the address being deleted is default
    SELECT IsDefault
    INTO v_is_default
    FROM VENDEE_ADDRESS
    WHERE UserID = p_user_id
      AND HomeNumber = p_home_number
      AND Street = p_street
      AND District = p_district
      AND City = p_city
      AND Province = p_province;

    -- Step 2: Delete the address
    DELETE FROM VENDEE_ADDRESS
    WHERE UserID = p_user_id 
      AND HomeNumber = p_home_number 
      AND Street = p_street 
      AND District = p_district 
      AND City = p_city 
      AND Province = p_province;

    -- Step 3: If deleted address was default, promote another address
    IF v_is_default THEN
        UPDATE VENDEE_ADDRESS
        SET IsDefault = TRUE
        WHERE ctid = (
            SELECT ctid
            FROM VENDEE_ADDRESS
            WHERE UserID = p_user_id
            LIMIT 1
        );
    END IF;
END;
$$;

--CALL add_user_address(14, '27A', 'An Lac Street','8', 'HCMC', 'HCMC', True);
--CALL add_user_address(14, '11A', 'An Lac Street','8', 'HCMC', 'HCMC', True);
--CALL delete_user_address(14, '11A', 'An Lac Street', '8', 'HCMC', 'HCMC');


--10)
-- Procedure được dùng ở phía Backend, khi người dùng thao tác chỉnh sửa địa chỉ (thay đổi nơi, thay đổi mặc định)
CREATE OR REPLACE PROCEDURE update_user_address(
    p_user_id INTEGER,
    p_old_home_number VARCHAR(200),
    p_old_street VARCHAR(255),
    p_old_district VARCHAR(255),
    p_old_city VARCHAR(255),
    p_old_province VARCHAR(255),
    p_new_home_number VARCHAR(200),
    p_new_street VARCHAR(255),
    p_new_district VARCHAR(255),
    p_new_city VARCHAR(255),
    p_new_province VARCHAR(255)
)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE VENDEE_ADDRESS
    SET HomeNumber = p_new_home_number,
        Street = p_new_street,
        District = p_new_district,
        City = p_new_city,
        Province = p_new_province
    WHERE UserID = p_user_id
    AND HomeNumber = p_old_home_number
    AND Street = p_old_street
    AND District = p_old_district
    AND City = p_old_city
    AND Province = p_old_province;
END;
$$;

-- 
CREATE OR REPLACE PROCEDURE set_default_address(
    p_user_id INTEGER,
    p_home_number VARCHAR(200),
    p_street VARCHAR(255),
    p_district VARCHAR(255),
    p_city VARCHAR(255),
    p_province VARCHAR(255)
)
LANGUAGE plpgsql AS $$
BEGIN
    -- Bo mac dinh cua tat ca dia chi
    UPDATE VENDEE_ADDRESS
    SET IsDefault = FALSE
    WHERE UserID = p_user_id;
    
    -- Dat dia chi nay lam mac dinh
    UPDATE VENDEE_ADDRESS
    SET IsDefault = TRUE
    WHERE UserID = p_user_id
    AND HomeNumber = p_home_number
    AND Street = p_street
    AND District = p_district
    AND City = p_city
    AND Province = p_province;
END;
$$;
--CALL update_user_address(14, '12A', 'An Lac Street', '8', 'HCMC', 'HCMC', '13A', 'An Lac Street', '8', 'HCMC', 'HCMC');
--SELECT * FROM vendee_address;
--CALL set_default_address(14, '27A', 'An Lac Street', '8', 'HCMC', 'HCMC');

--11)
--Procedure để tạo sản phẩm
CREATE OR REPLACE PROCEDURE create_product(
    shop_id INTEGER, 
    image_url TEXT,
    type VARCHAR(100), 
    description TEXT, 
    variant_pic_text TEXT, 
    color VARCHAR(100), 
    size VARCHAR(10), 
    price DECIMAL(15,2), 
    stock_quantity INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    product_id INTEGER;
BEGIN
    -- ==== Validate inputs ====

    IF price < 0 THEN
        RAISE EXCEPTION 'Price cannot be negative: %', price;
    END IF;

    IF stock_quantity < 0 THEN
        RAISE EXCEPTION 'Stock quantity cannot be negative: %', stock_quantity;
    END IF;

    IF color IS NULL OR length(trim(color)) = 0 THEN
        RAISE EXCEPTION 'Color must not be empty.';
    END IF;

    IF size IS NULL OR length(trim(size)) = 0 THEN
        RAISE EXCEPTION 'Size must not be empty.';
    END IF;

    IF shop_id IS NULL THEN
        RAISE EXCEPTION 'Shop ID must not be NULL.';
    END IF;

    -- Optional: check if the Shop exists (depends if you want strict checking)
    -- If needed, SELECT 1 FROM SHOP WHERE ShopID = shop_id;

    -- ==== Insert into PRODUCT ====
    INSERT INTO PRODUCT ("Type", Description, ShopID)
    VALUES (type, description, shop_id)
    RETURNING ProductID INTO product_id;

    -- ==== Insert into PRODUCT_IMAGES ====
    INSERT INTO PRODUCT_IMAGES (ProductID, Images)
    VALUES (product_id, image_url);

    -- ==== Insert into PRODUCT_VARIANT ====
    INSERT INTO PRODUCT_VARIANT (ProductID, Color, "Size", Price, StockQuantity, Image)
    VALUES (product_id, color, size, price, stock_quantity, variant_pic_text);

END;
$$;
--CALL create_product(1, 'https://lados.vn/wp-content/uploads/2024/07/474ab2a1-48db-46f0-8e62-9eb32fcf92c7-1.jpeg',
--'ao', 'Ao so mi nam thoi trang hang quoc', 
--'https://lados.vn/wp-content/uploads/2024/07/474ab2a1-48db-46f0-8e62-9eb32fcf92c7-1.jpeg', 'Black','M', 199000,50);


--12)
-- Procedure để tạo thêm các biến thể của sản phẩm (product variant)
CREATE OR REPLACE PROCEDURE update_product_func(
    product_id INTEGER, 
    new_color VARCHAR(100), 
    new_size VARCHAR(10), 
    new_price DECIMAL(15,2), 
    new_stock_quantity INTEGER,
    new_pic TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- ==== Validate inputs ====

    IF product_id IS NULL THEN
        RAISE EXCEPTION 'Product ID cannot be NULL.';
    END IF;

    IF new_color IS NULL OR length(trim(new_color)) = 0 THEN
        RAISE EXCEPTION 'Color must not be empty.';
    END IF;

    IF new_size IS NULL OR length(trim(new_size)) = 0 THEN
        RAISE EXCEPTION 'Size must not be empty.';
    END IF;

    IF new_price < 0 THEN
        RAISE EXCEPTION 'Price cannot be negative: %', new_price;
    END IF;

    IF new_stock_quantity < 0 THEN
        RAISE EXCEPTION 'Stock quantity cannot be negative: %', new_stock_quantity;
    END IF;

    -- Optional: Check if the product_id exists in PRODUCT table
    IF NOT EXISTS (SELECT 1 FROM PRODUCT WHERE ProductID = product_id) THEN
        RAISE EXCEPTION 'ProductID % does not exist.', product_id;
    END IF;

    -- ==== Perform INSERT ====
    INSERT INTO PRODUCT_VARIANT (ProductID, Color, "Size", Price, StockQuantity, Image) 
    VALUES (product_id, new_color, new_size, new_price, new_stock_quantity, new_pic);

END;
$$;
--CALL update_product_func(6, 'White', 'M', 299000, 50, 
--'https://ngockhanhstore.vn/wp-content/uploads/2024/07/ao-so-mi-dior-nam-mau-trang-hoc-tiet-in-logo-2.jpg');

--13)
--Procedure để người bán hàng thay đổi product variant
CREATE OR REPLACE PROCEDURE modify_product_func(
    product_id INTEGER, 
    same_color VARCHAR(100), 
    size VARCHAR(10), 
    modified_quantity INTEGER, 
    modified_price DECIMAL(15,2)
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check if quantity and price are non-negative
    IF modified_quantity < 0 THEN
        RAISE EXCEPTION 'Stock quantity cannot be negative: %', modified_quantity;
    END IF;
    
    IF modified_price < 0 THEN
        RAISE EXCEPTION 'Price cannot be negative: %', modified_price;
    END IF;

    -- If passed validation, then update
    UPDATE PRODUCT_VARIANT
    SET StockQuantity = modified_quantity,
        Price = modified_price
    WHERE ProductID = product_id
      AND Color = same_color
      AND "Size" = size;
END;
$$;
--CALL modify_product_func(6, 'white', 'M', 321000,1000)


--14)
--Procedure để người bán hàng xóa 1 biến thể của sản phẩm
CREATE OR REPLACE PROCEDURE delete_variant_func(
    product_id INTEGER, 
    old_color VARCHAR(100), 
    size VARCHAR(10)
)
AS $$
BEGIN
    -- Xóa biến thể khỏi bảng PRODUCT_VARIANT
    DELETE FROM PRODUCT_VARIANT 
    WHERE ProductID = product_id AND Color = old_color AND "Size" = size;
	-- Xoá Sản Phẩm nếu không còn biến thể nào 
	IF NOT EXISTS (
        SELECT 1
        FROM PRODUCT_VARIANT
        WHERE ProductID = product_id
    ) THEN
        DELETE FROM PRODUCT
        WHERE ProductID = product_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

