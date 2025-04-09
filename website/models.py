from . import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'USER'

    UserID = db.Column(db.Integer, primary_key=True)
    Password = db.Column(db.Text, nullable=False)
    FirstName = db.Column(db.Text, nullable=False)
    LastName = db.Column(db.Text, nullable=False)
    CreateDate = db.Column(db.DateTime, default=datetime.utcnow)
    UpdateDate = db.Column(db.DateTime)
    Email = db.Column(db.Text, unique=True)
    DateOfBirth = db.Column(db.Date)

    def __repr__(self):
        return f'<User {self.Email}>'

class UserPhone(db.Model):
    __tablename__ = 'USER_PHONE'

    UserID = db.Column(db.Integer, db.ForeignKey('USER.UserID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    PhoneNumber = db.Column(db.String(15), primary_key=True)

    user = db.relationship('User', backref='phones')

class VoucherCreator(db.Model):
    __tablename__ = 'VOUCHER_CREATOR'

    CreatorID = db.Column(db.Integer, primary_key=True)

class Admin(db.Model):
    __tablename__ = 'ADMIN'

    UserID = db.Column(db.Integer, db.ForeignKey('USER.UserID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    StartDate = db.Column(db.Date, nullable=False)
    CreatorID = db.Column(db.Integer, db.ForeignKey('VOUCHER_CREATOR.CreatorID'))

    user = db.relationship('User', backref='admin')
    creator = db.relationship('VoucherCreator', backref='admins')

class NonAdmin(db.Model):
    __tablename__ = 'NonAdmin'

    UserID = db.Column(db.Integer, db.ForeignKey('USER.UserID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    user = db.relationship('User', backref='non_admin')

class Vender(db.Model):
    __tablename__ = 'VENDER'

    UserID = db.Column(db.Integer, db.ForeignKey('NonAdmin.UserID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Income = db.Column(db.Numeric(15, 2))
    TaxNumber = db.Column(db.String(20))
    CreatorID = db.Column(db.Integer, db.ForeignKey('VOUCHER_CREATOR.CreatorID'))

    non_admin = db.relationship('NonAdmin', backref='vender')
    creator = db.relationship('VoucherCreator', backref='venders')

class VendeeAndCart(db.Model):
    __tablename__ = 'VENDEE_AND_CART'

    UserID = db.Column(db.Integer, db.ForeignKey('NonAdmin.UserID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    TotalSpending = db.Column(db.Numeric(15, 2))
    CartID = db.Column(db.Integer, unique=True)

    non_admin = db.relationship('NonAdmin', backref='vendee_and_cart')

class VendeeAddress(db.Model):
    __tablename__ = 'VENDEE_ADDRESS'

    UserID = db.Column(db.Integer, db.ForeignKey('VENDEE_AND_CART.UserID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    IsDefault = db.Column(db.Boolean, nullable=False, default=False)
    HomeNumber = db.Column(db.String(200), primary_key=True)
    Street = db.Column(db.String(255), primary_key=True)
    District = db.Column(db.String(255), primary_key=True)
    City = db.Column(db.String(255), primary_key=True)
    Province = db.Column(db.String(255), primary_key=True)

    vendee = db.relationship('VendeeAndCart', backref='addresses')

class DeliverStaff(db.Model):
    __tablename__ = 'DELIVER_STAFF'

    UserID = db.Column(db.Integer, db.ForeignKey('NonAdmin.UserID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    TypeVehicle = db.Column(db.String(100))
    LicensePlate = db.Column(db.String(20))

    non_admin = db.relationship('NonAdmin', backref='deliver_staff')

class DeliverStaffAssignedArea(db.Model):
    __tablename__ = 'DELIVER_STAFF_ASSIGNED_AREA'

    UserID = db.Column(db.Integer, db.ForeignKey('DELIVER_STAFF.UserID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    District = db.Column(db.String(255), primary_key=True)
    City = db.Column(db.String(255), primary_key=True)
    Province = db.Column(db.String(255), primary_key=True)

    deliver_staff = db.relationship('DeliverStaff', backref='assigned_areas')

class Voucher(db.Model):
    __tablename__ = 'VOUCHER'

    VoucherID = db.Column(db.Integer, primary_key=True)
    Type = db.Column(db.String(100))
    Value = db.Column(db.Numeric(15, 2))
    ValueType = db.Column(db.String(50))
    MaxDiscount = db.Column(db.Numeric(15, 2))
    MinOrderValue = db.Column(db.Numeric(15, 2))
    CreatorID = db.Column(db.Integer, db.ForeignKey('VOUCHER_CREATOR.CreatorID'))

    creator = db.relationship('VoucherCreator', backref='vouchers')

class Shop(db.Model):
    __tablename__ = 'SHOP'

    ShopID = db.Column(db.Integer, primary_key=True)
    Address = db.Column(db.String(255))
    PhoneNumber = db.Column(db.String(15), nullable=False)
    Name = db.Column(db.String(100))
    UserID = db.Column(db.Integer, db.ForeignKey('VENDER.UserID'))

    vender = db.relationship('Vender', backref='shops')

class Product(db.Model):
    __tablename__ = 'PRODUCT'

    ProductID = db.Column(db.Integer, primary_key=True)
    Type = db.Column(db.String(100))
    Description = db.Column(db.Text)
    ShopID = db.Column(db.Integer, db.ForeignKey('SHOP.ShopID'))

    shop = db.relationship('Shop', backref='products')

class ProductImages(db.Model):
    __tablename__ = 'PRODUCT_IMAGES'

    ProductID = db.Column(db.Integer, db.ForeignKey('PRODUCT.ProductID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Images = db.Column(db.Text, primary_key=True)

    product = db.relationship('Product', backref='images')

class VoucherApplyProduct(db.Model):
    __tablename__ = 'VOUCHER_APPLY_PRODUCT'

    VoucherID = db.Column(db.Integer, db.ForeignKey('VOUCHER.VoucherID'), primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('PRODUCT.ProductID'), primary_key=True)

    voucher = db.relationship('Voucher', backref='voucher_apply_products')
    product = db.relationship('Product', backref='voucher_apply_products')

class ProductVariant(db.Model):
    __tablename__ = 'PRODUCT_VARIANT'

    ProductID = db.Column(db.Integer, db.ForeignKey('PRODUCT.ProductID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Color = db.Column(db.String(100), primary_key=True)
    Size = db.Column(db.String(10), primary_key=True)
    Price = db.Column(db.Numeric(15, 2))
    StockQuantity = db.Column(db.Integer)
    Image = db.Column(db.Text)

    product = db.relationship('Product', backref='variants')

class Order(db.Model):
    __tablename__ = 'ORDER'

    OrderID = db.Column(db.Integer, primary_key=True)
    ActualDeliverDate = db.Column(db.DateTime)
    OrderDate = db.Column(db.DateTime, default=datetime.utcnow)
    Status = db.Column(db.String(50))
    ExpectedDeliverDate = db.Column(db.DateTime)
    PaymentMethod = db.Column(db.String(50))
    TotalMoney = db.Column(db.Numeric(15, 2))
    TotalProduct = db.Column(db.Integer)
    HomeNumber = db.Column(db.String(200))
    Street = db.Column(db.String(255))
    District = db.Column(db.String(255))
    City = db.Column(db.String(255))
    Province = db.Column(db.String(255))
    Subtotal = db.Column(db.Numeric(15, 2))
    Promotion = db.Column(db.Numeric(15, 2))
    CartID = db.Column(db.Integer, db.ForeignKey('VENDEE_AND_CART.CartID'))
    ShipByID = db.Column(db.Integer, db.ForeignKey('DELIVER_STAFF.UserID'))

    cart = db.relationship('VendeeAndCart', backref='orders')
    deliver_staff = db.relationship('DeliverStaff', backref='orders')

class VoucherApplyOrder(db.Model):
    __tablename__ = 'VOUCHER_APPLY_ORDER'

    VoucherID = db.Column(db.Integer, db.ForeignKey('VOUCHER.VoucherID'), primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('ORDER.OrderID'), primary_key=True)

    voucher = db.relationship('Voucher', backref='voucher_apply_orders')
    order = db.relationship('Order', backref='voucher_apply_orders')

class OrderContainProductVariant(db.Model):
    __tablename__ = 'ORDER_CONTAIN_PRODUCT_VARIANT'

    ProductID = db.Column(db.Integer, primary_key=True)
    Color = db.Column(db.String(100), primary_key=True)
    Size = db.Column(db.String(10), primary_key=True)
    OrderID = db.Column(db.Integer, db.ForeignKey('ORDER.OrderID'), primary_key=True)
    Quantity = db.Column(db.Integer)

    order = db.relationship('Order', backref='order_contains')
    product_variant = db.relationship('ProductVariant',
                                     primaryjoin="and_(OrderContainProductVariant.ProductID==ProductVariant.ProductID, "
                                                 "OrderContainProductVariant.Color==ProductVariant.Color, "
                                                 "OrderContainProductVariant.Size==ProductVariant.Size)")

class CartContainProductVariant(db.Model):
    __tablename__ = 'CART_CONTAIN_PRODUCT_VARIANT'

    ProductID = db.Column(db.Integer, primary_key=True)
    Color = db.Column(db.String(100), primary_key=True)
    Size = db.Column(db.String(10), primary_key=True)
    CartID = db.Column(db.Integer, db.ForeignKey('VENDEE_AND_CART.CartID'), primary_key=True)
    Quantity = db.Column(db.Integer)
    TotalMoney = db.Column(db.Numeric(15, 2))

    cart = db.relationship('VendeeAndCart', backref='cart_contains')
    product_variant = db.relationship('ProductVariant',
                                     primaryjoin="and_(CartContainProductVariant.ProductID==ProductVariant.ProductID, "
                                                 "CartContainProductVariant.Color==ProductVariant.Color, "
                                                 "CartContainProductVariant.Size==ProductVariant.Size)")

class Review(db.Model):
    __tablename__ = 'REVIEW'

    ReviewID = db.Column(db.Integer, primary_key=True)
    Rate = db.Column(db.Integer)
    Description = db.Column(db.Text)

class ReviewImages(db.Model):
    __tablename__ = 'REVIEW_IMAGES'

    ReviewID = db.Column(db.Integer, db.ForeignKey('REVIEW.ReviewID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Images = db.Column(db.Text, primary_key=True)

    review = db.relationship('Review', backref='images')

class ReviewWritten(db.Model):
    __tablename__ = 'REVIEW_WRITTEN'

    ReviewID = db.Column(db.Integer, db.ForeignKey('REVIEW.ReviewID'), primary_key=True)
    ProductID = db.Column(db.Integer, primary_key=True)
    Color = db.Column(db.String(100), primary_key=True)
    Size = db.Column(db.String(50), primary_key=True)
    ReviewerID = db.Column(db.Integer, db.ForeignKey('VENDEE_AND_CART.UserID'))

    review = db.relationship('Review', backref='written_reviews')
    reviewer = db.relationship('VendeeAndCart', backref='reviews')
    product_variant = db.relationship('ProductVariant',
                                     primaryjoin="and_(ReviewWritten.ProductID==ProductVariant.ProductID, "
                                                 "ReviewWritten.Color==ProductVariant.Color, "
                                                 "ReviewWritten.Size==ProductVariant.Size)")