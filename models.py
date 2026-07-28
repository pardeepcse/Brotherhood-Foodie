from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


# ================= USER =================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default="customer")

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    orders = db.relationship(
        "Order",
        back_populates="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.email}>"

# ================= CATEGORY =================

class Category(db.Model):

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)

    description = db.Column(db.Text)

    image = db.Column(db.String(200))

    foods = db.relationship(
        "Food",
        backref="category",
        cascade="all, delete",
        lazy=True
    )

    def __repr__(self):
     return f"<Category {self.name}>"

# ================= FOOD =================

class Food(db.Model):
    __tablename__ = "foods"

    id = db.Column(db.Integer, primary_key=True)

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )

    name = db.Column(db.String(100), nullable=False)

    description = db.Column(db.Text)

    price = db.Column(db.Float, nullable=False)

    discount = db.Column(db.Integer, default=0)

    image = db.Column(db.String(200))

    available = db.Column(db.Boolean, default=True)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    def discounted_price(self):
        return self.price - (self.price * self.discount / 100)

    def average_rating(self):

        if not self.reviews:
            return 0

        total = sum(review.rating for review in self.reviews)

        return round(total / len(self.reviews), 1)

    order_items = db.relationship(
        "OrderItem",
        back_populates="food",
        lazy=True,
    )

    def __repr__(self):
        return f"<Food {self.name}>"

# ================= Order====================
class Order(db.Model):

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)

    customer = db.Column(db.String(100), nullable=False)

    phone = db.Column(db.String(20), nullable=False)

    address = db.Column(db.Text, nullable=False)

    total = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(30), default="Pending")

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="orders"
    )

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Order {self.id}>"

# ============order items===============
class OrderItem(db.Model):

    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False
    )

    food_id = db.Column(
        db.Integer,
        db.ForeignKey("foods.id"),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        default=1
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    order = db.relationship(
        "Order",
        back_populates="items"
    )

    food = db.relationship(
        "Food",
        back_populates="order_items"
    )



# ================= REVIEW =================

class Review(db.Model):

    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)

    food_id = db.Column(
        db.Integer,
        db.ForeignKey("foods.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    comment = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    food = db.relationship(
        "Food",
        backref="reviews"
    )

    user = db.relationship(
        "User",
        backref="reviews"
    )

# ===============Gallery===========================

class Gallery(db.Model):

    __tablename__ = "gallery"

    id = db.Column(db.Integer, primary_key=True)

    image = db.Column(db.String(200), nullable=False)

    title = db.Column(db.String(100))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

# ======================Contact======================================

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=False
    )

    subject = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    admin_reply = db.Column(db.Text)
    replied = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)