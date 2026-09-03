from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from models import User, Store


auth = Blueprint("auth", __name__)


# =========================================================
# HELPERS
# =========================================================

def validate_password(password):
    """
    Minimum security rules:
    - 8 characters
    - at least one letter
    - at least one number
    """

    if len(password) < 8:
        return False

    has_letter = any(char.isalpha() for char in password)
    has_number = any(char.isdigit() for char in password)

    return has_letter and has_number


def login_user(user):
    """
    Store only the necessary identity information
    in the session.
    """

    session.clear()

    session["user_id"] = user["id"]
    session["role"] = user["role"]

    session.permanent = True


# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # -------------------------------------------------
        # Basic account information
        # -------------------------------------------------

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        role = request.form.get(
            "role",
            "buyer"
        ).strip().lower()

        accepted_terms = request.form.get(
            "accept_terms"
        )

        # -------------------------------------------------
        # Seller information
        # -------------------------------------------------

        store_name = request.form.get(
            "store_name",
            ""
        ).strip()

        activity_type = request.form.get(
            "activity_type",
            ""
        ).strip()

        wilaya = request.form.get(
            "wilaya",
            ""
        ).strip()

        municipality = request.form.get(
            "municipality",
            ""
        ).strip()

        verification_note = request.form.get(
            "verification_note",
            ""
        ).strip()

        # -------------------------------------------------
        # Validate role
        # -------------------------------------------------

        if role not in ("buyer", "seller"):
            role = "buyer"

        # -------------------------------------------------
        # Required fields
        # -------------------------------------------------

        if not full_name:
            flash(
                "يرجى إدخال الاسم الكامل.",
                "error"
            )
            return redirect(url_for("auth.register"))

        if not email:
            flash(
                "يرجى إدخال البريد الإلكتروني.",
                "error"
            )
            return redirect(url_for("auth.register"))

        if not phone:
            flash(
                "يرجى إدخال رقم الهاتف.",
                "error"
            )
            return redirect(url_for("auth.register"))

        if not password:
            flash(
                "يرجى إدخال كلمة المرور.",
                "error"
            )
            return redirect(url_for("auth.register"))

        if not confirm_password:
            flash(
                "يرجى تأكيد كلمة المرور.",
                "error"
            )
            return redirect(url_for("auth.register"))

        # -------------------------------------------------
        # Terms
        # -------------------------------------------------

        if not accepted_terms:
            flash(
                "يجب الموافقة على شروط الاستخدام.",
                "error"
            )
            return redirect(url_for("auth.register"))

        # -------------------------------------------------
        # Password validation
        # -------------------------------------------------

        if not validate_password(password):
            flash(
                "كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل، "
                "وحرف واحد ورقم واحد.",
                "error"
            )
            return redirect(url_for("auth.register"))

        if password != confirm_password:
            flash(
                "كلمتا المرور غير متطابقتين.",
                "error"
            )
            return redirect(url_for("auth.register"))

        # -------------------------------------------------
        # Check existing account
        # -------------------------------------------------

        existing_user = User.find_by_email(email)

        if existing_user:
            flash(
                "هذا البريد الإلكتروني مسجل من قبل.",
                "error"
            )
            return redirect(url_for("auth.register"))

        # -------------------------------------------------
        # Seller validation
        # -------------------------------------------------

        if role == "seller":

            if not store_name:
                flash(
                    "يرجى إدخال اسم المتجر.",
                    "error"
                )
                return redirect(url_for("auth.register"))

            if not activity_type:
                flash(
                    "يرجى تحديد نوع النشاط.",
                    "error"
                )
                return redirect(url_for("auth.register"))

            if not wilaya:
                flash(
                    "يرجى تحديد الولاية.",
                    "error"
                )
                return redirect(url_for("auth.register"))

        # -------------------------------------------------
        # Hash password
        # -------------------------------------------------

        password_hash = generate_password_hash(
            password
        )

        # -------------------------------------------------
        # Create user
        # -------------------------------------------------

        user_id = User.create(
            full_name=full_name,
            email=email,
            password=password_hash,
            role=role,
            phone=phone
        )

        if user_id is None:
            flash(
                "تعذر إنشاء الحساب. "
                "ربما البريد الإلكتروني مستخدم.",
                "error"
            )
            return redirect(url_for("auth.register"))

        # -------------------------------------------------
        # Seller setup
        # -------------------------------------------------

        if role == "seller":

            Store.create(
                user_id=user_id,
                name=store_name,
                description="",
                phone=phone,
                wilaya=wilaya,
                municipality=municipality
            )

            # Seller verification remains pending.
            # The admin can verify the seller later.

            from database import get_connection

            connection = get_connection()

            connection.execute(
                """
                UPDATE users
                SET
                    seller_verification_status = 'pending',
                    seller_activity_type = ?,
                    seller_verification_note = ?
                WHERE id = ?
                """,
                (
                    activity_type,
                    verification_note,
                    user_id
                )
            )

            connection.commit()
            connection.close()

        # -------------------------------------------------
        # Login automatically
        # -------------------------------------------------

        user = User.find_by_id(user_id)

        if user:
            login_user(user)

        flash(
            "تم إنشاء حسابك بنجاح 🎉",
            "success"
        )

        return redirect(url_for("home"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:
            flash(
                "يرجى إدخال البريد الإلكتروني وكلمة المرور.",
                "error"
            )
            return redirect(url_for("auth.login"))

        user = User.find_by_email(email)

        if not user:
            flash(
                "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
                "error"
            )
            return redirect(url_for("auth.login"))

        stored_password = user["password"]

        if not check_password_hash(
            stored_password,
            password
        ):
            flash(
                "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
                "error"
            )
            return redirect(url_for("auth.login"))

        login_user(user)

        flash(
            "مرحبًا بك من جديد 👋",
            "success"
        )

        return redirect(url_for("home"))

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
def logout():

    session.clear()

    flash(
        "تم تسجيل الخروج بنجاح.",
        "success"
    )

    return redirect(url_for("home"))
