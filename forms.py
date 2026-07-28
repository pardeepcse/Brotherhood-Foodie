from flask_wtf import FlaskForm
from wtforms import StringField,  TextAreaField, SubmitField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
from flask_wtf.file import FileField, FileAllowed
from wtforms import FloatField, BooleanField, SelectField

class LoginForm(FlaskForm):

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired()
        ]
    )

    submit = SubmitField("Login")


class RegisterForm(FlaskForm):

    name = StringField(
        "Name",
        validators=[DataRequired(), Length(min=3, max=100)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128)
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password")
        ]
    )

    submit = SubmitField("Register")



class CategoryForm(FlaskForm):

    name = StringField(
        "Category Name",
        validators=[DataRequired()]
    )

    description = TextAreaField("Description")

    image = FileField(
        "Category Image",
        validators=[
            FileAllowed(
                ["jpg", "jpeg", "png"],
                "Images only!"
            )
        ]
    )

    submit = SubmitField("Save Category")


class FoodForm(FlaskForm):

    category = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired()]
    )

    name = StringField(
        "Food Name",
        validators=[DataRequired()]
    )

    description = TextAreaField("Description")

    price = FloatField(
        "Price",
        validators=[
            DataRequired(),
            NumberRange(min=0)
        ]
    )

    discount = FloatField(
        "Discount",
        default=0,
        validators=[
            NumberRange(min=0, max=100)
        ]
    )

    image = FileField(
        "Image",
        validators=[
            FileAllowed(
                ["jpg","jpeg","png"],
                "Images only!"
            )
        ]
    )

    available = BooleanField(
        "Available",
        default=True
    )

    submit = SubmitField("Save Food")


class CheckoutForm(FlaskForm):

    name = StringField(
        "Full Name",
        validators=[DataRequired()]
    )

    phone = StringField(
        "Phone Number",
        validators=[DataRequired()]
    )

    address = TextAreaField(
        "Address",
        validators=[DataRequired()]
    )

    submit = SubmitField("Place Order")


class ReviewForm(FlaskForm):

    rating = SelectField(
        "Rating",
        choices=[
            (1, "⭐ 1 Star"),
            (2, "⭐⭐ 2 Stars"),
            (3, "⭐⭐⭐ 3 Stars"),
            (4, "⭐⭐⭐⭐ 4 Stars"),
            (5, "⭐⭐⭐⭐⭐ 5 Stars")
        ],
        coerce=int,
        validators=[DataRequired()]
    )

    comment = TextAreaField(
        "Review",
        validators=[
            DataRequired(),
            Length(min=5, max=500)
        ]
    )

    submit = SubmitField("Submit Review")



class GalleryForm(FlaskForm):

    title = StringField(
        "Image Title"
    )

    image = FileField(
        "Gallery Image",
        validators=[
            FileAllowed(
                ["jpg", "jpeg", "png"],
                "Images only!"
            )
        ]
    )

    submit = SubmitField("Upload Image")


class ContactForm(FlaskForm):

    name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    subject = StringField(
        "Subject",
        validators=[
            DataRequired(),
            Length(min=3, max=200)
        ]
    )

    message = TextAreaField(
        "Message",
        validators=[
            DataRequired(),
            Length(min=10, max=2000)
        ]
    )

    submit = SubmitField(
        "Send Message"
    )


class ForgetPasswordForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    submit = SubmitField("Send OTP")


class OTPForm(FlaskForm):

    otp = StringField(
        "OTP",
        validators=[
            DataRequired(),
            Length(min=6, max=6)
        ]
    )

    submit = SubmitField("Verify OTP")



class ResetPasswordForm(FlaskForm):

    password = PasswordField(
        "New Password",
        validators=[DataRequired()]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128)
        ]
    )

    submit = SubmitField("Reset Password")