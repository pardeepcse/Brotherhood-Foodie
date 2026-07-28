from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user


def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not current_user.is_authenticated:

            flash("Please login first.", "danger")

            return redirect(
                url_for("login", next=request.url)
            )

        return func(*args, **kwargs)

    return wrapper


def admin_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not current_user.is_authenticated:

            flash("Please login first.", "danger")

            return redirect(url_for("login"))

        if current_user.role != "admin":

            flash("Access denied!", "danger")

            return redirect(url_for("home"))

        return func(*args, **kwargs)

    return wrapper