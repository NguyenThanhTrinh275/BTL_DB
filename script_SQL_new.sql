-- 0) Drop in correct dependency order
DROP TABLE IF EXISTS
  REVIEW_WRITTEN,
  REVIEW_IMAGES,
  REVIEW,
  CART_CONTAIN_PRODUCT_VARIANT,
  ORDER_CONTAIN_PRODUCT_VARIANT,
  VOUCHER_APPLY_ORDER,
  VOUCHER_APPLY_PRODUCT,
  "ORDER",
  PRODUCT_VARIANT,
  PRODUCT_IMAGES,
  PRODUCT,
  SHOP,
  VOUCHER,
  DELIVER_STAFF_ASSIGNED_AREA,
  DELIVER_STAFF,
  VENDEE_ADDRESS,
  VENDEE_AND_CART,
  VENDER,
  NonAdmin,
  "ADMIN",
  VOUCHER_CREATOR,
  USER_PHONE,
  "USER"
CASCADE;

DROP SEQUENCE IF EXISTS VOUCHER_CREATOR_SEQ;

-- 1) USER
CREATE TABLE "USER" (
  UserID       SERIAL    PRIMARY KEY,
  "Password"   TEXT      NOT NULL,
  FirstName    TEXT      NOT NULL,
  LastName     TEXT      NOT NULL,
  CreateDate   TIMESTAMP NOT NULL DEFAULT now(),
  UpdateDate   TIMESTAMP,
  Email        TEXT      UNIQUE,
  DateOfBirth  DATE
);

-- non admin, vender, 1-4
INSERT INTO "USER"( "Password", FirstName, LastName, Email, DateOfBirth ) VALUES
('123','Hai','Nguyen','hai.ng@example.com','1980-02-10'),
('123','Lan','Tran','lan.tran@example.com','1985-06-15'),
('123','Minh','Le','minh.le@example.com','1990-09-20'),
('123','Anh','Pham','anh.pham@example.com','1992-12-05');

-- admin, to fulfill only 5-8
INSERT INTO "USER"( "Password", FirstName, LastName, Email, DateOfBirth ) VALUES
('123','Admin1','Nguyen','Admin1.ng@example.com','1980-02-10'),
('132','Admin2','Tran','Admin2.tran@example.com','1985-06-15'),
('123','Admin3','Le','Admin3.le@example.com','1990-09-20'),
('123','Admin4','Pham','Admin4.pham@example.com','1992-12-05');

-- non admin, vendee 9-12
INSERT INTO "USER"( "Password", FirstName, LastName, Email, DateOfBirth ) VALUES
('123','Haib','Nguyen','haib.ng@example.com','1980-02-10'),
('123','Lanb','Tran','lanb.tran@example.com','1985-06-15'),
('123','Minhb','Le','minhb.le@example.com','1990-09-20'),
('123','Anhb','Pham','anhb.pham@example.com','1992-12-05');

-- 2) USER_PHONE
CREATE TABLE USER_PHONE (
  UserID      INTEGER REFERENCES "USER"(UserID) ON DELETE CASCADE ON UPDATE CASCADE,
  PhoneNumber VARCHAR(15) NOT NULL
    CHECK ( length(PhoneNumber)=10 AND PhoneNumber ~ '^[0-9]+$' ),
  PRIMARY KEY (UserID,PhoneNumber)
);

INSERT INTO USER_PHONE(UserID,PhoneNumber) VALUES
(1,'0912345678'),
(1,'0987654321'),
(2,'0933334444'),
(3,'0900001111'),
(4,'0900001112'),
(5,'0912345678'),
(6,'0987654321'),
(7,'0933334444'),
(8,'0900001111'),
(9,'0900001112'),
(10,'0987654321'),
(11,'0933334444'),
(12,'0900001111'),
(12,'0900001112');
-- 3) VOUCHER_CREATOR
-- Tạo sequence tự động tăng số
CREATE SEQUENCE VOUCHER_CREATOR_SEQ
START 1
INCREMENT 1;

-- Tạo bảng với khóa chính có tiền tố VCC
CREATE TABLE VOUCHER_CREATOR (
  CreatorID TEXT PRIMARY KEY DEFAULT ('VCC' || LPAD(NEXTVAL('VOUCHER_CREATOR_SEQ')::TEXT, 4, '0'))
);

INSERT INTO VOUCHER_CREATOR DEFAULT VALUES;
INSERT INTO VOUCHER_CREATOR DEFAULT VALUES;
INSERT INTO VOUCHER_CREATOR DEFAULT VALUES;
INSERT INTO VOUCHER_CREATOR DEFAULT VALUES;

-- 4) ADMIN
CREATE TABLE "ADMIN" (
  UserID    INTEGER PRIMARY KEY 
               REFERENCES "USER"(UserID) ON DELETE CASCADE ON UPDATE CASCADE,
  StartDate DATE    NOT NULL,
  CreatorID TEXT REFERENCES VOUCHER_CREATOR(CreatorID)
);
INSERT INTO "ADMIN"(UserID,StartDate,CreatorID) VALUES
(5,'2023-01-01','VCC0001'),
(6,'2023-04-15','VCC0002'),
(7,'2023-07-20','VCC0003'),
(8,'2023-10-05','VCC0004');

-- 5) NonAdmin
CREATE TABLE NonAdmin (
  UserID INTEGER PRIMARY KEY 
    REFERENCES "USER"(UserID) ON DELETE CASCADE ON UPDATE CASCADE
);
INSERT INTO NonAdmin(UserID) VALUES (1),(2),(3),(4),(9),(10),(11),(12);

-- 6) VENDER
CREATE TABLE VENDER (
  UserID    INTEGER PRIMARY KEY
                REFERENCES NonAdmin(UserID) ON DELETE CASCADE ON UPDATE CASCADE,
  Income    DECIMAL(15,2),
  TaxNumber CHAR(20),
  CreatorID TEXT    REFERENCES VOUCHER_CREATOR(CreatorID)
);
INSERT INTO VENDER(UserID,Income,TaxNumber,CreatorID) VALUES
(1, 1200000,'TAX0001','VCC0001'),
(2, 800000,'TAX0002','VCC0002'),
(3, 500000,'TAX0003','VCC0003'),
(4, 1500000,'TAX0004','VCC0004');

-- 7) VENDEE_AND_CART
CREATE TABLE VENDEE_AND_CART (
  UserID        INTEGER PRIMARY KEY
                  REFERENCES NonAdmin(UserID) ON DELETE CASCADE ON UPDATE CASCADE,
  TotalSpending DECIMAL(15,2),
  CartID        INTEGER UNIQUE
);

INSERT INTO VENDEE_AND_CART(UserID,TotalSpending,CartID) VALUES
(1, 250000, 1),
(2,  50000, 2),
(3, 125000, 3),
(4,  75000, 4),
(9, 250000, 9),
(10,  50000, 10),
(11, 125000, 11),
(12,  75000, 12);

-- 8) VENDEE_ADDRESS
CREATE TABLE VENDEE_ADDRESS (
  UserID     INTEGER
                REFERENCES VENDEE_AND_CART(UserID) ON DELETE CASCADE ON UPDATE CASCADE,
  IsDefault  BOOLEAN NOT NULL DEFAULT FALSE,
  HomeNumber VARCHAR(200) NOT NULL,
  Street     VARCHAR(255) NOT NULL,
  District   VARCHAR(255) NOT NULL,
  City       VARCHAR(255) NOT NULL,
  Province   VARCHAR(255) NOT NULL,
  PRIMARY KEY (UserID,HomeNumber,Street,District,City,Province)
);
INSERT INTO VENDEE_ADDRESS VALUES
(9,TRUE,'12','Alpha St','District 1','HCMC','HCMC'),
(10,TRUE,'34','Beta Rd','District 2','HCMC','HCMC'),
(11,TRUE,'56','Gamma Ave','District 3','HCMC','HCMC'),
(12,TRUE,'78','Delta Blvd','District 4','HCMC','HCMC');

-- 12) SHOP
CREATE TABLE SHOP (
  ShopID      SERIAL PRIMARY KEY,
  Address     VARCHAR(255),
  PhoneNumber VARCHAR(15) NOT NULL 
                CHECK(length(PhoneNumber)=10 AND PhoneNumber ~ '^[0-9]+$'),
  "Name"      VARCHAR(100),
  UserID      INTEGER REFERENCES VENDER(UserID)
);
INSERT INTO SHOP(Address,PhoneNumber,"Name",UserID) VALUES
('Addr1','0900000001','Shop1',1),
('Addr2','0900000002','Shop2',2),
('Addr3','0900000003','Shop3',3),
('Addr4','0900000004','Shop4',4);

-- 13) PRODUCT
CREATE TABLE PRODUCT (
  ProductID   SERIAL PRIMARY KEY,
  "Type"      VARCHAR(100),
  Description TEXT,
  ShopID      INTEGER REFERENCES SHOP(ShopID)
);

-- 14) PRODUCT_IMAGES
CREATE TABLE PRODUCT_IMAGES (
  ProductID INTEGER REFERENCES PRODUCT(ProductID) ON DELETE CASCADE ON UPDATE CASCADE,
  Images    TEXT,
  PRIMARY KEY (ProductID,Images)
);
select * from product
INSERT INTO PRODUCT("Type",Description,ShopID) VALUES
  ('ao','T-Shirt 100% cotton, unisex',1),
  ('quan',  'Quần Jean slim fit denim',   1),
  ('ao', 'Áo khoác chống gió',      1),
  ('pk',  'Summer dress',     1);


INSERT INTO PRODUCT("Type", Description, ShopID) VALUES
('ao', 'Áo thun cổ tròn cotton', 1),
('quan', 'Quần short kaki nam', 2),
('pk', 'Mũ lưỡi trai unisex', 3),
('ao', 'Áo sơ mi công sở nam', 4),
('quan', 'Quần tây âu nam', 1),
('ao', 'Áo polo thể thao', 2),
('pk', 'Túi xách da nữ', 3),
('ao', 'Áo khoác bomber nam', 4),
('quan', 'Quần jogger thể thao', 1),
('pk', 'Balo laptop chống sốc', 2),
('ao', 'Áo len cổ lọ nam', 3),
('quan', 'Quần jeans ống suông', 4),
('pk', 'Ví da nam cao cấp', 1),
('ao', 'Áo hoodie in hình', 2),
('quan', 'Quần jeans rách gối', 3),
('pk', 'Kính râm thời trang', 4),
('ao', 'Áo thun dài tay unisex', 1),
('quan', 'Quần kaki ống đứng', 2),
('pk', 'Thắt lưng da nam', 3),
('ao', 'Áo sơ mi kẻ caro', 4);

select * from product_images
INSERT INTO PRODUCT_IMAGES VALUES
(1,'https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lvn4mzmumz5l96'),
(1,'https://down-vn.img.susercontent.com/file/vn-11134208-7r98o-lwy5dl2zcusb36'),
(2,'https://product.hstatic.net/1000321597/product/2_b2e8a807e553427b9b435a7150b2b5f2_master.png'),
(3,'https://media.glamour.com/photos/6660c7c76276ab5606da12f2/1:1/w_5462,h_5462,c_limit/1521685967');

INSERT INTO PRODUCT_IMAGES VALUES
(4,'abc')

INSERT INTO PRODUCT_IMAGES(ProductID, Images) VALUES
-- Type: ao
(5, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/sub/vngoods_424873_sub7_3x4.jpg?width=423'),
(7, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/sub/vngoods_424873_sub7_3x4.jpg?width=423'),
(9, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/sub/vngoods_424873_sub7_3x4.jpg?width=423'),
(11, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/sub/vngoods_424873_sub7_3x4.jpg?width=423'),
(15, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/sub/vngoods_424873_sub7_3x4.jpg?width=423'),
(18, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/sub/vngoods_424873_sub7_3x4.jpg?width=423'),
(21, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/sub/vngoods_424873_sub7_3x4.jpg?width=423'),
-- Type: quan
(6, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/455533/item/vngoods_57_455533_3x4.jpg?width=369'),
(8, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/455533/item/vngoods_57_455533_3x4.jpg?width=369'),
(10, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/455533/item/vngoods_57_455533_3x4.jpg?width=369'),
(12, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/455533/item/vngoods_57_455533_3x4.jpg?width=369'),
(16, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/455533/item/vngoods_57_455533_3x4.jpg?width=369'),
(19, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/455533/item/vngoods_57_455533_3x4.jpg?width=369'),
(22, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/455533/item/vngoods_57_455533_3x4.jpg?width=369'),
-- Type: pk
(13, 'https://encrypted-tbn3.gstatic.com/shopping?q=tbn9GcQZMfkda8sIBoSB4YoxXvdxTlRDrLsdBxYQHQEMF5WOT4HUr7o32rcB6yxbGw7XtdSdtmbj2PCLGq5Q03qUyKR6vW7guxT6H-RwHhAqiABklYcd5Jh0ZR3cXj1K5Pw_ZBB三大MFI&usqp=CAc'),
(14, 'https://encrypted-tbn3.gstatic.com/shopping?q=tbn9GcQZMfkda8sIBoSB4YoxXvdxTlRDrLsdBxYQHQEMF5WOT4HUr7o32rcB6yxbGw7XtdSdtmbj2PCLGq5Q03qUyKR6vW7guxT6H-RwHhAqiABklYcd5Jh0ZR3cXj1K5Pw_ZBBuZmAIDMFI&usqp=CAc'),
(17, 'https://encrypted-tbn3.gstatic.com/shopping?q=tbn9GcQZMfkda8sIBoSB4YoxXvdxTlRDrLsdBxYQHQEMF5WOT4HUr7o32rcB6yxbGw7XtdSdtmbj2PCLGq5Q03qUyKR6vW7guxT6H-RwHhAqiABklYcd5Jh0ZR3cXj1K5Pw_ZBBuZmAIDMFI&usqp=CAc'),
(20, 'https://encrypted-tbn3.gstatic.com/shopping?q=tbn9GcQZMfkda8sIBoSB4YoxXvdxTlRDrLsdBxYQHQEMF5WOT4HUr7o32rcB6yxbGw7XtdSdtmbj2PCLGq5Q03qUyKR6vW7guxT6H-RwHhAqiABklYcd5Jh0ZR3cXj1K5Pw_ZBBuZmAIDMFI&usqp=CAc'),
(23, 'https://encrypted-tbn3.gstatic.com/shopping?q=tbn9GcQZMfkda8sIBoSB4YoxXvdxTlRDrLsdBxYQHQEMF5WOT4HUr7o32rcB6yxbGw7XtdSdtmbj2PCLGq5Q03qUyKR6vW7guxT6H-RwHhAqiABklYcd5Jh0ZR3cXj1K5Pw_ZBBuZmAIDMFI&usqp=CAc'),
(24, 'https://encrypted-tbn3.gstatic.com/shopping?q=tbn9GcQZMfkda8sIBoSB4YoxXvdxTlRDrLsdBxYQHQEMF5WOT4HUr7o32rcB6yxbGw7XtdSdtmbj2PCLGq5Q03qUyKR6vW7guxT6H-RwHhAqiABklYcd5Jh0ZR3cXj1K5Pw_ZBBuZmAIDMFI&usqp=CAc');

-- four variants for those products
-- 16) PRODUCT_VARIANT
CREATE TABLE PRODUCT_VARIANT (
  ProductID     INTEGER,
  Color         VARCHAR(100),
  "Size"        VARCHAR(10),
  Price         DECIMAL(15,2),
  StockQuantity INTEGER,
  Image         TEXT,
  PRIMARY KEY (ProductID,Color,"Size"),
  FOREIGN KEY (ProductID) REFERENCES PRODUCT(ProductID) ON DELETE CASCADE
);

INSERT INTO PRODUCT_VARIANT(ProductID,Color,"Size",Price,StockQuantity,Image) VALUES
  (1,'White','S', 199000, 50,'https://m.media-amazon.com/images/I/61wwa6l9EBL._AC_UY1100_.jpg'),
  (1,'Black','M', 199000, 60,'https://m.media-amazon.com/images/I/51zIWA3uW9L._AC_SY780_.jpg'),
  (2,'Blue','32',499000, 40,'https://product.hstatic.net/1000270127/product/img_9694_224782ed8d964f18a94a181c7215bebf.jpg'),
  (3,'Red','L', 899000, 30,'https://m.media-amazon.com/images/I/71GXHWIwnFL._AC_UY1100_.jpg');

INSERT INTO PRODUCT_VARIANT(ProductID,Color,"Size",Price,StockQuantity,Image) VALUES
(4,'Green','L',299000, 40, '123');


INSERT INTO PRODUCT_VARIANT(ProductID, Color, "Size", Price, StockQuantity, Image) VALUES
-- Type: ao (ProductID: 5, 7, 9, 11, 15, 18 inflame, 21)
(5, 'White', 'S', 199000, 50, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(5, 'Black', 'M', 199000, 60, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(7, 'Blue', 'M', 299000, 45, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(7, 'Grey', 'L', 299000, 55, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(9, 'Red', 'S', 249000, 40, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(9, 'Navy', 'M', 249000, 50, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(11, 'White', 'L', 399000, 35, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(11, 'Black', 'XL', 399000, 45, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(15, 'Green', 'M', 349000, 50, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(15, 'Blue', 'S', 349000, 60, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(18, 'Grey', 'M', 299000, 40, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(18, 'Red', 'L', 299000, 50, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(21, 'Navy', 'S', 249000, 45, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
(21, 'White', 'M', 249000, 55, 'https://image.uniqlo.com/UQ/ST3/vn/imagesgoods/424873/item/vngoods_61_424873_3x4.jpg?width=369'),
-- Type: quan (ProductID: 6, 8, 10, 12, 16, 19, 22)
(6, 'Khaki', '30', 499000, 40, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(6, 'Black', '32', 499000, 50, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(8, 'Navy', '32', 599000, 35, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(8, 'Grey', '34', 599000, 45, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(10, 'Blue', '30', 499000, 50, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(10, 'Black', '32', 499000, 60, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(12, 'Khaki', '32', 549000, 40, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(12, 'Navy', '34', 549000, 50, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(16, 'Blue', '30', 499000, 45, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(16, 'Grey', '32', 499000, 55, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(19, 'Black', '34', 599000, 40, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(19, 'Khaki', '32', 599000, 50, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlw ءltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(22, 'Blue', '32', 549000, 45, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
(22, 'Black', '34', 549000, 55, 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn9GcSlSWAXEYc8nQuU7bP7Ttadly1MMjaIXk2vTaB--ZI-ZO0qmY85XGgHCrzrKLRacsfySahahxc5Mr6ZT_aVlwltW4YdtZvXM3ZcFv85_jxmqU4uqzfq8-i8l3snqZMN4EVkuzVTkUw&usqp=CAc'),
-- Type: pk (ProductID: 13, 14, 17, 20, 23, 24)
(13, 'Brown', 'One Size', 199000, 60, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(13, 'Black', 'One Size', 199000, 50, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(14, 'Beige', 'One Size', 299000, 45, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(14, 'Black', 'One Size', 299000, 55, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(17, 'Blue', 'One Size', 249000, 40, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(17, 'Grey', 'One Size', 249000, 50, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(20, 'Brown', 'One Size', 199000, 60, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(20, 'Black', 'One Size', 199000, 50, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(23, 'Beige', 'One Size', 299000, 45, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(23, 'Blue', 'One Size', 299000, 55, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(24, 'Black', 'One Size', 249000, 40, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp'),
(24, 'Grey', 'One Size', 249000, 50, 'https://salt.tikicdn.com/cache/750x750/ts/product/f6/58/20/50991740efae6d4f58c91d89ca527a2d.jpg.webp');

-- 17) "ORDER"
CREATE TABLE "ORDER" (
  OrderID           SERIAL   PRIMARY KEY,
  ActualDeliverDate TIMESTAMP,
  OrderDate         TIMESTAMP DEFAULT now(),
  Status            VARCHAR(50),
  ExpectedDeliverDate TIMESTAMP,
  PaymentMethod     VARCHAR(50),
  TotalMoney        DECIMAL(15,2),
  TotalProduct      INTEGER,
  HomeNumber        VARCHAR(200),
  Street            VARCHAR(255),
  District          VARCHAR(255),
  City              VARCHAR(255),
  Province          VARCHAR(255),
  Subtotal          DECIMAL(15,2),
  Promotion         DECIMAL(15,2),
  CartID            INTEGER  REFERENCES VENDEE_AND_CART(CartID)
);

-- Select * from "ORDER"
INSERT INTO "ORDER"(Status,TotalMoney,TotalProduct,HomeNumber,Street,District,City,Province,CartID)
VALUES
('NEW',100000,1,'12','St1','D1','HCMC','HCMC',9),
('PAID',200000,2,'34','St2','D2','HCMC','HCMC',10),
('DONE',150000,1,'56','St3','D3','HCMC','HCMC',11),
('CANC', 50000,1,'78','St4','D4','HCMC','HCMC',12);
-- SELECT * FROM VENDEE_AND_CART WHERE CartID = 9;

CREATE TABLE ORDER_CONTAIN_PRODUCT_VARIANT (
  ProductID INTEGER,
  Color     VARCHAR(100),
  "Size"    VARCHAR(10),
  OrderID   INTEGER REFERENCES "ORDER"(OrderID),
  Quantity  INTEGER,
  PRIMARY KEY (ProductID,Color,"Size",OrderID),
  FOREIGN KEY (ProductID,Color,"Size")
    REFERENCES PRODUCT_VARIANT(ProductID,Color,"Size")
);
-- Select * from ORDER_CONTAIN_PRODUCT_VARIANT

INSERT INTO ORDER_CONTAIN_PRODUCT_VARIANT VALUES
(1,'White','S',1,1),
(1,'Black','M',2,2),
(2,'Blue','32',3,1),
(3,'Red','L',4,1);

-- 20) CART_CONTAIN_PRODUCT_VARIANT
CREATE TABLE CART_CONTAIN_PRODUCT_VARIANT (
  ProductID  INTEGER,
  Color      VARCHAR(100),
  "Size"     VARCHAR(10),
  CartID     INTEGER REFERENCES VENDEE_AND_CART(CartID),
  Quantity   INTEGER,
  TotalMoney DECIMAL(15,2),
  PRIMARY KEY (ProductID,Color,"Size",CartID),
  FOREIGN KEY (ProductID,Color,"Size")
    REFERENCES PRODUCT_VARIANT(ProductID,Color,"Size")
);

INSERT INTO CART_CONTAIN_PRODUCT_VARIANT VALUES
(1,'White','S',9,1,198000),
(1,'Black','M',9,2,398000),
(2,'Blue','32',10,1, 499000),
(3,'Red','L',11,1, 899000);

-- 21) REVIEW
CREATE TABLE REVIEW (
  ReviewID   SERIAL PRIMARY KEY,
  Rate       INTEGER CHECK (Rate BETWEEN 1 AND 5),
  Description TEXT
);
INSERT INTO REVIEW(Rate,Description) VALUES
(5,'Excellent'),(4,'Good'),(3,'Fair'),(2,'Poor');

-- 22) REVIEW_IMAGES
CREATE TABLE REVIEW_IMAGES (
  ReviewID INTEGER REFERENCES REVIEW(ReviewID) ON DELETE CASCADE ON UPDATE CASCADE,
  Images   TEXT,
  PRIMARY KEY (ReviewID,Images)
);
INSERT INTO REVIEW_IMAGES VALUES
(1,'https://m.media-amazon.com/images/I/51tRj8VDYiL._AC_UY1000_.jpg'),(1,'https://product.hstatic.net/1000270127/product/img_9238_c1996f4e789746f9a16a26c93f3ed845_master.jpg'),(2,'https://i.ebayimg.com/images/g/v-gAAOSwrBZnD8Qk/s-l1200.jpg'),(3,'https://assets.ajio.com/medias/sys_master/root/20230216/0OcU/63edce00f997dde6f4ab1372/-473Wx593H-410369162-3785-MODEL4.jpg');

-- 23) REVIEW_WRITTEN
CREATE TABLE REVIEW_WRITTEN (
  ReviewID   INTEGER REFERENCES REVIEW(ReviewID),
  ProductID  INTEGER,
  Color      VARCHAR(100),
  "Size"     VARCHAR(10),
  ReviewerID INTEGER REFERENCES VENDEE_AND_CART(UserID),
  PRIMARY KEY (ReviewID,ProductID,Color,"Size"),
  FOREIGN KEY (ProductID,Color,"Size")
    REFERENCES PRODUCT_VARIANT(ProductID,Color,"Size")
);
-- (1,'White','S',101,1,1000),
-- (1,'Black','M',101,2,2200),
-- (2,'Blue','32',102,1, 800),
-- (3,'Red','L',103,1, 500);
-- SELECT * FROM PRODUCT_VARIANT;
INSERT INTO REVIEW_WRITTEN(ReviewID,ProductID,Color,"Size",ReviewerID) VALUES
(1,1,'Black','M',9),
(1,1,'White','S',10),
(2,3,'Red','L',11),
(3,2,'Blue','32',12);







