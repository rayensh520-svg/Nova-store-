import os
import re
import sqlite3
import secrets
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    abort,
    current_app,
    send_from_directory,
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from database import get_db
from models import (
    User,
    Store,
    Product,
    Favorite,
    Cart,
    Order,
    OrderItem,
    Review,
    StoreFollower,
    Message,
    Notification,
    Complaint,
    BlockedUser,
    RewardCard,
    Referral,
    RewardMilestone,
    PriceAlert,
    ProductView,
    ChatSettings,
)


auth = Blueprint("auth", __name__)


# =========================================================
# HELPERS
# =========================================================

def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    try:
        return User.find_by_id(user_id)
    except Exception:
        return None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()

        if not user:
            flash("سجلي الدخول أولاً.", "warning")
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()

        if not user or user["role"] != "admin":
            abort(403)

        return view(*args, **kwargs)

    return wrapped


def seller_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()

        if not user or user["role"] != "seller":
            abort(403)

        return view(*args, **kwargs)

    return wrapped


def approved_seller_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()

        if not user or user["role"] != "seller":
            abort(403)

        if user["seller_verification_status"] != "approved":
            flash(
                "حساب البائع مازال قيد المراجعة. بعد الموافقة يمكنك نشر المنتجات.",
                "warning",
            )
            return redirect(url_for("auth.seller"))

        return view(*args, **kwargs)

    return wrapped


def row_value(row, key, default=None):
    if row is None:
        return default

    try:
        value = row[key]
        return default if value is None else value
    except Exception:
        return default


def safe_int(value, default=0, minimum=None, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default

    if minimum is not None:
        number = max(number, minimum)

    if maximum is not None:
        number = min(number, maximum)

    return number


def safe_float(value, default=0.0, minimum=None, maximum=None):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    if minimum is not None:
        number = max(number, minimum)

    if maximum is not None:
        number = min(number, maximum)

    return number


# =========================================================
# PASSWORD
# =========================================================

def validate_password(password):
    """
    كلمة السر:
    - الحد الأدنى 8 أحرف فقط.
    - القوة (حروف + أرقام + رموز) توصية وليست شرطاً.
    """
    if not password:
        return False, "أدخلي كلمة السر."

    if len(password) < 8:
        return False, "كلمة السر يجب أن تحتوي على 8 أحرف على الأقل."

    return True, None


def password_strength_message(password):
    if not password:
        return "ننصح باستعمال حروف كبيرة وصغيرة وأرقام ورموز."

    has_letter = bool(re.search(r"[A-Za-zÀ-ÿ\u0600-\u06FF]", password))
    has_number = bool(re.search(r"\d", password))
    has_symbol = bool(re.search(r"[^A-Za-zÀ-ÿ\u0600-\u06FF0-9]", password))

    score = sum([has_letter, has_number, has_symbol])

    if len(password) >= 12 and score == 3:
        return "كلمة سر قوية جداً."

    if score >= 2:
        return "كلمة سر جيدة."

    return "يمكن تقوية كلمة السر بإضافة أرقام ورموز."


# =========================================================
# FILE UPLOAD SECURITY
# =========================================================

ALLOWED_ID_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "pdf"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_UPLOAD_SIZE = 8 * 1024 * 1024


def allowed_file(filename, extensions):
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()
    return extension in extensions


def save_private_verification_document(file):
    """
    وثائق الهوية لا يتم وضعها داخل static.
    تحفظ داخل مجلد خاص ولا يتم إنشاء route عام لعرضها.
    """

    if not file or not file.filename:
        return None, "لم يتم اختيار وثيقة."

    if not allowed_file(file.filename, ALLOWED_ID_EXTENSIONS):
        return None, "نوع الوثيقة غير مسموح."

    original_name = secure_filename(file.filename)

    if not original_name:
        return None, "اسم الملف غير صالح."

    extension = original_name.rsplit(".", 1)[1].lower()

    upload_dir = os.path.join(
        current_app.instance_path,
        "private",
        "verification_documents",
    )

    os.makedirs(upload_dir, exist_ok=True)

    random_name = f"{secrets.token_urlsafe(24)}.{extension}"
    path = os.path.join(upload_dir, random_name)

    try:
        file.save(path)

        if os.path.getsize(path) > MAX_UPLOAD_SIZE:
            os.remove(path)
            return None, "حجم الوثيقة كبير جداً. الحد الأقصى 8MB."

    except Exception:
        return None, "حدث خطأ أثناء حفظ الوثيقة."

    return random_name, None


def normalize_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]


# =========================================================
# CART
# =========================================================

def product_unit_price(product):
    price = safe_float(row_value(product, "price", 0))
    discount = safe_float(row_value(product, "discount", 0))

    return max(price - discount, 0)


def get_cart_total(user_id):
    total = 0

    items = Cart.get_items(user_id)

    for item in items:
        quantity = safe_int(row_value(item, "cart_quantity", 1), 1, 1)
        total += product_unit_price(item) * quantity

    return total


# =========================================================
# HOME
# =========================================================

@auth.route("/")
def index():
    try:
        products = ProductSearch.latest(limit=24)
    except Exception:
        products = []

    return render_template(
        "index.html",
        products=products,
        user=current_user(),
    )


# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if current_user():
        return redirect(url_for("auth.index"))

    if request.method == "GET":
        return render_template("register.html")

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()

    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    role = request.form.get("role", "buyer").strip().lower()

    wilaya = request.form.get("wilaya", "").strip()
    municipality = request.form.get("municipality", "").strip()

    if role not in ("buyer", "seller"):
        role = "buyer"

    if not full_name:
        flash("الاسم الكامل مطلوب.", "danger")
        return redirect(url_for("auth.register"))

    if not email or "@" not in email:
        flash("أدخلي بريداً إلكترونياً صحيحاً.", "danger")
        return redirect(url_for("auth.register"))

    valid_password, password_error = validate_password(password)

    if not valid_password:
        flash(password_error, "danger")
        return redirect(url_for("auth.register"))

    if password != confirm_password:
        flash("كلمتا السر غير متطابقتين.", "danger")
        return redirect(url_for("auth.register"))

    try:
        if User.find_by_email(email):
            flash("هذا البريد الإلكتروني مستعمل من قبل.", "danger")
            return redirect(url_for("auth.register"))

        password_hash = generate_password_hash(password)

        referral_code = request.form.get("referral_code", "").strip().upper()
        referred_by = None

        if referral_code:
            referrer = User.find_by_referral_code(referral_code)

            if referrer:
                referred_by = referrer["id"]

        seller_activity_type = None
        seller_verification_note = None

        if role == "seller":
            seller_activity_type = request.form.get(
                "activity_type",
                ""
            ).strip()

            seller_verification_note = request.form.get(
                "verification_note",
                ""
            ).strip()

        user_id = User.create(
            full_name=full_name,
            email=email,
            password_hash=password_hash,
            phone=phone or None,
            role=role,
            wilaya=wilaya or None,
            municipality=municipality or None,
            seller_activity_type=seller_activity_type,
            seller_verification_note=seller_verification_note,
            referral_code=referral_code or None,
            referred_by=referred_by,
        )

        if role == "seller":

            document_type = request.form.get(
                "verification_document_type",
                "",
            ).strip()

            document = request.files.get(
                "verification_document"
            )

            if document_type not in (
                "national_id",
                "driving_license",
            ):
                flash(
                    "يجب اختيار بطاقة التعريف الوطنية أو رخصة السياقة.",
                    "danger",
                )
                return redirect(url_for("auth.register"))

            filename, upload_error = save_private_verification_document(
                document
            )

            if upload_error:
                flash(upload_error, "danger")
                return redirect(url_for("auth.register"))

            verification_note = seller_verification_note or ""

            verification_note = (
                f"{verification_note}\n"
                f"DOCUMENT_TYPE={document_type}\n"
                f"DOCUMENT_FILE={filename}"
            ).strip()

            User.set_seller_verification(
                user_id,
                "pending",
                verification_note,
            )

            store_name = request.form.get(
                "store_name",
                "",
            ).strip()

            if not store_name:
                store_name = full_name

            Store.create(
                user_id=user_id,
                name=store_name,
                description="",
                phone=phone or None,
                wilaya=wilaya or None,
                municipality=municipality or None,
                logo=None,
                cover_image=None,
            )

            flash(
                "تم إنشاء حساب البائع. طلب التحقق قيد المراجعة.",
                "success",
            )

        else:
            flash(
                "تم إنشاء حسابك بنجاح. مرحباً بك في DZ MARKET.",
                "success",
            )

        session.clear()
        session["user_id"] = user_id

        return redirect(url_for("auth.index"))

    except sqlite3.IntegrityError:
        flash(
            "تعذر إنشاء الحساب. ربما البريد الإلكتروني مستعمل.",
            "danger",
        )
        return redirect(url_for("auth.register"))

    except Exception as exc:
        current_app.logger.exception(
            "Registration error: %s",
            exc,
        )

        flash(
            "حدث خطأ أثناء إنشاء الحساب.",
            "danger",
        )

        return redirect(url_for("auth.register"))


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if current_user():
        return redirect(url_for("auth.index"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash(
            "أدخلي البريد الإلكتروني وكلمة السر.",
            "danger",
        )
        return redirect(url_for("auth.login"))

    try:
        user = User.find_by_email(email)

        if not user:
            flash(
                "البريد الإلكتروني أو كلمة السر غير صحيحة.",
                "danger",
            )
            return redirect(url_for("auth.login"))

        if not user["is_active"]:
            flash(
                "هذا الحساب غير نشط.",
                "danger",
            )
            return redirect(url_for("auth.login"))

        stored_password = user["password"]

        if not check_password_hash(
            stored_password,
            password,
        ):
            flash(
                "البريد الإلكتروني أو كلمة السر غير صحيحة.",
                "danger",
            )
            return redirect(url_for("auth.login"))

        session.clear()
        session["user_id"] = user["id"]

        flash(
            "تم تسجيل الدخول بنجاح.",
            "success",
        )

        return redirect(
            request.args.get("next")
            or url_for("auth.index")
        )

    except Exception as exc:
        current_app.logger.exception(
            "Login error: %s",
            exc,
        )

        flash(
            "حدث خطأ أثناء تسجيل الدخول.",
            "danger",
        )

        return redirect(url_for("auth.login"))


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
@login_required
def logout():

    session.clear()

    flash(
        "تم تسجيل الخروج.",
        "success",
    )

    return redirect(url_for("auth.index"))


# =========================================================
# ACCOUNT
# =========================================================

@auth.route("/account")
@login_required
def account():

    user = current_user()

    return render_template(
        "account.html",
        user=user,
    )


@auth.route("/account/edit", methods=["GET", "POST"])
@login_required
def edit_account():
    user = current_user()

    if not user:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        wilaya = (request.form.get("wilaya") or "").strip()
        municipality = (request.form.get("municipality") or "").strip()
        bio = (request.form.get("bio") or "").strip()

        if not full_name:
            flash("الاسم الكامل مطلوب.", "danger")
            return redirect(url_for("auth.edit_account"))

        if len(full_name) > 120:
            flash("الاسم طويل جداً.", "danger")
            return redirect(url_for("auth.edit_account"))

        if len(bio) > 500:
            flash("النبذة يجب ألا تتجاوز 500 حرف.", "danger")
            return redirect(url_for("auth.edit_account"))

        avatar_path = None
        avatar = request.files.get("avatar")

        if avatar and avatar.filename:
            original_name = secure_filename(avatar.filename)

            if not original_name:
                flash("اسم الصورة غير صالح.", "danger")
                return redirect(url_for("auth.edit_account"))

            if not allowed_file(
                original_name,
                ALLOWED_IMAGE_EXTENSIONS,
            ):
                flash(
                    "صيغة الصورة غير مدعومة. استعمل JPG أو PNG أو WEBP.",
                    "danger",
                )
                return redirect(url_for("auth.edit_account"))

            try:
                avatar.seek(0, os.SEEK_END)
                file_size = avatar.tell()
                avatar.seek(0)
            except Exception:
                flash("تعذر قراءة حجم الصورة.", "danger")
                return redirect(url_for("auth.edit_account"))

            if file_size > 5 * 1024 * 1024:
                flash(
                    "حجم الصورة كبير جداً. الحد الأقصى 5MB.",
                    "danger",
                )
                return redirect(url_for("auth.edit_account"))

            extension = original_name.rsplit(".", 1)[1].lower()

            upload_folder = os.path.join(
                current_app.instance_path,
                "uploads",
                "avatars",
            )

            os.makedirs(upload_folder, exist_ok=True)

            filename = (
                f"user_{user['id']}_{secrets.token_hex(12)}.{extension}"
            )

            save_path = os.path.join(
                upload_folder,
                filename,
            )

            try:
                avatar.save(save_path)
            except Exception:
                current_app.logger.exception(
                    "Avatar save error"
                )
                flash(
                    "تعذر حفظ صورة الحساب.",
                    "danger",
                )
                return redirect(url_for("auth.edit_account"))

            avatar_path = (
                f"/account/avatar/{user['id']}/{filename}"
            )

        try:
            User.update_profile(
                user["id"],
                full_name=full_name,
                phone=phone,
                wilaya=wilaya,
                municipality=municipality,
                bio=bio,
                avatar=(
                    avatar_path
                    if avatar_path
                    else user["avatar"]
                ),
            )

            flash(
                "تم تحديث معلومات حسابك بنجاح.",
                "success",
            )

            return redirect(
                url_for("auth.account")
            )

        except Exception as exc:
            current_app.logger.exception(
                "Account update error: %s",
                exc,
            )

            flash(
                "حدث خطأ أثناء حفظ التغييرات.",
                "danger",
            )

            return redirect(
                url_for("auth.edit_account")
            )

    return render_template(
        "edit_account.html",
        user=user,
    )


@auth.route("/account/avatar/<int:user_id>/<filename>")
@login_required
def account_avatar(user_id, filename):
    user = current_user()

    if not user:
        return redirect(url_for("auth.login"))

    # صورة الحساب عامة من ناحية العرض، لكن لا يمكن استعمال
    # هذا المسار للوصول إلى وثائق الهوية لأنها محفوظة في مجلد مختلف.
    upload_folder = os.path.join(
        current_app.instance_path,
        "uploads",
        "avatars",
    )

    return send_from_directory(
        upload_folder,
        filename,
    )


# =========================================================
# ORDERS
# =========================================================

@auth.route("/orders")
@login_required
def orders():

    user = current_user()

    orders_list = Order.by_user(
        user["id"]
    )

    return render_template(
        "orders.html",
        user=user,
        orders=orders_list,
    )


@auth.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):

    user = current_user()

    order = Order.find_by_id(
        order_id
    )

    if not order:
        abort(404)

    if order["user_id"] != user["id"]:
        abort(403)

    items = OrderItem.by_order(
        order_id
    )

    reviews = {}

    for item in items:
        try:
            existing = Review.by_product(
                item["product_id"]
            )

            for review in existing:
                if review["user_id"] == user["id"]:
                    reviews[item["product_id"]] = review
        except Exception:
            pass

    return render_template(
        "order_detail.html",
        user=user,
        order=order,
        items=items,
        reviews=reviews,
    )


# =========================================================
# CART
# =========================================================

@auth.route("/cart")
@login_required
def cart():

    user = current_user()

    items = Cart.get_items(
        user["id"]
    )

    total = get_cart_total(
        user["id"]
    )

    return render_template(
        "cart.html",
        user=user,
        items=items,
        total=total,
    )


@auth.route("/cart/add", methods=["POST"])
@login_required
def add_to_cart():

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id"),
        0,
        1,
    )

    quantity = safe_int(
        request.form.get("quantity"),
        1,
        1,
        9999,
    )

    purchase_mode = request.form.get(
        "purchase_mode",
        "ready_stock",
    )

    product = Product.find_by_id(
        product_id
    )

    if not product:
        flash(
            "المنتج غير موجود.",
            "danger",
        )
        return redirect(
            url_for("auth.index")
        )

    try:
        Cart.add(
            user["id"],
            product_id,
            quantity,
            purchase_mode,
        )

        flash(
            "تمت إضافة المنتج إلى السلة.",
            "success",
        )

    except Exception as exc:
        current_app.logger.exception(
            "Cart add error: %s",
            exc,
        )

        flash(
            "تعذر إضافة المنتج إلى السلة.",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for("auth.cart")
    )


@auth.route("/cart/update", methods=["POST"])
@login_required
def update_cart():

    user = current_user()

    item_id = safe_int(
        request.form.get("item_id"),
        0,
        1,
    )

    quantity = safe_int(
        request.form.get("quantity"),
        1,
        1,
        9999,
    )

    try:
        Cart.update(
            item_id,
            user["id"],
            quantity,
        )

        flash(
            "تم تحديث السلة.",
            "success",
        )

    except Exception:
        flash(
            "تعذر تحديث السلة.",
            "danger",
        )

    return redirect(
        url_for("auth.cart")
    )


@auth.route("/cart/remove", methods=["POST"])
@login_required
def remove_from_cart():

    user = current_user()

    item_id = safe_int(
        request.form.get("item_id"),
        0,
        1,
    )

    try:
        Cart.remove(
            item_id,
            user["id"],
        )
        flash(
            "تم حذف المنتج من السلة.",
            "success",
        )
    except Exception:
        flash(
            "تعذر حذف المنتج.",
            "danger",
        )

    return redirect(
        url_for("auth.cart")
    )


@auth.route("/cart/clear", methods=["POST"])
@login_required
def clear_cart():

    user = current_user()

    Cart.clear(
        user["id"]
    )

    flash(
        "تم تفريغ السلة.",
        "success",
    )

    return redirect(
        url_for("auth.cart")
    )


# =========================================================
# CHECKOUT
# =========================================================

@auth.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():

    user = current_user()

    items = Cart.get_items(
        user["id"]
    )

    if not items:
        flash(
            "السلة فارغة.",
            "warning",
        )
        return redirect(
            url_for("auth.cart")
        )

    total = get_cart_total(
        user["id"]
    )

    if request.method == "GET":
        return render_template(
            "checkout.html",
            user=user,
            items=items,
            total=total,
        )

    delivery_address = request.form.get(
        "delivery_address",
        "",
    ).strip()

    delivery_wilaya = request.form.get(
        "delivery_wilaya",
        "",
    ).strip()

    delivery_phone = request.form.get(
        "delivery_phone",
        "",
    ).strip()

    if not delivery_address:
        flash(
            "عنوان التوصيل مطلوب.",
            "danger",
        )
        return redirect(
            url_for("auth.checkout")
        )

    if not delivery_wilaya:
        flash(
            "الولاية مطلوبة.",
            "danger",
        )
        return redirect(
            url_for("auth.checkout")
        )

    if not delivery_phone:
        flash(
            "رقم الهاتف مطلوب.",
            "danger",
        )
        return redirect(
            url_for("auth.checkout")
        )

    db = get_db()

    try:
        db.execute("BEGIN IMMEDIATE")

        fresh_items = Cart.get_items(
            user["id"]
        )

        if not fresh_items:
            db.rollback()
            flash(
                "السلة فارغة.",
                "warning",
            )
            return redirect(
                url_for("auth.cart")
            )

        order_total = 0

        for item in fresh_items:

            quantity = safe_int(
                row_value(
                    item,
                    "cart_quantity",
                    1,
                ),
                1,
                1,
            )

            product_id = item["product_id"]

            product = Product.find_by_id(
                product_id
            )

            if not product:
                raise ValueError(
                    "PRODUCT_NOT_FOUND"
                )

            availability = row_value(
                product,
                "availability_type",
                "available_now",
            )

            available_quantity = safe_int(
                row_value(
                    product,
                    "quantity",
                    0,
                ),
                0,
                0,
            )

            purchase_mode = row_value(
                item,
                "purchase_mode",
                "ready_stock",
            )

            if (
                purchase_mode == "ready_stock"
                and availability != "made_to_order"
            ):
                if quantity > available_quantity:
                    raise ValueError(
                        "INSUFFICIENT_STOCK"
                    )

                Product.decrease_stock(
                    product_id,
                    quantity,
                )

            unit_price = product_unit_price(
                product
            )

            order_total += (
                unit_price * quantity
            )

        order_id = Order.create(
            user_id=user["id"],
            total_amount=order_total,
            delivery_address=delivery_address,
            delivery_wilaya=delivery_wilaya,
            delivery_phone=delivery_phone,
            status="pending",
        )

        for item in fresh_items:

            quantity = safe_int(
                row_value(
                    item,
                    "cart_quantity",
                    1,
                ),
                1,
                1,
            )

            product = Product.find_by_id(
                item["product_id"]
            )

            purchase_mode = row_value(
                item,
                "purchase_mode",
                "ready_stock",
            )

            preparation_time = safe_int(
                row_value(
                    product,
                    "preparation_time_minutes",
                    0,
                ),
                0,
                0,
            )

            OrderItem.create(
                order_id=order_id,
                product_id=item["product_id"],
                store_id=item["store_id"],
                quantity=quantity,
                price=product_unit_price(product),
                purchase_mode=purchase_mode,
                preparation_time_minutes=preparation_time,
            )

            try:
                store = Store.find_by_id(
                    item["store_id"]
                )

                if store:
                    Notification.create(
                        store["user_id"],
                        "طلب جديد",
                        f"لديك طلب جديد رقم #{order_id}.",
                    )
            except Exception:
                pass

        Cart.clear(
            user["id"]
        )

        db.commit()

        flash(
            "تم إرسال طلبك بنجاح.",
            "success",
        )

        return redirect(
            url_for(
                "auth.order_detail",
                order_id=order_id,
            )
        )

    except ValueError as exc:

        db.rollback()

        if str(exc) == "INSUFFICIENT_STOCK":
            flash(
                "الكمية المطلوبة أكبر من المخزون المتاح.",
                "danger",
            )
        else:
            flash(
                "تعذر إنشاء الطلب.",
                "danger",
            )

        return redirect(
            url_for("auth.cart")
        )

    except Exception as exc:

        db.rollback()

        current_app.logger.exception(
            "Checkout error: %s",
            exc,
        )

        flash(
            "حدث خطأ أثناء تأكيد الطلب.",
            "danger",
        )

        return redirect(
            url_for("auth.cart")
        )


# =========================================================
# FAVORITES
# =========================================================

@auth.route("/favorites")
@login_required
def favorites():

    user = current_user()

    products = Favorite.all(
        user["id"]
    )

    return render_template(
        "favorites.html",
        user=user,
        products=products,
    )


@auth.route("/favorites/toggle", methods=["POST"])
@login_required
def toggle_favorite():

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id"),
        0,
        1,
    )

    if not Product.find_by_id(product_id):
        return jsonify(
            {
                "ok": False,
                "message": "المنتج غير موجود.",
            }
        ), 404

    try:
        if Favorite.exists(
            user["id"],
            product_id,
        ):
            Favorite.remove(
                user["id"],
                product_id,
            )
            state = False
        else:
            Favorite.add(
                user["id"],
                product_id,
            )
            state = True

        return jsonify(
            {
                "ok": True,
                "favorite": state,
            }
        )

    except Exception:
        return jsonify(
            {
                "ok": False,
                "message": "تعذر تحديث المفضلة.",
            }
        ), 500


# =========================================================
# MESSAGES
# =========================================================

@auth.route("/messages")
@login_required
def messages():

    user = current_user()

    conversations = Message.conversations(
        user["id"]
    )

    return render_template(
        "messages.html",
        user=user,
        conversations=conversations,
    )


@auth.route("/messages/<int:user_id>")
@login_required
def chat(user_id):

    user = current_user()

    if user_id == user["id"]:
        abort(400)

    other_user = User.find_by_id(
        user_id
    )

    if not other_user:
        abort(404)

    product_id = safe_int(
        request.args.get("product_id"),
        0,
        1,
    ) or None

    product = None

    if product_id:
        product = Product.find_by_id(
            product_id
        )

    conversation = Message.between(
        user["id"],
        user_id,
        product_id,
    )

    Message.mark_as_read(
        user["id"],
        user_id,
        product_id,
    )

    return render_template(
        "chat.html",
        user=user,
        other_user=other_user,
        messages=conversation,
        product=product,
        product_id=product_id,
    )


@auth.route("/messages/send", methods=["POST"])
@login_required
def send_message():

    user = current_user()

    receiver_id = safe_int(
        request.form.get("receiver_id"),
        0,
        1,
    )

    product_id = safe_int(
        request.form.get("product_id"),
        0,
        1,
    ) or None

    body = request.form.get(
        "body",
        "",
    ).strip()

    if not receiver_id or not body:
        return jsonify(
            {
                "ok": False,
                "message": "الرسالة فارغة.",
            }
        ), 400

    if receiver_id == user["id"]:
        return jsonify(
            {
                "ok": False,
                "message": "لا يمكنك مراسلة نفسك.",
            }
        ), 400

    if BlockedUser.is_blocked(
        user["id"],
        receiver_id,
    ):
        return jsonify(
            {
                "ok": False,
                "message": "لا يمكن إرسال الرسالة.",
            }
        ), 403

    try:
        message_id = Message.create(
            sender_id=user["id"],
            receiver_id=receiver_id,
            body=body,
            product_id=product_id,
        )

        Notification.create(
            receiver_id,
            "رسالة جديدة",
            f"لديك رسالة جديدة من {user['full_name']}.",
        )

        return jsonify(
            {
                "ok": True,
                "message_id": message_id,
            }
        )

    except Exception:
        return jsonify(
            {
                "ok": False,
                "message": "تعذر إرسال الرسالة.",
            }
        ), 500


# =========================================================
# CHAT SETTINGS
# =========================================================

@auth.route("/chat/settings", methods=["GET", "POST"])
@login_required
def chat_settings():

    user = current_user()

    if request.method == "GET":

        settings = ChatSettings.get(
            user["id"]
        )

        return render_template(
            "chat_settings.html",
            user=user,
            settings=settings,
        )

    language = request.form.get(
        "language",
        "ar",
    )

    voice_type = request.form.get(
        "voice_type",
        "female",
    )

    style = request.form.get(
        "style",
        "friendly",
    )

    voice_enabled = bool(
        request.form.get(
            "voice_enabled"
        )
    )

    try:
        ChatSettings.update(
            user["id"],
            voice_type=voice_type,
            voice_enabled=voice_enabled,
            language=language,
            style=style,
        )

        flash(
            "تم حفظ إعدادات المحادثة.",
            "success",
        )

    except Exception:
        flash(
            "تعذر حفظ الإعدادات.",
            "danger",
        )

    return redirect(
        url_for("auth.chat_settings")
    )


# =========================================================
# COMPLAINTS
# =========================================================

@auth.route("/complaints", methods=["GET", "POST"])
@login_required
def complaints():

    user = current_user()

    if request.method == "POST":

        subject = request.form.get(
            "subject",
            "",
        ).strip()

        body = request.form.get(
            "message",
            "",
        ).strip()

        order_id = safe_int(
            request.form.get("order_id"),
            0,
            1,
        ) or None

        if not subject or not body:
            flash(
                "الموضوع والرسالة مطلوبان.",
                "danger",
            )
            return redirect(
                url_for("auth.complaints")
            )

        try:
            Complaint.create(
                user_id=user["id"],
                subject=subject,
                body=body,
                order_id=order_id,
            )

            flash(
                "تم إرسال الشكوى إلى فريق الدعم.",
                "success",
            )

        except Exception:
            flash(
                "تعذر إرسال الشكوى.",
                "danger",
            )

        return redirect(
            url_for("auth.complaints")
        )

    complaints_list = Complaint.by_user(
        user["id"]
    )

    return render_template(
        "complaints.html",
        user=user,
        complaints=complaints_list,
    )


# =========================================================
# SELLER DASHBOARD
# =========================================================

@auth.route("/seller")
@seller_required
def seller():

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

    if not store:
        abort(404)

    products = Product.by_store(
        store["id"]
    )

    return render_template(
        "seller.html",
        user=user,
        store=store,
        products=products,
    )


# =========================================================
# SELLER STORE EDIT
# =========================================================

@auth.route("/seller/edit", methods=["GET", "POST"])
@seller_required
def seller_edit():

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

    if not store:
        abort(404)

    if request.method == "GET":
        return render_template(
            "seller_edit.html",
            user=user,
            store=store,
        )

    name = request.form.get(
        "name",
        "",
    ).strip()

    description = request.form.get(
        "description",
        "",
    ).strip()

    phone = request.form.get(
        "phone",
        "",
    ).strip()

    wilaya = request.form.get(
        "wilaya",
        "",
    ).strip()

    municipality = request.form.get(
        "municipality",
        "",
    ).strip()

    logo = request.form.get(
        "logo",
        "",
    ).strip()

    cover_image = request.form.get(
        "cover_image",
        "",
    ).strip()

    try:
        Store.update(
            store["id"],
            name=name or store["name"],
            description=description,
            phone=phone or None,
            wilaya=wilaya or None,
            municipality=municipality or None,
            logo=logo or None,
            cover_image=cover_image or None,
        )

        flash(
            "تم تحديث المتجر.",
            "success",
        )

    except Exception:
        flash(
            "تعذر تحديث المتجر.",
            "danger",
        )

    return redirect(
        url_for("auth.seller")
    )


# =========================================================
# SELLER CREATE PRODUCT
# =========================================================

@auth.route("/seller/products/new", methods=["GET", "POST"])
@approved_seller_required
def new_product():

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

    if not store:
        abort(404)

    if request.method == "GET":
        return render_template(
            "seller_product_form.html",
            user=user,
            store=store,
            product=None,
            mode="create",
        )

    name = request.form.get(
        "name",
        "",
    ).strip()

    description = request.form.get(
        "description",
        "",
    ).strip()

    category = request.form.get(
        "category",
        "",
    ).strip()

    brand = request.form.get(
        "brand",
        "",
    ).strip()

    price = safe_float(
        request.form.get("price"),
        0,
        0,
    )

    discount = safe_float(
        request.form.get("discount"),
        0,
        0,
    )

    quantity = safe_int(
        request.form.get("quantity"),
        0,
        0,
    )

    availability_type = request.form.get(
        "availability_type",
        "available_now",
    ).strip()

    if availability_type not in (
        "available_now",
        "made_to_order",
        "both",
    ):
        availability_type = "available_now"

    preparation_time_minutes = safe_int(
        request.form.get(
            "preparation_time_minutes"
        ),
        0,
        0,
    )

    colors = request.form.get(
        "colors",
        "",
    ).strip()

    sizes = request.form.get(
        "sizes",
        "",
    ).strip()

    images = request.form.get(
        "images",
        "",
    ).strip()

    video = request.form.get(
        "video",
        "",
    ).strip()

    delivery_wilayas = request.form.get(
        "delivery_wilayas",
        "",
    ).strip()

    if not name:
        flash(
            "اسم المنتج مطلوب.",
            "danger",
        )
        return redirect(
            url_for("auth.new_product")
        )

    if price <= 0:
        flash(
            "السعر يجب أن يكون أكبر من صفر.",
            "danger",
        )
        return redirect(
            url_for("auth.new_product")
        )

    if availability_type == "made_to_order":
        quantity = 0

    try:
        Product.create(
            store_id=store["id"],
            name=name,
            description=description,
            price=price,
            discount=discount,
            quantity=quantity,
            category=category,
            brand=brand,
            images=images,
            video=video,
            delivery_wilayas=delivery_wilayas,
            availability_type=availability_type,
            preparation_time_minutes=preparation_time_minutes,
            colors=colors,
            sizes=sizes,
        )

        flash(
            "تم نشر المنتج.",
            "success",
        )

        return redirect(
            url_for("auth.seller")
        )

    except Exception as exc:

        current_app.logger.exception(
            "Product creation error: %s",
            exc,
        )

        flash(
            "تعذر نشر المنتج.",
            "danger",
        )

        return redirect(
            url_for("auth.new_product")
        )


# =========================================================
# SELLER EDIT PRODUCT
# =========================================================

@auth.route(
    "/seller/products/<int:product_id>/edit",
    methods=["GET", "POST"],
)
@approved_seller_required
def edit_product(product_id):

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

    if not store:
        abort(404)

    product = Product.find_by_id(
        product_id
    )

    if not product:
        abort(404)

    if product["store_id"] != store["id"]:
        abort(403)

    if request.method == "GET":
        return render_template(
            "seller_edit.html",
            user=user,
            store=store,
            product=product,
        )

    name = request.form.get(
        "name",
        row_value(product, "name", ""),
    ).strip()

    description = request.form.get(
        "description",
        row_value(product, "description", ""),
    ).strip()

    category = request.form.get(
        "category",
        row_value(product, "category", ""),
    ).strip()

    brand = request.form.get(
        "brand",
        row_value(product, "brand", ""),
    ).strip()

    price = safe_float(
        request.form.get(
            "price",
            product["price"],
        ),
        product["price"],
        0,
    )

    discount = safe_float(
        request.form.get(
            "discount",
            product["discount"],
        ),
        product["discount"],
        0,
    )

    quantity = safe_int(
        request.form.get(
            "quantity",
            product["quantity"],
        ),
        product["quantity"],
        0,
    )

    availability_type = request.form.get(
        "availability_type",
        row_value(
            product,
            "availability_type",
            "available_now",
        ),
    )

    if availability_type not in (
        "available_now",
        "made_to_order",
        "both",
    ):
        availability_type = "available_now"

    if availability_type == "made_to_order":
        quantity = 0

    preparation_time_minutes = safe_int(
        request.form.get(
            "preparation_time_minutes",
            row_value(
                product,
                "preparation_time_minutes",
                0,
            ),
        ),
        0,
        0,
    )

    colors = request.form.get(
        "colors",
        row_value(product, "colors", ""),
    ).strip()

    sizes = request.form.get(
        "sizes",
        row_value(product, "sizes", ""),
    ).strip()

    images = request.form.get(
        "images",
        row_value(product, "images", ""),
    ).strip()

    video = request.form.get(
        "video",
        row_value(product, "video", ""),
    ).strip()

    delivery_wilayas = request.form.get(
        "delivery_wilayas",
        row_value(
            product,
            "delivery_wilayas",
            "",
        ),
    ).strip()

    try:

        Product.update(
            product_id,
            name=name,
            description=description,
            price=price,
            discount=discount,
            quantity=quantity,
            category=category,
            brand=brand,
            images=images,
            video=video,
            delivery_wilayas=delivery_wilayas,
            availability_type=availability_type,
            preparation_time_minutes=preparation_time_minutes,
            colors=colors,
            sizes=sizes,
        )

        flash(
            "تم تحديث المنتج.",
            "success",
        )

    except Exception as exc:

        current_app.logger.exception(
            "Product update error: %s",
            exc,
        )

        flash(
            "تعذر تحديث المنتج.",
            "danger",
        )

    return redirect(
        url_for("auth.seller")
    )


# =========================================================
# REWARDS / CARDS
# =========================================================

@auth.route("/cards")
@login_required
def cards():

    user = current_user()

    cards_list = RewardCard.by_user(
        user["id"]
    )

    return render_template(
        "cards.html",
        user=user,
        cards=cards_list,
    )


@auth.route("/cards/use", methods=["POST"])
@login_required
def use_card():

    user = current_user()

    code = request.form.get(
        "code",
        "",
    ).strip().upper()

    if not code:
        flash(
            "رمز البطاقة مطلوب.",
            "danger",
        )
        return redirect(
            url_for("auth.cards")
        )

    try:

        card = RewardCard.find_by_code(
            code
        )

        if not card:
            flash(
                "البطاقة غير موجودة.",
                "danger",
            )
            return redirect(
                url_for("auth.cards")
            )

        if card["user_id"] != user["id"]:
            abort(403)

        if card["used"]:
            flash(
                "هذه البطاقة مستعملة من قبل.",
                "warning",
            )
            return redirect(
                url_for("auth.cards")
            )

        expires_at = row_value(
            card,
            "expires_at",
        )

        if expires_at:
            from datetime import datetime

            try:
                expiry = datetime.fromisoformat(
                    str(expires_at)
                )

                if expiry < datetime.now():
                    flash(
                        "انتهت صلاحية هذه البطاقة.",
                        "warning",
                    )
                    return redirect(
                        url_for("auth.cards")
                    )
            except ValueError:
                pass

        RewardCard.use(
            code,
            user["id"],
        )

        flash(
            "تم استعمال البطاقة.",
            "success",
        )

    except Exception:
        flash(
            "تعذر استعمال البطاقة.",
            "danger",
        )

    return redirect(
        url_for("auth.cards")
    )


# =========================================================
# REFERRALS
# =========================================================

@auth.route("/referral")
@login_required
def referral():

    user = current_user()

    referrals = Referral.by_inviter(
        user["id"]
    )

    return render_template(
        "referral.html",
        user=user,
        referrals=referrals,
    )


# =========================================================
# SEARCH
# =========================================================

class ProductSearch:

    @staticmethod
    def latest(limit=24):

        db = get_db()

        return db.execute(
            """
            SELECT
                p.*,
                s.name AS store_name,
                s.trust_score AS store_trust_score,
                s.verification_status AS store_verification_status
            FROM products p
            JOIN stores s
                ON s.id = p.store_id
            WHERE p.active = 1
            ORDER BY p.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    @staticmethod
    def search(query, limit=48):

        db = get_db()

        q = f"%{query.strip()}%"

        return db.execute(
            """
            SELECT
                p.*,
                s.name AS store_name,
                s.trust_score AS store_trust_score,
                s.verification_status AS store_verification_status
            FROM products p
            JOIN stores s
                ON s.id = p.store_id
            WHERE
                p.active = 1
                AND (
                    p.name LIKE ?
                    OR p.description LIKE ?
                    OR p.category LIKE ?
                    OR p.brand LIKE ?
                )
            ORDER BY p.created_at DESC
            LIMIT ?
            """,
            (q, q, q, q, limit),
        ).fetchall()


@auth.route("/search")
def search():

    query = request.args.get(
        "q",
        "",
    ).strip()

    products = []

    if query:
        products = ProductSearch.search(
            query
        )

    return render_template(
        "index.html",
        products=products,
        query=query,
        user=current_user(),
    )


# =========================================================
# PRODUCT DETAIL
# =========================================================

@auth.route("/product/<int:product_id>")
def product_detail(product_id):

    product = Product.find_by_id(
        product_id
    )

    if not product:
        abort(404)

    user = current_user()

    user_id = (
        user["id"]
        if user
        else None
    )

    try:
        ProductView.add(
            product_id,
            user_id,
        )
    except Exception:
        pass

    reviews = Review.by_product(
        product_id
    )

    store = Store.find_by_id(
        product["store_id"]
    )

    following = False

    if user and store:
        try:
            following = StoreFollower.is_following(
                user["id"],
                store["id"],
            )
        except Exception:
            following = False

    is_favorite = False

    if user:
        try:
            is_favorite = Favorite.exists(
                user["id"],
                product_id,
            )
        except Exception:
            pass

    return render_template(
        "product.html",
        product=product,
        store=store,
        reviews=reviews,
        user=user,
        is_favorite=is_favorite,
        following=following,
    )


# =========================================================
# REVIEWS
# =========================================================

@auth.route("/reviews/add", methods=["POST"])
@login_required
def add_review():

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id"),
        0,
        1,
    )

    order_id = safe_int(
        request.form.get("order_id"),
        0,
        1,
    )

    order_item_id = safe_int(
        request.form.get("order_item_id"),
        0,
        1,
    )

    rating = safe_int(
        request.form.get("rating"),
        0,
        1,
        5,
    )

    comment = request.form.get(
        "comment",
        "",
    ).strip()

    if not product_id or not order_id or not rating:
        flash(
            "بيانات التقييم ناقصة.",
            "danger",
        )
        return redirect(
            request.referrer
            or url_for("auth.index")
        )

    try:

        if not Review.can_review(
            user["id"],
            product_id,
            order_id,
        ):
            flash(
                "لا يمكنك تقييم هذا المنتج بهذا الطلب.",
                "warning",
            )
            return redirect(
                request.referrer
                or url_for("auth.index")
            )

        Review.create(
            user_id=user["id"],
            product_id=product_id,
            order_id=order_id,
            order_item_id=order_item_id or None,
            rating=rating,
            comment=comment,
        )

        flash(
            "شكراً على تقييمك.",
            "success",
        )

    except Exception as exc:

        current_app.logger.exception(
            "Review error: %s",
            exc,
        )

        flash(
            "تعذر إضافة التقييم.",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for(
            "auth.product_detail",
            product_id=product_id,
        )
    )


# =========================================================
# PRICE ALERT
# =========================================================

@auth.route("/price-alerts", methods=["POST"])
@login_required
def price_alert():

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id"),
        0,
        1,
    )

    target_price = safe_float(
        request.form.get("target_price"),
        0,
        0,
    )

    if not product_id or target_price <= 0:
        flash(
            "أدخلي سعراً صحيحاً.",
            "danger",
        )
        return redirect(
            request.referrer
            or url_for("auth.index")
        )

    if not Product.find_by_id(product_id):
        abort(404)

    try:

        PriceAlert.create(
            user_id=user["id"],
            product_id=product_id,
            target_price=target_price,
        )

        flash(
            "تم تفعيل تنبيه السعر.",
            "success",
        )

    except Exception:
        flash(
            "تعذر إنشاء التنبيه.",
            "danger",
        )

    return redirect(
        request.referrer
        or url_for(
            "auth.product_detail",
            product_id=product_id,
        )
    )


# =========================================================
# ADMIN
# =========================================================

@auth.route("/admin")
@admin_required
def admin_dashboard():

    user = current_user()

    return render_template(
        "admin.html",
        user=user,
    )


@auth.route("/admin/api/stats")
@admin_required
def admin_stats():

    db = get_db()

    users = db.execute(
        "SELECT COUNT(*) AS count FROM users"
    ).fetchone()["count"]

    sellers = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'seller'
        """
    ).fetchone()["count"]

    approved_sellers = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'seller'
        AND seller_verification_status = 'approved'
        """
    ).fetchone()["count"]

    products = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM products
        WHERE active = 1
        """
    ).fetchone()["count"]

    orders = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM orders
        """
    ).fetchone()["count"]

    complaints = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM complaints
        WHERE status IN ('open', 'in_review')
        """
    ).fetchone()["count"]

    return jsonify(
        {
            "ok": True,
            "users": users,
            "sellers": sellers,
            "approved_sellers": approved_sellers,
            "products": products,
            "orders": orders,
            "complaints": complaints,
        }
    )


# =========================================================
# STATUS
# =========================================================

@auth.route("/api/status")
def api_status():

    return jsonify(
        {
            "ok": True,
            "app": "DZ MARKET",
            "status": "online",
            "version": "1.0",
        }
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@auth.errorhandler(403)
def forbidden(error):

    try:
        return render_template(
            "403.html"
        ), 403
    except Exception:
        return (
            "<h1>403 - Access denied</h1>",
            403,
        )


@auth.errorhandler(404)
def not_found(error):

    try:
        return render_template(
            "404.html"
        ), 404
    except Exception:
        return (
            "<h1>404 - Page not found</h1>",
            404,
        )


@auth.errorhandler(500)
def internal_error(error):

    try:
        return render_template(
            "500.html"
        ), 500
    except Exception:
        return (
            "<h1>500 - Server error</h1>",
            500,
        )

