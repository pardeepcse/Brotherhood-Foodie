from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    request,
    make_response
)

import os
import random

from datetime import datetime, timedelta

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from sqlalchemy import or_


from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer,
    
)

from flask_mail import Mail, Message
from config import Config

from utils import login_required, admin_required

from models import (
    db,
    User,
    Category,
    Food,
    Gallery,
    Review,
    Order,
    OrderItem,
    Contact
)

from forms import (
    RegisterForm,
    LoginForm,
    CategoryForm,
    FoodForm,
    CheckoutForm,
    ReviewForm,
    GalleryForm,
    ContactForm,
    ForgetPasswordForm,
    OTPForm,
    ResetPasswordForm
)


from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.middleware.proxy_fix import ProxyFix


# ==========================================
# Flask App Configuration
# ==========================================
app = Flask(__name__)


app.config.from_object(Config)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

db.init_app(app)

mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["UPLOAD_FOLDER"] = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "foods"
)

app.config["CATEGORY_UPLOAD_FOLDER"] = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "categories"
)

app.config["GALLERY_UPLOAD_FOLDER"] = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "gallery"
)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["CATEGORY_UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["GALLERY_UPLOAD_FOLDER"], exist_ok=True)


def create_default_admins():

    admins = [
        {
            "name": os.environ.get(
                "ADMIN1_NAME",
                "Admin One"
            ),
            "email": os.environ.get(
                "ADMIN1_EMAIL"
            ),
            "password": os.environ.get(
                "ADMIN1_PASSWORD"
            )
        },
        {
            "name": os.environ.get(
                "ADMIN2_NAME",
                "Admin Two"
            ),
            "email": os.environ.get(
                "ADMIN2_EMAIL"
            ),
            "password": os.environ.get(
                "ADMIN2_PASSWORD"
            )
        }
    ]

    for admin_data in admins:

        email = admin_data["email"]
        password = admin_data["password"]

        if not email or not password:
            continue

        email = email.strip().lower()

        user = User.query.filter_by(
            email=email
        ).first()

        # User exist nahi karta to create karo
        if user is None:

            user = User(
                name=admin_data["name"],
                email=email,
                role="admin"
            )

            user.set_password(password)

            db.session.add(user)

        else:
            # Existing user ko admin banao
            user.role = "admin"

    try:
        db.session.commit()

    except Exception as error:
        db.session.rollback()
        app.logger.error(
            f"Admin creation error: {error}"
        )


with app.app_context():
    db.create_all()
    create_default_admins()
@app.context_processor
def cart_count():

    cart = session.get("cart", {})

    total_items = sum(cart.values())

    return dict(cart_count=total_items)


# ==========================================
# Home Routes
# ==========================================

@app.route("/")
def home():

    foods = (
        Food.query
        .filter_by(available=True)
        .limit(6)
        .all()
    )

    categories = Category.query.all()

    gallery_images = (
        Gallery.query
        .order_by(Gallery.created_at.desc())
        .all()
    )

    # Latest customer reviews
    customer_reviews = (
        db.session.query(
            Review,
            User,
            Food
        )
        .join(
            User,
            Review.user_id == User.id
        )
        .join(
            Food,
            Review.food_id == Food.id
        )
        .order_by(
            Review.id.desc()
        )
        .limit(6)
        .all()
    )

    # Home page Contact form
    form = ContactForm()

    return render_template(
        "index.html",
        foods=foods,
        categories=categories,
        gallery_images=gallery_images,
        customer_reviews=customer_reviews,
        form=form
    )


@app.route("/menu")
def menu():
    foods = (
        Food.query
        .filter_by(available=True)
        .order_by(Food.id.desc())
        .all()
    )
    return render_template(
        "menu.html",
        foods=foods
    )

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/about-details")
def about_details():
    return render_template("about_details.html")



@app.route("/menu/category/<int:category_id>")
def category_menu(category_id):

    category = Category.query.get_or_404(category_id)

    foods = (
        Food.query
        .filter_by(
            category_id=category.id,
            available=True
        )
        .order_by(Food.id.desc())
        .all()
    )

    return render_template(
        "menu.html",
        foods=foods,
        category=category
    )

@app.route("/gallery")
def gallery():

    images = Gallery.query.order_by(
        Gallery.created_at.desc()
    ).all()

    return render_template(
        "gallery.html",
        images=images
    )



# ==========================================
# Authentication
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegisterForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        user = User(
            name=form.name.data.strip(),
            email=email
        )

        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration Error: {e}")
            flash("Something went wrong while creating your account.", "danger")
            return redirect(url_for("register"))

        login_user(user, remember=True)

        try:
            msg = Message(
                subject="Welcome to Brotherhood Foodie",
                sender=app.config["MAIL_DEFAULT_SENDER"],
                recipients=[user.email]
            )

            msg.body = f"""
        Hello {user.name},

        🎉 Your account has been created successfully.

        Welcome to Brotherhood Foodie!

        You can now login and place your favourite food orders.

        Thank You,
        Brotherhood Foodie Team
        """

            mail.send(msg)

        except Exception as e:
            app.logger.error(f"Welcome Email Error: {e}")

        flash("Registration Successful!", "success")

        return redirect(url_for("home"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("dashboard"))

    form = LoginForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):

            login_user(user, remember=True)

            flash("Login Successful!", "success")
            
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("home"))

        flash("Invalid Email or Password!", "danger")

    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():

    # Flask-Login user logout karega
    logout_user()

    # Cart aur OTP session data remove karo
    session.pop("cart", None)
    session.pop("reset_email", None)
    session.pop("reset_otp", None)
    session.pop("otp_expiry", None)
    session.pop("otp_verified", None)

    flash(
        "Logged Out Successfully.",
        "success"
    )

    return redirect(
        url_for("login")
    )
# ==========================================
# Customer Dashboard
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():
    user = db.session.get(User, current_user.id)
    

    my_orders = Order.query.filter_by(
        customer=user.name
    ).order_by(Order.id.desc()).all()

    my_reviews = Review.query.filter_by(
        user_id=user.id
    ).count()

    return render_template(
        "dashboard.html",
        user=user,
        my_orders=my_orders,
        my_reviews=my_reviews
    )

# ==========================================
# Cart
# ==========================================
@app.route("/add-to-cart/<int:food_id>")
@login_required
def add_to_cart(food_id):

    food = Food.query.get_or_404(food_id)

    cart = session.get("cart", {})

    food_id = str(food.id)

    if food_id in cart:
        cart[food_id] += 1
    else:
        cart[food_id] = 1

    session["cart"] = cart

    flash(f"{food.name} added to cart.", "success")

    return redirect(request.referrer or url_for("menu"))

@app.route("/cart")
@login_required
def cart():

    cart = session.get("cart", {})

    cart_items = []
    total = 0

    for food_id, qty in cart.items():

        food = db.session.get(
            Food,
            int(food_id)
        )

        if food:

            subtotal = food.discounted_price() * qty
            total += subtotal

            cart_items.append({
                "food": food,
                "qty": qty,
                "subtotal": subtotal
            })

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )





@app.route("/cart/increase/<int:food_id>")
@login_required
def increase_quantity(food_id):

    cart = session.get("cart", {})

    food_id = str(food_id)

    if food_id in cart:
        cart[food_id] += 1

    session["cart"] = cart

    return redirect(url_for("cart"))

@app.route("/cart/decrease/<int:food_id>")
@login_required
def decrease_quantity(food_id):

    cart = session.get("cart", {})

    food_id = str(food_id)

    if food_id in cart:

        cart[food_id] -= 1

        if cart[food_id] <= 0:
            del cart[food_id]

    session["cart"] = cart

    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:food_id>")
@login_required
def remove_from_cart(food_id):

    cart = session.get("cart", {})

    food_id = str(food_id)

    if food_id in cart:
        del cart[food_id]

    session["cart"] = cart

    flash("Item removed from cart.", "success")

    return redirect(url_for("cart"))

@app.route("/cart/clear")
@login_required
def clear_cart():

    session["cart"] = {}

    flash("Cart cleared successfully.", "success")

    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():

    form = CheckoutForm()

    if form.validate_on_submit():

        cart = session.get("cart", {})

        if not cart:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("cart"))

        # User Login Check
        if not current_user.is_authenticated:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))

        user = current_user

        total = 0

        for food_id, qty in cart.items():
            food = db.session.get(Food, int(food_id))
            if food:
                total += food.discounted_price() * qty

        customer_name = user.name if user.name else user.email

        order = Order(
            customer=customer_name,
            phone=form.phone.data,
            address=form.address.data,
            total=total,
            user_id=user.id
        )

        try:

            db.session.add(order)
            db.session.flush()

            for food_id, qty in cart.items():

                food = db.session.get(Food, int(food_id))

                if food:

                    item = OrderItem(
                        order_id=order.id,
                        food_id=food.id,
                        quantity=qty,
                        price=food.discounted_price()
                    )

                    db.session.add(item)

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            app.logger.error(f"Checkout Database Error: {e}")

            flash("Unable to place order.", "danger")

            return redirect(url_for("cart"))

        # Send Email
        try:

            msg = Message(
                subject="Order Confirmed - Brotherhood Foodie",
                sender=app.config["MAIL_DEFAULT_SENDER"],
                recipients=[user.email]
            )

            msg.body = f"""
        Hello {customer_name},

        Thank you for ordering from Brotherhood Foodie.

        Your order has been placed successfully.

        Customer : {customer_name}
        Email    : {user.email}
        Total    : ₹{total:.2f}

        Estimated Delivery Time : 30-45 Minutes

        Regards,
        Brotherhood Foodie Team
        """

            mail.send(msg)

        except Exception as error:

            app.logger.error(
                f"Order Email Error: {error}"
            )
        session["cart"] = {}

        flash("Order Placed Successfully!", "success")

        return redirect(url_for("home"))

    return render_template("checkout.html", form=form)


@app.route("/invoice/<int:order_id>")
@login_required
def invoice(order_id):

    order = Order.query.get_or_404(order_id)

    subtotal = order.total

    if subtotal >= 3000:
        discount_percent = 25
    elif subtotal >= 2000:
        discount_percent = 20
    elif subtotal >= 1500:
        discount_percent = 15
    elif subtotal >= 1000:
        discount_percent = 10
    elif subtotal >= 500:
        discount_percent = 5
    else:
        discount_percent = 0

    discount_amount = subtotal * discount_percent / 100

    after_discount = subtotal - discount_amount

    gst = after_discount * 0.05

    grand_total = after_discount + gst

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        rightMargin=50,
        leftMargin=50,
        topMargin=30,
        bottomMargin=20
    )
    styles = getSampleStyleSheet()

    elements = []
    styles["Title"].alignment = 1

    elements.append(
        Paragraph("<b>Brotherhood Foodie</b>", styles["Title"])
    )

    elements.append(
        Paragraph("Restaurant Invoice", styles["Heading2"])
    )
    elements.append(Spacer(1, 8))

    styles["Heading2"].alignment = 1

    
    invoice_no = f"INV-{order.id:05d}"

    info = [

        ["Invoice No", invoice_no],

        ["Order Date", order.created_at.strftime("%d-%m-%Y %I:%M %p")],

        ["Payment", "Cash on Delivery"]

    ]

    info_table = Table(info, colWidths=[120,220])

    info_table.setStyle(TableStyle([

        ("BOTTOMPADDING",(0,0),(-1,-1),6),

        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),

    ]))

    elements.append(info_table)
  

    data = [
        ["Order ID", str(order.id)],
        ["Customer", order.customer],
        ["Phone", order.phone],
        ["Address", order.address],
        ["Status", order.status],
    ]

    table = Table(data, colWidths=[130, 260])

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ]))

    elements.append(table)
    
   
    

    # ========Order items========================

    elements.append(Paragraph("<b>Ordered Items</b>", styles["Heading2"]))
    
    
    

    item_data = [
        ["Food Item", "Qty", "Price", "Total"]
    ]

    for item in order.items:

        item_data.append([
            item.food.name,
            str(item.quantity),
            f"Rs. {item.price:.2f}",
            f"Rs. {item.price * item.quantity:.2f}"
        ])

    item_table = Table(
        item_data,
        colWidths=[180, 50, 80, 80]
    )

    item_table.setStyle(TableStyle([

        ("GRID", (0,0), (-1,-1), 1, colors.black),

        ("BACKGROUND", (0,0), (-1,0), colors.orange),

        ("TEXTCOLOR", (0,0), (-1,0), colors.white),

        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),

        ("ALIGN", (0,0), (-1,-1), "CENTER"),

        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

        ("BOTTOMPADDING", (0,0), (-1,0), 8),

        ("TOPPADDING", (0,0), (-1,-1), 8),

        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#ff6b35")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),

    ]))
    
    elements.append(item_table) 
    
    

    summary_data = [
        ["Subtotal", f"Rs. {subtotal:.2f}"],
        [f"Discount ({discount_percent}%)", f"- Rs. {discount_amount:.2f}"],
        ["Amount After Discount", f"Rs. {after_discount:.2f}"],
        ["GST (5%)", f"Rs. {gst:.2f}"],
        ["You Saved", f"Rs. {discount_amount:.2f}"]
    ]

    summary_table = Table(summary_data, colWidths=[220,110])

    summary_table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.grey),
        ("BACKGROUND",(0,0),(0,-1),colors.beige),
        ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
        ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))

    elements.append(summary_table)
    elements.append(Paragraph("<br/>", styles["Normal"]))
    
    total_table = Table(
        [[f"Grand Total : Rs. {grand_total:.2f}"]],
        colWidths=[330]
    )

    total_table.setStyle(TableStyle([
       ("FONTSIZE",(0,0),(-1,-1),15),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))

    elements.append(total_table)

    elements.append(Spacer(1, 10))

    styles["Normal"].alignment = 1

    elements.append(
        Paragraph(
            "❤️ Thank You For Visiting Brotherhood Foodie ❤️",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            "Fresh Food • Fast Delivery • Visit Again",
            styles["Normal"]
        )
    )

    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    response = make_response(pdf)

    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=invoice_{order.id}.pdf"

    return response

# ==========================================
# Review Routes
# ==========================================
@app.route(
    "/review/<int:food_id>",
    methods=["GET", "POST"]
)
@login_required
def review(food_id):

    food = Food.query.get_or_404(food_id)

    form = ReviewForm()

    if form.validate_on_submit():

        customer_review = Review(
            food_id=food.id,
            user_id=current_user.id,
            rating=form.rating.data,
            comment=form.comment.data.strip()
        )

        try:

            db.session.add(customer_review)
            db.session.commit()

            flash(
                "Review submitted successfully!",
                "success"
            )

            return redirect(
                url_for("home") + "#review"
            )

        except Exception as error:

            db.session.rollback()

            app.logger.error(
                f"Review Save Error: {error}"
            )

            flash(
                "Review submit nahi hua. Please try again.",
                "danger"
            )

    return render_template(
        "review.html",
        form=form,
        food=food
    )


# ==========================================
# Admin Dashboard
# ==========================================
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    total_categories = Category.query.count()
    total_foods = Food.query.count()
    total_gallery = Gallery.query.count()
    total_users = User.query.count()
    total_orders = Order.query.count()

    return render_template(
        "admin/dashboard.html",
        total_categories=total_categories,
        total_foods=total_foods,
        total_gallery=total_gallery,
        total_users=total_users,
        total_orders=total_orders
    )


@app.route("/admin/contacts")
@admin_required
def contacts():

    contacts = Contact.query.order_by(
        Contact.id.desc()
    ).all()

    return render_template(
        "admin/contacts.html",
        contacts=contacts
    )

@app.route("/admin/contact/delete/<int:id>")
@admin_required
def delete_contact(id):

    contact = Contact.query.get_or_404(id)

    db.session.delete(contact)

    db.session.commit()

    flash("Message Deleted Successfully!", "success")

    return redirect(url_for("contacts"))

@app.route("/admin/contact/reply/<int:id>", methods=["GET", "POST"])
@admin_required
def reply_contact(id):

    contact = Contact.query.get_or_404(id)

    if request.method == "POST":

        reply = request.form["reply"]

        contact.admin_reply = reply
        contact.replied = True

        db.session.commit()

        msg = Message(
            subject="Reply from Brotherhood Foodie",
            recipients=[contact.email]
        )

        msg.body = f"""
Hello {contact.name},

Thank you for contacting Brotherhood Foodie.

------------------------------------

Your Message:

{contact.message}

------------------------------------

Admin Reply:

{reply}

------------------------------------

Thank you for contacting us.

Regards,
Brotherhood Foodie Team
"""

        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Reply email failed: {e}")

        flash("Reply Sent Successfully!", "success")

        return redirect(url_for("contacts"))

    return render_template(
        "admin/reply_contact.html",
        contact=contact
    )


# ==========================================
# Category Management
# ==========================================

@app.route("/admin/categories")
@admin_required
def categories():

    categories = Category.query.all()

    return render_template(
        "admin/categories.html",
        categories=categories
    )

@app.route("/admin/category/add", methods=["GET", "POST"])
@admin_required
def add_category():

    form = CategoryForm()

    if form.validate_on_submit():

        filename = ""

        if form.image.data:

            file = form.image.data

            print("Uploaded File:", file.filename)

            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"

            print("Saved Filename:", filename)

            upload_folder = os.path.join(app.root_path, "static", "uploads", "categories")

            os.makedirs(upload_folder, exist_ok=True)

            file.save(os.path.join(upload_folder, filename))

        print("Database Image:", filename)

        category = Category(
            name=form.name.data,
            description=form.description.data,
            image=filename
        )

        db.session.add(category)
        db.session.commit()

        flash("Category Added Successfully", "success")

        return redirect(url_for("categories"))

    return render_template(
        "admin/add_category.html",
        form=form
    )

@app.route("/admin/category/delete/<int:category_id>")
@admin_required
def delete_category(category_id):

    category = Category.query.get_or_404(category_id)

    if category.image:
        image_path = os.path.join(
            app.config["CATEGORY_UPLOAD_FOLDER"],
            category.image
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(category)
    db.session.commit()

    flash("Category Deleted", "success")

    return redirect(url_for("categories"))

@app.route("/admin/category/edit/<int:category_id>", methods=["GET", "POST"])
@admin_required
def edit_category(category_id):

    category = Category.query.get_or_404(category_id)

    form = CategoryForm(obj=category)

    if form.validate_on_submit():

        category.name = form.name.data
        category.description = form.description.data

        if form.image.data:

            file = form.image.data
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"

            file.save(
                os.path.join(
                    app.config["CATEGORY_UPLOAD_FOLDER"],
                    filename
                )
            )

            category.image = filename

        db.session.commit()

        flash("Category Updated Successfully!", "success")

        return redirect(url_for("categories"))

    return render_template(
        "admin/edit_category.html",
        form=form,
        category=category
    )


# ==========================================
# Food Management
# ==========================================
@app.route("/admin/foods")
@admin_required
def foods():

    search = request.args.get("search", "")

    if search:

        foods = (
            Food.query
            .filter(Food.name.ilike(f"%{search}%"))
            .order_by(Food.id.desc())
            .all()
        )

    else:

        foods = Food.query.order_by(Food.id.desc()).all()

    return render_template(
        "admin/foods.html",
        foods=foods,
        search=search
    )

@app.route("/admin/food/add", methods=["GET", "POST"])
@admin_required
def add_food():

    form = FoodForm()

    form.category.choices = [
        (c.id, c.name)
        for c in Category.query.all()
    ]

    if form.validate_on_submit():

        filename = ""

        if form.image.data:

            file = form.image.data

            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"

            file.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

        food = Food(
            category_id=form.category.data,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            discount=form.discount.data,
            image=filename,
            available=form.available.data
        )

        try:
            db.session.add(food)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Unable to save food item.", "danger")
            return redirect(url_for("add_food"))

        flash("Food Added Successfully", "success")

        return redirect(url_for("foods"))

    return render_template(
        "admin/add_food.html",
        form=form
    )

@app.route("/admin/food/edit/<int:food_id>", methods=["GET", "POST"])
@admin_required
def edit_food(food_id):

    food = Food.query.get_or_404(food_id)

    form = FoodForm(obj=food)

    form.category.choices = [
        (c.id, c.name)
        for c in Category.query.all()
    ]

    if form.validate_on_submit():

        food.category_id = form.category.data
        food.name = form.name.data
        food.description = form.description.data
        food.price = form.price.data
        food.discount = form.discount.data
        food.available = form.available.data

        image = form.image.data

        if image and hasattr(image, "filename") and image.filename:

            old_image = food.image

            filename = (
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}_"
                f"{secure_filename(image.filename)}"
            )

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            if old_image:
                old_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    old_image
                )

                if os.path.exists(old_path):
                    os.remove(old_path)

            food.image = filename

        filename = (
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}_"
            f"{secure_filename(image.filename)}"
        )

        image.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        if old_image:
            old_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                old_image
            )

            if os.path.exists(old_path):
                os.remove(old_path)

        food.image = filename

        db.session.commit()

        flash("Food Updated Successfully", "success")

        return redirect(url_for("foods"))

    return render_template(
        "admin/edit_food.html",
        form=form,
        food=food
    )

@app.route("/admin/food/delete/<int:food_id>")
@admin_required
def delete_food(food_id):

    food = Food.query.get_or_404(food_id)

    # Delete image from folder (optional)
    if food.image:
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], food.image)

        if food.image:

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                food.image
            )

            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except OSError:
                pass

    db.session.delete(food)
    db.session.commit()

    flash("Food Deleted Successfully", "success")

    return redirect(url_for("foods"))


# ==========================================
# Gallery Management
# ==========================================

@app.route("/admin/gallery")
@admin_required
def gallery_list():

    galleries = Gallery.query.order_by(
        Gallery.created_at.desc()
    ).all()

    return render_template(
        "admin/gallery.html",
        galleries=galleries
    )

@app.route("/admin/gallery/add", methods=["GET", "POST"])
@admin_required
def add_gallery():

    form = GalleryForm()

    if form.validate_on_submit():

        filename = ""

        if form.image.data:

            file = form.image.data

            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"

            file.save(
                os.path.join(
                    app.config["GALLERY_UPLOAD_FOLDER"],
                    filename
                )
            )

        gallery = Gallery(
            title=form.title.data,
            image=filename
        )

        try:
            db.session.add(gallery)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Unable to upload gallery image.", "danger")
            return redirect(url_for("add_gallery"))

        flash("Gallery Image Uploaded Successfully", "success")

        return redirect(url_for("gallery_list"))

    return render_template(
        "admin/add_gallery.html",
        form=form
    )


@app.route("/admin/gallery/delete/<int:id>")
@admin_required
def delete_gallery(id):

    gallery = Gallery.query.get_or_404(id)

    
    image_path = os.path.join(
        app.config["GALLERY_UPLOAD_FOLDER"],
        gallery.image
    )

    try:
        if os.path.exists(image_path):
            os.remove(image_path)
    except OSError:
        pass

    try:
        db.session.delete(gallery)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Unable to delete gallery image.", "danger")
        return redirect(url_for("gallery_list"))

    flash("Gallery Image Deleted Successfully", "success")

    return redirect(url_for("gallery_list"))
# ==========================================
# Orders details
# ==========================================

@app.route("/order/<int:order_id>")
@login_required
def order_details(order_id):

    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash("Access Denied!", "danger")
        return redirect(url_for("dashboard"))

    return render_template(
        "order_details.html",
        order=order
    )



# ==========================================
# Orders Management
# ==========================================

@app.route("/admin/panel")
@admin_required
def admin_panel():
    return render_template("admin/panel.html")

@app.route("/admin/orders")
@admin_required
def orders():

    orders = Order.query.order_by(Order.id.desc()).all()

    return render_template(
        "admin/orders.html",
        orders=orders
    )

@app.route("/admin/order/status/<int:order_id>/<string:status>")
@admin_required
def update_order_status(order_id, status):

    order = Order.query.get_or_404(order_id)

    allowed_status = [
        "Pending",
        "Preparing",
        "Completed",
        "Cancelled"
    ]

    if status not in allowed_status:
        flash("Invalid order status.", "danger")
        return redirect(url_for("orders"))

    order.status = status

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Unable to update order status.", "danger")
        return redirect(url_for("orders"))

    flash("Order status updated successfully!", "success")

    return redirect(url_for("orders"))

@app.route("/admin/order/complete/<int:order_id>")
@admin_required
def complete_order(order_id):

    order = Order.query.get_or_404(order_id)

    order.status = "Completed"

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Unable to complete order.", "danger")
        return redirect(url_for("orders"))

    flash("Order Completed Successfully!", "success")

    return redirect(url_for("orders"))

@app.route("/admin/order/delete/<int:order_id>")
@admin_required
def delete_order(order_id):

    order = Order.query.get_or_404(order_id)

    try:
        OrderItem.query.filter_by(
            order_id=order.id
        ).delete()

        db.session.delete(order)

        db.session.commit()

    except Exception:
        db.session.rollback()
        flash("Unable to delete order.", "danger")
        return redirect(url_for("orders"))

    flash("Order deleted successfully!", "success")

    return redirect(url_for("orders"))
# ==========================================
# Review Management
# ==========================================

@app.route("/admin/reviews")
@admin_required
def reviews():

    reviews = Review.query.order_by(
        Review.id.desc()
    ).all()

    return render_template(
        "admin/reviews.html",
        reviews=reviews
    )

@app.route("/admin/review/delete/<int:review_id>")
@admin_required
def delete_review(review_id):

    review = Review.query.get_or_404(review_id)

    db.session.delete(review)

    db.session.commit()

    flash("Review Deleted Successfully!", "success")

    return redirect(url_for("reviews"))



# ==========================================
# Contact Form
# ==========================================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    form = ContactForm()

    if form.validate_on_submit():

        contact_message = Contact(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            subject=form.subject.data.strip(),
            message=form.message.data.strip()
        )

        # First save message in database
        try:

            db.session.add(contact_message)
            db.session.commit()

        except Exception as error:

            db.session.rollback()

            app.logger.error(
                f"Contact Save Error: {error}"
            )

            flash(
                "Message save nahi hua. Please try again.",
                "danger"
            )

            return redirect(
                url_for("contact")
            )

        admin_email = app.config.get(
            "MAIL_DEFAULT_SENDER"
        )

        # Email configuration available ho tabhi mail send karo
        if admin_email:

            # Email to admin
            try:

                admin_message = Message(
                    subject=(
                        f"New Contact Message - "
                        f"{contact_message.subject}"
                    ),
                    sender=admin_email,
                    recipients=[admin_email],
                    reply_to=contact_message.email
                )

                admin_message.body = f"""
New Contact Message

Name: {contact_message.name}
Email: {contact_message.email}
Subject: {contact_message.subject}

Message:
{contact_message.message}

Brotherhood Foodie
"""

                mail.send(admin_message)

            except Exception as error:

                app.logger.error(
                    f"Admin Contact Email Error: {error}"
                )

            # Automatic reply to customer
            try:

                customer_message = Message(
                    subject=(
                        "Thank you for contacting "
                        "Brotherhood Foodie"
                    ),
                    sender=admin_email,
                    recipients=[contact_message.email]
                )

                customer_message.body = f"""
Hello {contact_message.name},

We have received your message successfully.

Subject:
{contact_message.subject}

Our team will reply shortly.

Regards,
Brotherhood Foodie Team
"""

                mail.send(customer_message)

            except Exception as error:

                app.logger.error(
                    f"Customer Contact Email Error: {error}"
                )

        flash(
            "Message Sent Successfully!",
            "success"
        )

        return redirect(
            url_for("home") + "#contact"
        )

    # Show validation errors in browser
    if request.method == "POST":

        for field_name, errors in form.errors.items():

            readable_name = (
                field_name
                .replace("_", " ")
                .title()
            )

            for error in errors:

                flash(
                    f"{readable_name}: {error}",
                    "danger"
                )

    if request.method == "POST":

        for field_name, errors in form.errors.items():

            readable_name = (
                field_name
                .replace("_", " ")
                .title()
            )

            for error in errors:

                flash(
                    f"{readable_name}: {error}",
                    "danger"
                )

    return redirect(
        url_for("home") + "#contact"
    )
# ==========================================
# offers
# ==========================================
@app.route("/special-offer")
@login_required
def add_special_offer():

    # First available pizza with discount
    food = Food.query.filter(
        Food.available == True,
        Food.discount > 0
    ).first()

    if not food:
        flash("Special offer is currently unavailable.", "warning")
        return redirect(url_for("menu"))

    cart = session.get("cart", {})

    food_id = str(food.id)

    if food_id in cart:
        cart[food_id] += 1
    else:
        cart[food_id] = 1

    session["cart"] = cart

    flash(f"{food.name} added to cart successfully!", "success")

    return redirect(url_for("cart"))

# ==========================================
#  forget password
# ==========================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    form = ForgetPasswordForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not registered.", "danger")
            return redirect(url_for("forgot_password"))

        otp = random.randint(100000, 999999)

        session["reset_email"] = user.email
        session["reset_otp"] = str(otp)

        session["otp_expiry"] = (
            datetime.now() + timedelta(minutes=5)
        ).strftime("%Y-%m-%d %H:%M:%S")

        try:

            msg = Message(
                subject="Password Reset OTP",
                sender=app.config["MAIL_DEFAULT_SENDER"],
                recipients=[user.email]
            )

            msg.body = f"""
Hello {user.name},

Your OTP for password reset is:

{otp}

This OTP is valid for 5 minutes.

Brotherhood Foodie
"""

            mail.send(msg)

        except Exception as error:

            app.logger.error(
                f"Forgot Password Email Error: {error}"
            )

            flash(
                "Unable to send OTP. Please try again later.",
                "danger"
            )

            return redirect(url_for("forgot_password"))

        flash("OTP sent to your email.", "success")

        return redirect(url_for("verify_otp"))

    return render_template(
        "forgot_password.html",
        form=form
    )
# ==========================================
# verify_otp
# ==========================================

@app.route(
    "/verify-otp",
    methods=["GET", "POST"]
)
def verify_otp():

    if (
        "reset_otp" not in session
        or "otp_expiry" not in session
        or "reset_email" not in session
    ):

        flash(
            "Please request a new OTP.",
            "warning"
        )

        return redirect(
            url_for("forgot_password")
        )

    form = OTPForm()

    if form.validate_on_submit():

        try:

            expiry = datetime.strptime(
                session["otp_expiry"],
                "%Y-%m-%d %H:%M:%S"
            )

        except (ValueError, KeyError):

            session.pop(
                "reset_otp",
                None
            )

            session.pop(
                "otp_expiry",
                None
            )

            flash(
                "Invalid OTP session. Please request a new OTP.",
                "danger"
            )

            return redirect(
                url_for("forgot_password")
            )

        if datetime.now() > expiry:

            session.pop(
                "reset_otp",
                None
            )

            session.pop(
                "otp_expiry",
                None
            )

            flash(
                "OTP expired. Please request a new OTP.",
                "danger"
            )

            return redirect(
                url_for("forgot_password")
            )

        entered_otp = form.otp.data.strip()

        saved_otp = session.get(
            "reset_otp"
        )

        if entered_otp == saved_otp:

            session["otp_verified"] = True

            session.pop(
                "reset_otp",
                None
            )

            session.pop(
                "otp_expiry",
                None
            )

            flash(
                "OTP verified successfully.",
                "success"
            )

            return redirect(
                url_for("reset_password")
            )

        flash(
            "Invalid OTP.",
            "danger"
        )

    return render_template(
        "verify_otp.html",
        form=form
    )

# ==========================================
# Reset Password
# ==========================================
@app.route(
    "/reset-password",
    methods=["GET", "POST"]
)
def reset_password():

    if not session.get(
        "otp_verified"
    ):

        flash(
            "Please verify your OTP first.",
            "warning"
        )

        return redirect(
            url_for("forgot_password")
        )

    reset_email = session.get(
        "reset_email"
    )

    if not reset_email:

        flash(
            "Password reset session expired.",
            "danger"
        )

        return redirect(
            url_for("forgot_password")
        )

    form = ResetPasswordForm()

    if form.validate_on_submit():

        user = User.query.filter_by(
            email=reset_email
        ).first()

        if not user:

            flash(
                "User not found.",
                "danger"
            )

            return redirect(
                url_for("forgot_password")
            )

        user.set_password(
            form.password.data
        )

        try:

            db.session.commit()

        except Exception as error:

            db.session.rollback()

            app.logger.error(
                f"Reset Password Error: {error}"
            )

            flash(
                "Unable to reset password.",
                "danger"
            )

            return redirect(
                url_for("reset_password")
            )

        session.pop(
            "reset_email",
            None
        )

        session.pop(
            "reset_otp",
            None
        )

        session.pop(
            "otp_expiry",
            None
        )

        session.pop(
            "otp_verified",
            None
        )

        flash(
            "Password reset successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "reset_password.html",
        form=form
    )


# ==========================================
# Error Handlers
# ==========================================

@app.errorhandler(404)
def not_found(error):

    return render_template(
        "404.html"
    ), 404


@app.errorhandler(500)
def server_error(error):

    db.session.rollback()

    app.logger.error(
        f"Server Error: {error}"
    )

    return render_template(
        "500.html"
    ), 500


# ==========================================
if __name__ == "__main__":
    app.run(debug=True)