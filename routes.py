from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from models import User, Store


auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "buyer")

        if not full_name or not email or not password:
            flash("يرجى ملء جميع الحقول.", "error")
            return redirect(url_for("auth.register"))

        if role not in ("buyer", "seller"):
            role = "buyer"

        existing_user = User.find_by_email(email)

        if existing_user:
            flash("هذا البريد الإلكتروني مسجل من قبل.", "error")
            return redirect(url_for("auth.register"))

        password_hash = generate_password_hash(password)

        user_id = User.create(
            full_name=full_name,
            email=email,
            password=password_hash,
            role=role
        )

        if user_id is None:
            flash("تعذر إنشاء الحساب.", "error")
            return redirect(url_for("auth.register"))

        # إنشاء متجر تلقائيًا للبائع
        if role == "seller":
            Store.create(
                user_id=user_id,
                name=f"متجر {full_name}"
            )

        session["user_id"] = user_id
        session["role"] = role

        flash("تم إنشاء الحساب بنجاح 🎉", "success")

        return redirect(url_for("home"))

    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.find_by_email(email)

        if not user:
            flash("البريد الإلكتروني أو كلمة المرور غير صحيحة.", "error")
            return redirect(url_for("auth.login"))

        if not check_password_hash(user["password"], password):
            flash("البريد الإلكتروني أو كلمة المرور غير صحيحة.", "error")
            return redirect(url_for("auth.login"))

        session["user_id"] = user["id"]
        session["role"] = user["role"]

        flash("مرحبًا بك من جديد 👋", "success")

        return redirect(url_for("home"))

    return render_template("login.html")


@auth.route("/logout")
def logout():
    session.clear()

    flash("تم تسجيل الخروج بنجاح.", "success")

    return redirect(url_for("home"))
