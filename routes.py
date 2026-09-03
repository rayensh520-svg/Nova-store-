# routes.py
# ============================================================
# DZ MARKET 🇩🇿
# Main Application Routes
# ============================================================

import os
import re
import sqlite3
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
    abort
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

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
    ChatSettings
)


# ============================================================
# BLUEPRINT
# ============================================================

auth = Blueprint(
    "auth",
    __name__
)


# ============================================================
# HELPERS
# ============================================================

def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return User.find_by_id(user_id)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not current_user():
            flash(
                "سجلي الدخول أولاً للمتابعة.",
                "warning"
            )
            return redirect(
                url_for("auth.login")
            )

        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user = current_user()

        if not user or user["role"] != "admin":
            abort(403)

        return view(*args, **kwargs)

    return wrapped_view


def seller_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user = current_user()

        if not user or user["role"] != "seller":
            abort(403)

        return view(*args, **kwargs)

    return wrapped_view


def approved_seller_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user = current_user()

        if not user or user["role"] != "seller":
            abort(403)

        if user["seller_verification_status"] != "approved":
            flash(
                "حساب البائع مازال قيد المراجعة.",
                "warning"
            )
            return redirect(
                url_for("auth.seller")
            )

        return view(*args, **kwargs)

    return wrapped_view


def row_value(row, key, default=None):
    if row is None:
        return default

    try:
        value = row[key]
    except (KeyError, IndexError, TypeError):
        return default

    return default if value is None else value


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_password(password):
    """
    Password policy:
    - at least 8 characters
    - one letter
    - one number
    - one special character
    """

    if not password or len(password) < 8:
        return False

    if not re.search(r"[A-Za-z]", password):
        return False

    if not re.search(r"\d", password):
        return False

    if not re.search(r"[^A-Za-z0-9]", password):
        return False

    return True


def get_cart_total(items):
    total = 0

    for item in items:
        price = safe_float(item["price"])
        discount = safe_float(
            item["discount"],
            0
        )

        final_price = max(
            price - discount,
            0
        )

        total += (
            final_price *
            safe_int(item["quantity"], 0)
        )

    return round(total, 2)


def normalize_list(value):
    if not value:
        return ""

    parts = [
        part.strip()
        for part in value.split(",")
        if part.strip()
    ]

    return ",".join(parts)


# ============================================================
# HOME
# ============================================================

@auth.route("/")
def index():

    products = ProductSearch.latest(
        limit=30
    )

    return render_template(
        "index.html",
        products=products
    )


# ============================================================
# REGISTER
# ============================================================

@auth.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user():
        return redirect(
            url_for("auth.account")
        )

    if request.method == "POST":

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

        wilaya = request.form.get(
            "wilaya",
            ""
        ).strip()

        municipality = request.form.get(
            "municipality",
            ""
        ).strip()

        store_name = request.form.get(
            "store_name",
            ""
        ).strip()

        activity_type = request.form.get(
            "activity_type",
            ""
        ).strip()

        verification_note = request.form.get(
            "verification_note",
            ""
        ).strip()

        referral_code = request.form.get(
            "referral_code",
            ""
        ).strip()

        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if not full_name:
            flash(
                "الاسم الكامل مطلوب.",
                "danger"
            )
            return render_template(
                "register.html"
            )

        if not email or "@" not in email:
            flash(
                "أدخلي بريد إلكتروني صحيح.",
                "danger"
            )
            return render_template(
                "register.html"
            )

        if not validate_password(password):
            flash(
                "كلمة السر لازم تكون 8 أحرف على الأقل وتحتوي على حرف ورقم ورمز.",
                "danger"
            )
            return render_template(
                "register.html"
            )

        if password != confirm_password:
            flash(
                "كلمتا السر غير متطابقتين.",
                "danger"
            )
            return render_template(
                "register.html"
            )

        if role not in ("buyer", "seller"):
            role = "buyer"

        # ----------------------------------------------------
        # Existing account
        # ----------------------------------------------------

        if User.find_by_email(email):
            flash(
                "هذا البريد الإلكتروني مستعمل من قبل.",
                "danger"
            )
            return render_template(
                "register.html"
            )

        # ----------------------------------------------------
        # Referral
        # ----------------------------------------------------

        referred_by = None

        if referral_code:
            referrer = User.find_by_referral_code(
                referral_code
            )

            if referrer:
                referred_by = referrer["id"]

        # ----------------------------------------------------
        # Create user
        # ----------------------------------------------------

        password_hash = generate_password_hash(
            password
        )

        try:

            user = User.create(
                full_name=full_name,
                email=email,
                password_hash=password_hash,
                phone=phone or None,
                role=role,
                wilaya=wilaya or None,
                municipality=municipality or None,
                seller_activity_type=(
                    activity_type
                    if role == "seller"
                    else None
                ),
                seller_verification_note=(
                    verification_note
                    if role == "seller"
                    else None
                ),
                referred_by=referred_by
            )

            # ------------------------------------------------
            # Seller store
            # ------------------------------------------------

            if role == "seller":

                if not store_name:
                    flash(
                        "اسم المتجر مطلوب للبائع.",
                        "danger"
                    )

                    # Remove just-created user
                    db = get_db()

                    db.execute(
                        """
                        DELETE FROM users
                        WHERE id = ?
                        """,
                        (user["id"],)
                    )

                    db.commit()

                    return render_template(
                        "register.html"
                    )

                Store.create(
                    user_id=user["id"],
                    name=store_name,
                    phone=phone or None,
                    wilaya=wilaya or None,
                    municipality=municipality or None
                )

            # ------------------------------------------------
            # Referral record
            # ------------------------------------------------

            if referred_by:
                try:
                    Referral.create(
                        inviter_id=referred_by,
                        invited_user_id=user["id"]
                    )
                except sqlite3.IntegrityError:
                    pass

            flash(
                "تم إنشاء الحساب بنجاح 🇩🇿",
                "success"
            )

            if role == "seller":
                flash(
                    "طلب البائع أُرسل للمراجعة قبل تفعيل البيع.",
                    "info"
                )

            return redirect(
                url_for("auth.login")
            )

        except sqlite3.IntegrityError:
            flash(
                "تعذر إنشاء الحساب. تأكدي أن المعلومات غير مستعملة من قبل.",
                "danger"
            )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@auth.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user():
        return redirect(
            url_for("auth.account")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.find_by_email(
            email
        )

        if not user:
            flash(
                "البريد الإلكتروني أو كلمة السر غير صحيحة.",
                "danger"
            )
            return render_template(
                "login.html"
            )

        if not user["is_active"]:
            flash(
                "هذا الحساب غير مفعل.",
                "danger"
            )
            return render_template(
                "login.html"
            )

        if not check_password_hash(
            user["password"],
            password
        ):
            flash(
                "البريد الإلكتروني أو كلمة السر غير صحيحة.",
                "danger"
            )
            return render_template(
                "login.html"
            )

        session.clear()

        session["user_id"] = user["id"]
        session["role"] = user["role"]

        flash(
            "مرحبا بك في DZ MARKET 🇩🇿",
            "success"
        )

        return redirect(
            url_for("auth.account")
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@auth.route("/logout")
def logout():

    session.clear()

    flash(
        "تم تسجيل الخروج.",
        "success"
    )

    return redirect(
        url_for("auth.index")
    )


# ============================================================
# ACCOUNT
# ============================================================

@auth.route("/account")
@login_required
def account():

    user = current_user()

    return render_template(
        "account.html",
        user=user
    )


# ============================================================
# ORDERS
# ============================================================

@auth.route("/orders")
@login_required
def orders():

    user = current_user()

    orders_list = Order.by_user(
        user["id"]
    )

    return render_template(
        "orders.html",
        orders=orders_list
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

    if (
        order["user_id"] != user["id"]
        and user["role"] != "admin"
    ):
        abort(403)

    items = OrderItem.by_order(
        order_id
    )

    return render_template(
        "order_detail.html",
        order=order,
        items=items
    )


# ============================================================
# CART
# ============================================================

@auth.route("/cart")
@login_required
def cart():

    user = current_user()

    items = Cart.get_items(
        user["id"]
    )

    total = get_cart_total(
        items
    )

    return render_template(
        "cart.html",
        items=items,
        total=total
    )


@auth.route(
    "/cart/add",
    methods=["POST"]
)
@login_required
def cart_add():

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id")
    )

    quantity = safe_int(
        request.form.get("quantity"),
        1
    )

    purchase_mode = request.form.get(
        "purchase_mode",
        "ready_stock"
    )

    if quantity <= 0:
        flash(
            "الكمية غير صحيحة.",
            "danger"
        )
        return redirect(
            request.referrer
            or url_for("auth.index")
        )

    try:

        Cart.add(
            user_id=user["id"],
            product_id=product_id,
            quantity=quantity,
            purchase_mode=purchase_mode
        )

        flash(
            "تمت إضافة المنتج للسلة 🛒",
            "success"
        )

    except ValueError as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        request.referrer
        or url_for("auth.cart")
    )


@auth.route(
    "/cart/update",
    methods=["POST"]
)
@login_required
def cart_update():

    user = current_user()

    cart_item_id = safe_int(
        request.form.get("cart_item_id")
    )

    quantity = safe_int(
        request.form.get("quantity")
    )

    try:

        Cart.update(
            user["id"],
            cart_item_id,
            quantity
        )

        flash(
            "تم تحديث السلة.",
            "success"
        )

    except ValueError as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        url_for("auth.cart")
    )


@auth.route(
    "/cart/remove",
    methods=["POST"]
)
@login_required
def cart_remove():

    user = current_user()

    cart_item_id = safe_int(
        request.form.get("cart_item_id")
    )

    Cart.remove(
        user["id"],
        cart_item_id
    )

    flash(
        "تم حذف المنتج من السلة.",
        "success"
    )

    return redirect(
        url_for("auth.cart")
    )


@auth.route(
    "/cart/clear",
    methods=["POST"]
)
@login_required
def cart_clear():

    user = current_user()

    Cart.clear(
        user["id"]
    )

    flash(
        "تم تفريغ السلة.",
        "success"
    )

    return redirect(
        url_for("auth.cart")
    )


# ============================================================
# CHECKOUT
# ============================================================

@auth.route(
    "/checkout",
    methods=["GET", "POST"]
)
@login_required
def checkout():

    user = current_user()

    items = Cart.get_items(
        user["id"]
    )

    if not items:
        flash(
            "السلة فارغة.",
            "warning"
        )

        return redirect(
            url_for("auth.cart")
        )

    total = get_cart_total(
        items
    )

    if request.method == "POST":

        address = request.form.get(
            "delivery_address",
            ""
        ).strip()

        wilaya = request.form.get(
            "delivery_wilaya",
            ""
        ).strip()

        phone = request.form.get(
            "delivery_phone",
            ""
        ).strip()

        if not address:
            flash(
                "عنوان التوصيل مطلوب.",
                "danger"
            )
            return render_template(
                "checkout.html",
                items=items,
                total=total
            )

        if not wilaya:
            flash(
                "الولاية مطلوبة.",
                "danger"
            )
            return render_template(
                "checkout.html",
                items=items,
                total=total
            )

        if not phone:
            flash(
                "رقم الهاتف مطلوب.",
                "danger"
            )
            return render_template(
                "checkout.html",
                items=items,
                total=total
            )

        db = get_db()

        try:

            # -----------------------------------------------
            # Start transaction
            # -----------------------------------------------

            db.execute("BEGIN IMMEDIATE")

            fresh_items = db.execute(
                """
                SELECT
                    c.*,
                    p.name,
                    p.price,
                    p.discount,
                    p.quantity AS available_quantity,
                    p.availability_type,
                    p.preparation_time_minutes,
                    p.store_id,
                    p.active
                FROM cart_items c
                JOIN products p
                    ON p.id = c.product_id
                WHERE c.user_id = ?
                """,
                (user["id"],)
            ).fetchall()

            if not fresh_items:
                db.rollback()

                flash(
                    "السلة فارغة.",
                    "warning"
                )

                return redirect(
                    url_for("auth.cart")
                )

            # -----------------------------------------------
            # Validate products and stock
            # -----------------------------------------------

            calculated_total = 0

            for item in fresh_items:

                if not item["active"]:
                    raise ValueError(
                        f"المنتج غير متاح حاليا: {item['name']}"
                    )

                quantity = safe_int(
                    item["quantity"]
                )

                if quantity <= 0:
                    raise ValueError(
                        "الكمية غير صحيحة."
                    )

                if (
                    item["purchase_mode"]
                    == "ready_stock"
                ):

                    if item["availability_type"] not in (
                        "available_now",
                        "both"
                    ):
                        raise ValueError(
                            f"المنتج {item['name']} أصبح متاحا عند الطلب فقط."
                        )

                    if quantity > item["available_quantity"]:
                        raise ValueError(
                            f"الكمية المطلوبة من {item['name']} غير متوفرة."
                        )

                elif (
                    item["purchase_mode"]
                    == "made_to_order"
                ):

                    if item["availability_type"] not in (
                        "made_to_order",
                        "both"
                    ):
                        raise ValueError(
                            f"المنتج {item['name']} لم يعد متاحا عند الطلب."
                        )

                price = max(
                    safe_float(item["price"])
                    - safe_float(item["discount"]),
                    0
                )

                calculated_total += (
                    price * quantity
                )

            calculated_total = round(
                calculated_total,
                2
            )

            # -----------------------------------------------
            # Create order
            # -----------------------------------------------

            cursor = db.execute(
                """
                INSERT INTO orders (
                    user_id,
                    total_amount,
                    delivery_address,
                    delivery_wilaya,
                    delivery_phone,
                    status
                )
                VALUES (?, ?, ?, ?, ?, 'pending')
                """,
                (
                    user["id"],
                    calculated_total,
                    address,
                    wilaya,
                    phone
                )
            )

            order_id = cursor.lastrowid

            # -----------------------------------------------
            # Create order items + reserve stock
            # -----------------------------------------------

            stores_to_notify = set()

            for item in fresh_items:

                quantity = safe_int(
                    item["quantity"]
                )

                price = max(
                    safe_float(item["price"])
                    - safe_float(item["discount"]),
                    0
                )

                db.execute(
                    """
                    INSERT INTO order_items (
                        order_id,
                        product_id,
                        store_id,
                        quantity,
                        price,
                        purchase_mode,
                        preparation_time_minutes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        item["product_id"],
                        item["store_id"],
                        quantity,
                        price,
                        item["purchase_mode"],
                        item["preparation_time_minutes"]
                    )
                )

                # Ready-stock items consume stock.
                if (
                    item["purchase_mode"]
                    == "ready_stock"
                ):

                    cursor = db.execute(
                        """
                        UPDATE products
                        SET quantity = quantity - ?
                        WHERE id = ?
                          AND quantity >= ?
                        """,
                        (
                            quantity,
                            item["product_id"],
                            quantity
                        )
                    )

                    if cursor.rowcount != 1:
                        raise ValueError(
                            f"المخزون تغير أثناء الطلب: {item['name']}"
                        )

                stores_to_notify.add(
                    item["store_id"]
                )

            # -----------------------------------------------
            # Clear cart
            # -----------------------------------------------

            db.execute(
                """
                DELETE FROM cart_items
                WHERE user_id = ?
                """,
                (user["id"],)
            )

            # -----------------------------------------------
            # Commit
            # -----------------------------------------------

            db.commit()

            # -----------------------------------------------
            # Notifications
            # -----------------------------------------------

            for store_id in stores_to_notify:

                store = Store.find_by_id(
                    store_id
                )

                if store:
                    Notification.create(
                        user_id=store["user_id"],
                        title="طلب جديد",
                        body=f"لديك طلب جديد رقم #{order_id}."
                    )

            flash(
                f"تم تأكيد طلبك رقم #{order_id} بنجاح 🎉",
                "success"
            )

            return redirect(
                url_for(
                    "auth.order_detail",
                    order_id=order_id
                )
            )

        except Exception as error:

            try:
                db.rollback()
            except Exception:
                pass

            flash(
                str(error),
                "danger"
            )

    return render_template(
        "checkout.html",
        items=items,
        total=total
    )


# ============================================================
# FAVORITES
# ============================================================

@auth.route("/favorites")
@login_required
def favorites():

    user = current_user()

    products = Favorite.all(
        user["id"]
    )

    return render_template(
        "favorites.html",
        products=products
    )


@auth.route(
    "/favorites/toggle",
    methods=["POST"]
)
@login_required
def favorites_toggle():

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id")
    )

    if Favorite.exists(
        user["id"],
        product_id
    ):
        Favorite.remove(
            user["id"],
            product_id
        )

        status = "removed"

    else:
        Favorite.add(
            user["id"],
            product_id
        )

        status = "added"

    if request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest":

        return jsonify({
            "success": True,
            "status": status
        })

    return redirect(
        request.referrer
        or url_for("auth.index")
    )


# ============================================================
# MESSAGES
# ============================================================

@auth.route("/messages")
@login_required
def messages():

    user = current_user()

    conversations = Message.conversations(
        user["id"]
    )

    return render_template(
        "messages.html",
        conversations=conversations
    )


@auth.route(
    "/messages/<int:user_id>"
)
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

    product_id = request.args.get(
        "product_id"
    )

    product_id = (
        safe_int(product_id)
        if product_id
        else None
    )

    Message.mark_as_read(
        receiver_id=user["id"],
        sender_id=other_user["id"],
        product_id=product_id
    )

    conversation = Message.between(
        user["id"],
        other_user["id"],
        product_id=product_id
    )

    product = None

    if product_id:
        product = Product.find_by_id(
            product_id
        )

    return render_template(
        "chat.html",
        messages=conversation,
        other_user=other_user,
        product=product
    )


@auth.route(
    "/messages/send",
    methods=["POST"]
)
@login_required
def send_message():

    user = current_user()

    receiver_id = safe_int(
        request.form.get("receiver_id")
    )

    body = request.form.get(
        "body",
        ""
    ).strip()

    product_id = request.form.get(
        "product_id"
    )

    product_id = (
        safe_int(product_id)
        if product_id
        else None
    )

    if not receiver_id or not body:
        flash(
            "الرسالة غير صحيحة.",
            "danger"
        )

        return redirect(
            request.referrer
            or url_for("auth.messages")
        )

    try:

        Message.create(
            sender_id=user["id"],
            receiver_id=receiver_id,
            body=body,
            product_id=product_id
        )

        Notification.create(
            user_id=receiver_id,
            title="رسالة جديدة",
            body=f"لديك رسالة جديدة من {user['full_name']}."
        )

    except ValueError as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        request.referrer
        or url_for(
            "auth.chat",
            user_id=receiver_id
        )
    )


# ============================================================
# CHAT SETTINGS
# ============================================================

@auth.route(
    "/chat/settings",
    methods=["GET", "POST"]
)
@login_required
def chat_settings():

    user = current_user()

    if request.method == "POST":

        voice_type = request.form.get(
            "voice_type",
            "female"
        )

        voice_enabled = (
            1
            if request.form.get(
                "voice_enabled"
            )
            else 0
        )

        language = request.form.get(
            "language",
            "ar"
        )

        style = request.form.get(
            "style",
            "friendly"
        )

        try:

            ChatSettings.update(
                user_id=user["id"],
                voice_type=voice_type,
                voice_enabled=voice_enabled,
                language=language,
                style=style
            )

            flash(
                "تم حفظ إعدادات المحادثة.",
                "success"
            )

        except ValueError as error:

            flash(
                str(error),
                "danger"
            )

    settings = ChatSettings.get(
        user["id"]
    )

    return render_template(
        "chat_settings.html",
        settings=settings
    )


# ============================================================
# COMPLAINTS
# ============================================================

@auth.route(
    "/complaints",
    methods=["GET", "POST"]
)
@login_required
def complaints():

    user = current_user()

    if request.method == "POST":

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        body = request.form.get(
            "message",
            ""
        ).strip()

        order_id = request.form.get(
            "order_id"
        )

        order_id = (
            safe_int(order_id)
            if order_id
            else None
        )

        if not subject or not body:
            flash(
                "الموضوع والرسالة مطلوبان.",
                "danger"
            )

        else:

            Complaint.create(
                user_id=user["id"],
                subject=subject,
                body=body,
                order_id=order_id
            )

            flash(
                "تم إرسال الشكوى للإدارة.",
                "success"
            )

            return redirect(
                url_for("auth.complaints")
            )

    complaints_list = Complaint.by_user(
        user["id"]
    )

    return render_template(
        "complaints.html",
        complaints=complaints_list
    )


# ============================================================
# SELLER DASHBOARD
# ============================================================

@auth.route("/seller")
@seller_required
def seller():

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

    products = []

    if store:
        products = Product.by_store(
            store["id"]
        )

    return render_template(
        "seller.html",
        user=user,
        store=store,
        products=products
    )


# ============================================================
# SELLER STORE EDIT
# ============================================================

@auth.route(
    "/seller/edit",
    methods=["GET", "POST"]
)
@seller_required
def seller_edit():

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

    if not store:
        abort(404)

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
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

        if not name:
            flash(
                "اسم المتجر مطلوب.",
                "danger"
            )

        else:

            Store.update(
                store_id=store["id"],
                name=name,
                description=description,
                phone=phone,
                wilaya=wilaya,
                municipality=municipality
            )

            flash(
                "تم تحديث معلومات المتجر.",
                "success"
            )

            return redirect(
                url_for("auth.seller")
            )

    return render_template(
        "seller_edit.html",
        store=store,
        user=user
    )


# ============================================================
# SELLER PRODUCT CREATE
# ============================================================

@auth.route(
    "/seller/products/new",
    methods=["GET", "POST"]
)
@seller_required
def seller_product_new():

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

    if not store:
        abort(404)

    if request.method == "POST":

        try:

            product = Product.create(
                store_id=store["id"],

                name=request.form.get(
                    "name",
                    ""
                ).strip(),

                description=request.form.get(
                    "description",
                    ""
                ).strip(),

                price=safe_float(
                    request.form.get("price")
                ),

                discount=safe_float(
                    request.form.get("discount")
                ),

                quantity=safe_int(
                    request.form.get("quantity")
                ),

                category=request.form.get(
                    "category",
                    ""
                ).strip(),

                brand=request.form.get(
                    "brand",
                    ""
                ).strip(),

                images=normalize_list(
                    request.form.get(
                        "images",
                        ""
                    )
                ),

                video=request.form.get(
                    "video",
                    ""
                ).strip(),

                delivery_wilayas=normalize_list(
                    request.form.get(
                        "delivery_wilayas",
                        ""
                    )
                ),

                availability_type=request.form.get(
                    "availability_type",
                    "available_now"
                ),

                preparation_time_minutes=safe_int(
                    request.form.get(
                        "preparation_time_minutes"
                    )
                ),

                colors=normalize_list(
                    request.form.get(
                        "colors",
                        ""
                    )
                ),

                sizes=normalize_list(
                    request.form.get(
                        "sizes",
                        ""
                    )
                )
            )

            flash(
                "تم نشر المنتج بنجاح.",
                "success"
            )

            return redirect(
                url_for("auth.seller")
            )

        except ValueError as error:

            flash(
                str(error),
                "danger"
            )

    return render_template(
        "seller_product_form.html",
        store=store,
        product=None
    )


# ============================================================
# SELLER PRODUCT EDIT
# ============================================================

@auth.route(
    "/seller/products/<int:product_id>/edit",
    methods=["GET", "POST"]
)
@seller_required
def seller_product_edit(product_id):

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

    if request.method == "POST":

        try:

            Product.update(
                product_id=product_id,

                name=request.form.get(
                    "name",
                    ""
                ).strip(),

                description=request.form.get(
                    "description",
                    ""
                ).strip(),

                price=safe_float(
                    request.form.get("price")
                ),

                discount=safe_float(
                    request.form.get("discount")
                ),

                quantity=safe_int(
                    request.form.get("quantity")
                ),

                category=request.form.get(
                    "category",
                    ""
                ).strip(),

                brand=request.form.get(
                    "brand",
                    ""
                ).strip(),

                images=normalize_list(
                    request.form.get(
                        "images",
                        ""
                    )
                ),

                video=request.form.get(
                    "video",
                    ""
                ).strip(),

                delivery_wilayas=normalize_list(
                    request.form.get(
                        "delivery_wilayas",
                        ""
                    )
                ),

                availability_type=request.form.get(
                    "availability_type",
                    "available_now"
                ),

                preparation_time_minutes=safe_int(
                    request.form.get(
                        "preparation_time_minutes"
                    )
                ),

                colors=normalize_list(
                    request.form.get(
                        "colors",
                        ""
                    )
                ),

                sizes=normalize_list(
                    request.form.get(
                        "sizes",
                        ""
                    )
                ),

                active=(
                    1
                    if request.form.get("active")
                    else 0
                )
            )

            flash(
                "تم تحديث المنتج.",
                "success"
            )

            return redirect(
                url_for("auth.seller")
            )

        except ValueError as error:

            flash(
                str(error),
                "danger"
            )

    return render_template(
        "seller_product_form.html",
        store=store,
        product=product
    )


# ============================================================
# REWARDS / CARDS
# ============================================================

@auth.route("/cards")
@login_required
def cards():

    user = current_user()

    cards_list = RewardCard.by_user(
        user["id"]
    )

    return render_template(
        "cards.html",
        cards=cards_list
    )


@auth.route(
    "/cards/use",
    methods=["POST"]
)
@login_required
def use_card():

    user = current_user()

    code = request.form.get(
        "code",
        ""
    ).strip()

    success = RewardCard.use(
        code,
        user["id"]
    )

    if success:
        flash(
            "تم استعمال البطاقة.",
            "success"
        )
    else:
        flash(
            "البطاقة غير صالحة أو مستعملة.",
            "danger"
        )

    return redirect(
        url_for("auth.cards")
    )


# ============================================================
# REFERRALS
# ============================================================

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
        referrals=referrals
    )


# ============================================================
# PRODUCT SEARCH
# ============================================================

class ProductSearch:

    @staticmethod
    def latest(limit=30):

        db = get_db()

        return db.execute(
            """
            SELECT
                p.*,
                s.name AS store_name,
                s.trust_score,
                s.verification_status
                    AS store_verification_status
            FROM products p
            JOIN stores s
                ON s.id = p.store_id
            WHERE p.active = 1
              AND s.verification_status = 'approved'
            ORDER BY p.created_at DESC, p.id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    @staticmethod
    def search(
        query="",
        category=None,
        wilaya=None,
        limit=50
    ):

        db = get_db()

        sql = """
            SELECT
                p.*,
                s.name AS store_name,
                s.trust_score,
                s.verification_status
                    AS store_verification_status
            FROM products p
            JOIN stores s
                ON s.id = p.store_id
            WHERE p.active = 1
              AND s.verification_status = 'approved'
        """

        params = []

        if query:
            sql += """
                AND (
                    p.name LIKE ?
                    OR p.description LIKE ?
                    OR p.brand LIKE ?
                )
            """

            term = f"%{query}%"

            params.extend([
                term,
                term,
                term
            ])

        if category:
            sql += """
                AND p.category = ?
            """

            params.append(
                category
            )

        if wilaya:
            sql += """
                AND (
                    p.delivery_wilayas LIKE ?
                    OR s.wilaya = ?
                )
            """

            params.extend([
                f"%{wilaya}%",
                wilaya
            ])

        sql += """
            ORDER BY p.created_at DESC, p.id DESC
            LIMIT ?
        """

        params.append(
            limit
        )

        return db.execute(
            sql,
            params
        ).fetchall()


@auth.route("/search")
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    category = request.args.get(
        "category"
    )

    wilaya = request.args.get(
        "wilaya"
    )

    products = ProductSearch.search(
        query=query,
        category=category,
        wilaya=wilaya
    )

    return render_template(
        "index.html",
        products=products,
        search_query=query
    )


# ============================================================
# PRODUCT VIEW / REVIEW
# ============================================================

@auth.route(
    "/product/<int:product_id>"
)
def product_detail(product_id):

    product = Product.find_by_id(
        product_id
    )

    if not product:
        abort(404)

    ProductView.add(
        product_id,
        session.get("user_id")
    )

    reviews = Review.by_product(
        product_id
    )

    return render_template(
        "product.html",
        product=product,
        reviews=reviews
    )


@auth.route(
    "/reviews/add",
    methods=["POST"]
)
@login_required
def add_review():

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id")
    )

    order_id = safe_int(
        request.form.get("order_id")
    )

    order_item_id = request.form.get(
        "order_item_id"
    )

    order_item_id = (
        safe_int(order_item_id)
        if order_item_id
        else None
    )

    rating = safe_int(
        request.form.get("rating")
    )

    comment = request.form.get(
        "comment",
        ""
    ).strip()

    try:

        Review.create(
            user_id=user["id"],
            product_id=product_id,
            order_id=order_id,
            order_item_id=order_item_id,
            rating=rating,
            comment=comment
        )

        flash(
            "تم نشر تقييمك. شكرا على رأيك ❤️",
            "success"
        )

    except ValueError as error:

        flash(
            str(error),
            "danger"
        )

    return redirect(
        request.referrer
        or url_for(
            "auth.order_detail",
            order_id=order_id
        )
    )


# ============================================================
# PRICE ALERTS
# ============================================================

@auth.route(
    "/price-alerts",
    methods=["POST"]
)
@login_required
def create_price_alert():

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id")
    )

    target_price = safe_float(
        request.form.get("target_price")
    )

    if target_price <= 0:
        flash(
            "السعر المستهدف غير صحيح.",
            "danger"
        )

        return redirect(
            request.referrer
            or url_for("auth.index")
        )

    PriceAlert.create(
        user_id=user["id"],
        product_id=product_id,
        target_price=target_price
    )

    flash(
        "تم إنشاء تنبيه السعر.",
        "success"
    )

    return redirect(
        request.referrer
        or url_for("auth.index")
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@auth.route("/admin")
@admin_required
def admin():

    db = get_db()

    stats = {}

    stats["users"] = db.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE role = 'buyer'
        """
    ).fetchone()[0]

    stats["sellers"] = db.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE role = 'seller'
        """
    ).fetchone()[0]

    stats["pending_sellers"] = db.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE role = 'seller'
          AND seller_verification_status = 'pending'
        """
    ).fetchone()[0]

    stats["products"] = db.execute(
        """
        SELECT COUNT(*)
        FROM products
        """
    ).fetchone()[0]

    stats["orders"] = db.execute(
        """
        SELECT COUNT(*)
        FROM orders
        """
    ).fetchone()[0]

    stats["delivered_orders"] = db.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'delivered'
        """
    ).fetchone()[0]

    stats["messages"] = db.execute(
        """
        SELECT COUNT(*)
        FROM messages
        """
    ).fetchone()[0]

    stats["complaints"] = db.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status IN ('open', 'in_review')
        """
    ).fetchone()[0]

    stats["reports"] = db.execute(
        """
        SELECT COUNT(*)
        FROM reports
        WHERE status IN ('open', 'in_review')
        """
    ).fetchone()[0]

    stats["stores"] = db.execute(
        """
        SELECT COUNT(*)
        FROM stores
        """
    ).fetchone()[0]

    revenue = db.execute(
        """
        SELECT
            COALESCE(SUM(total_amount), 0)
        FROM orders
        WHERE status = 'delivered'
        """
    ).fetchone()[0]

    stats["revenue"] = round(
        safe_float(revenue),
        2
    )

    return render_template(
        "admin.html",
        stats=stats
    )


# ============================================================
# ADMIN API STATS
# ============================================================

@auth.route("/admin/api/stats")
@admin_required
def admin_api_stats():

    db = get_db()

    users = db.execute(
        """
        SELECT COUNT(*)
        FROM users
        """
    ).fetchone()[0]

    sellers = db.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE role = 'seller'
        """
    ).fetchone()[0]

    products = db.execute(
        """
        SELECT COUNT(*)
        FROM products
        """
    ).fetchone()[0]

    orders = db.execute(
        """
        SELECT COUNT(*)
        FROM orders
        """
    ).fetchone()[0]

    pending_sellers = db.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE role = 'seller'
          AND seller_verification_status = 'pending'
        """
    ).fetchone()[0]

    complaints = db.execute(
        """
        SELECT COUNT(*)
        FROM complaints
        WHERE status IN ('open', 'in_review')
        """
    ).fetchone()[0]

    reports = db.execute(
        """
        SELECT COUNT(*)
        FROM reports
        WHERE status IN ('open', 'in_review')
        """
    ).fetchone()[0]

    return jsonify({
        "users": users,
        "sellers": sellers,
        "products": products,
        "orders": orders,
        "pending_sellers": pending_sellers,
        "complaints": complaints,
        "reports": reports
    })


# ============================================================
# API STATUS
# ============================================================

@auth.route("/api/status")
def api_status():

    return jsonify({
        "status": "ok",
        "app": "DZ MARKET",
        "version": "1.0"
    })


# ============================================================
# ERROR HANDLERS
# ============================================================

@auth.errorhandler(403)
def forbidden(error):

    return (
        render_template(
            "403.html"
        ),
        403
    )


@auth.errorhandler(404)
def not_found(error):

    return (
        render_template(
            "404.html"
        ),
        404
    )


@auth.errorhandler(500)
def internal_error(error):

    return (
        render_template(
            "500.html"
        ),
        500
    )
