# =========================================================
# DZ MARKET 🇩🇿
# MAIN ROUTES
# Production-Oriented Flask Blueprint
# =========================================================

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import get_connection

from models import (
    User,
    Store,
    Product,
    Favorite,
    Cart,
    Order,
    OrderItem,
    Message,
    Notification,
    Complaint,
    Report,
    RewardCard,
    Referral,
    RewardMilestone,
    ChatSettings
)


# =========================================================
# BLUEPRINT
# =========================================================

auth = Blueprint("auth", __name__)


# =========================================================
# GENERAL HELPERS
# =========================================================

def current_user():
    """Return the currently logged-in user."""

    user_id = session.get("user_id")

    if not user_id:
        return None

    try:
        return User.find_by_id(user_id)
    except Exception:
        return None


def login_required():
    """Protect routes that require authentication."""

    if not session.get("user_id"):
        flash("يجب تسجيل الدخول أولًا.", "error")
        return redirect(url_for("auth.login"))

    return None


def admin_required():
    """Protect administrator routes."""

    user = current_user()

    if not user:
        return redirect(url_for("auth.login"))

    if user["role"] != "admin":
        flash("ليس لديك صلاحية للوصول إلى لوحة الإدارة.", "error")
        return redirect(url_for("home"))

    return None


def seller_required():
    """Protect seller routes."""

    user = current_user()

    if not user:
        return redirect(url_for("auth.login"))

    if user["role"] != "seller":
        flash("هذه الصفحة مخصصة للبائعين فقط.", "error")
        return redirect(url_for("home"))

    return None


def row_value(row, key, default=None):
    """Safely read a sqlite3.Row value."""

    if row is None:
        return default

    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def calculate_cart_total(items):
    """Calculate cart total while respecting product discounts."""

    total = 0.0

    for item in items:

        price = safe_float(row_value(item, "price", 0))
        discount = safe_float(row_value(item, "discount", 0))
        quantity = safe_int(row_value(item, "quantity", 1), 1)

        if discount > 0:
            price = price - (price * discount / 100)

        total += price * quantity

    return round(total, 2)


def get_table_columns(connection, table_name):
    """Return table columns safely."""

    try:
        rows = connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        return {
            row["name"]
            for row in rows
        }

    except Exception:
        return set()


def count_table(connection, table_name):
    """Safe table counter."""

    try:
        result = connection.execute(
            f"SELECT COUNT(*) AS total FROM {table_name}"
        ).fetchone()

        return result["total"] if result else 0

    except Exception:
        return 0


# =========================================================
# HOME
# =========================================================

@auth.route("/")
def index():
    """
    Main marketplace homepage.
    """

    try:
        connection = get_connection()

        products = connection.execute(
            """
            SELECT
                p.*,
                s.name AS store_name
            FROM products p
            LEFT JOIN stores s
                ON s.id = p.store_id
            ORDER BY p.created_at DESC
            LIMIT 30
            """
        ).fetchall()

        connection.close()

    except Exception:
        products = []

    user = current_user()

    return render_template(
        "index.html",
        user=user,
        products=products
    )


# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        phone = request.form.get(
            "phone", ""
        ).strip()

        password = request.form.get(
            "password", ""
        )

        role = request.form.get(
            "role", "buyer"
        ).strip().lower()

        wilaya = request.form.get(
            "wilaya", ""
        ).strip()

        municipality = request.form.get(
            "municipality", ""
        ).strip()

        if not full_name:
            flash("الاسم الكامل مطلوب.", "error")
            return redirect(url_for("auth.register"))

        if not email:
            flash("البريد الإلكتروني مطلوب.", "error")
            return redirect(url_for("auth.register"))

        if not password or len(password) < 6:
            flash(
                "كلمة المرور يجب أن تحتوي على 6 أحرف على الأقل.",
                "error"
            )
            return redirect(url_for("auth.register"))

        if role not in ("buyer", "seller"):
            role = "buyer"

        try:

            existing = User.find_by_email(email)

            if existing:
                flash(
                    "هذا البريد الإلكتروني مسجل مسبقًا.",
                    "error"
                )
                return redirect(url_for("auth.register"))

            User.create(
                full_name=full_name,
                email=email,
                password_hash=generate_password_hash(password),
                phone=phone,
                role=role,
                wilaya=wilaya,
                municipality=municipality
            )

            flash(
                "تم إنشاء حسابك بنجاح 🎉",
                "success"
            )

            return redirect(url_for("auth.login"))

        except Exception as error:

            print("REGISTER ERROR:", error)

            flash(
                "حدث خطأ أثناء إنشاء الحساب.",
                "error"
            )

            return redirect(url_for("auth.register"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        if not email or not password:
            flash(
                "أدخل البريد الإلكتروني وكلمة المرور.",
                "error"
            )
            return redirect(url_for("auth.login"))

        user = User.find_by_email(email)

        if not user:
            flash(
                "بيانات الدخول غير صحيحة.",
                "error"
            )
            return redirect(url_for("auth.login"))

        password_hash = row_value(
            user,
            "password_hash"
        )

        if not password_hash:
            flash(
                "تعذر التحقق من الحساب.",
                "error"
            )
            return redirect(url_for("auth.login"))

        if not check_password_hash(
            password_hash,
            password
        ):
            flash(
                "بيانات الدخول غير صحيحة.",
                "error"
            )
            return redirect(url_for("auth.login"))

        session.clear()

        session["user_id"] = user["id"]
        session["role"] = user["role"]

        flash(
            "مرحبًا بك في DZ MARKET 🇩🇿",
            "success"
        )

        if user["role"] == "admin":
            return redirect(url_for("auth.admin"))

        if user["role"] == "seller":
            return redirect(url_for("auth.seller"))

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


# =========================================================
# ACCOUNT
# =========================================================

@auth.route("/account")
def account():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    return render_template(
        "account.html",
        user=user
    )


# =========================================================
# ORDERS
# =========================================================

@auth.route("/orders")
def orders():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    orders_list = Order.by_user(
        user["id"]
    )

    return render_template(
        "orders.html",
        user=user,
        orders=orders_list
    )


@auth.route("/orders/<int:order_id>")
def order_detail(order_id):

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    order = Order.find_by_id(order_id)

    if not order:
        flash(
            "الطلب غير موجود.",
            "error"
        )
        return redirect(url_for("auth.orders"))

    if order["user_id"] != user["id"] and user["role"] != "admin":
        flash(
            "ليس لديك صلاحية الوصول لهذا الطلب.",
            "error"
        )
        return redirect(url_for("auth.orders"))

    items = OrderItem.by_order(order_id)

    return render_template(
        "order_detail.html",
        user=user,
        order=order,
        items=items
    )


# =========================================================
# CART
# =========================================================

@auth.route("/cart")
def cart():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    items = Cart.get_items(
        user["id"]
    )

    total = calculate_cart_total(items)

    return render_template(
        "cart.html",
        user=user,
        items=items,
        total=total
    )


@auth.route("/cart/add", methods=["POST"])
def cart_add():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id")
    )

    quantity = safe_int(
        request.form.get("quantity", 1),
        1
    )

    if product_id <= 0:
        return jsonify({
            "success": False,
            "message": "المنتج غير صالح."
        }), 400

    if quantity <= 0:
        quantity = 1

    product = Product.find_by_id(
        product_id
    )

    if not product:
        return jsonify({
            "success": False,
            "message": "المنتج غير موجود."
        }), 404

    stock = safe_int(
        row_value(product, "quantity", 0)
    )

    if stock <= 0:
        return jsonify({
            "success": False,
            "message": "هذا المنتج غير متوفر حاليًا."
        }), 400

    quantity = min(quantity, stock)

    try:

        Cart.add(
            user["id"],
            product_id,
            quantity
        )

        return jsonify({
            "success": True,
            "message": "تمت إضافة المنتج إلى السلة 🛒"
        })

    except Exception as error:

        print("CART ADD ERROR:", error)

        return jsonify({
            "success": False,
            "message": "تعذر إضافة المنتج."
        }), 500


@auth.route("/cart/update", methods=["POST"])
def cart_update():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id")
    )

    quantity = safe_int(
        request.form.get("quantity", 1),
        1
    )

    if quantity < 1:
        quantity = 1

    product = Product.find_by_id(
        product_id
    )

    if not product:
        return jsonify({
            "success": False,
            "message": "المنتج غير موجود."
        }), 404

    stock = safe_int(
        row_value(product, "quantity", 0)
    )

    if stock > 0:
        quantity = min(quantity, stock)

    try:

        Cart.update_quantity(
            user["id"],
            product_id,
            quantity
        )

        return jsonify({
            "success": True,
            "quantity": quantity
        })

    except Exception as error:

        print("CART UPDATE ERROR:", error)

        return jsonify({
            "success": False,
            "message": "تعذر تحديث السلة."
        }), 500


@auth.route("/cart/remove", methods=["POST"])
def cart_remove():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id")
    )

    try:

        Cart.remove(
            user["id"],
            product_id
        )

        return jsonify({
            "success": True,
            "message": "تم حذف المنتج من السلة."
        })

    except Exception as error:

        print("CART REMOVE ERROR:", error)

        return jsonify({
            "success": False,
            "message": "تعذر حذف المنتج."
        }), 500


@auth.route("/cart/clear", methods=["POST"])
def cart_clear():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    try:

        Cart.clear(
            user["id"]
        )

        return jsonify({
            "success": True,
            "message": "تم إفراغ السلة."
        })

    except Exception as error:

        print("CART CLEAR ERROR:", error)

        return jsonify({
            "success": False,
            "message": "تعذر إفراغ السلة."
        }), 500


# =========================================================
# CHECKOUT
# =========================================================

@auth.route("/checkout", methods=["GET", "POST"])
def checkout():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    items = Cart.get_items(
        user["id"]
    )

    if not items:
        if request.method == "POST":
            return jsonify({
                "success": False,
                "message": "السلة فارغة."
            }), 400

        flash(
            "السلة فارغة.",
            "error"
        )
        return redirect(url_for("auth.cart"))

    if request.method == "GET":

        total = calculate_cart_total(
            items
        )

        return render_template(
            "checkout.html",
            user=user,
            items=items,
            total=total
        )

    delivery_address = request.form.get(
        "delivery_address",
        ""
    ).strip()

    delivery_wilaya = request.form.get(
        "delivery_wilaya",
        row_value(user, "wilaya", "")
    ).strip()

    delivery_phone = request.form.get(
        "delivery_phone",
        row_value(user, "phone", "")
    ).strip()

    if not delivery_address:
        return jsonify({
            "success": False,
            "message": "عنوان التوصيل مطلوب."
        }), 400

    if not delivery_wilaya:
        return jsonify({
            "success": False,
            "message": "الولاية مطلوبة."
        }), 400

    if not delivery_phone:
        return jsonify({
            "success": False,
            "message": "رقم الهاتف مطلوب."
        }), 400

    total = calculate_cart_total(
        items
    )

    connection = get_connection()

    try:

        order_id = Order.create(
            user_id=user["id"],
            total_amount=total,
            delivery_address=delivery_address,
            delivery_wilaya=delivery_wilaya,
            delivery_phone=delivery_phone
        )

        for item in items:

            product_id = row_value(
                item,
                "product_id"
            )

            quantity = safe_int(
                row_value(item, "quantity", 1),
                1
            )

            price = safe_float(
                row_value(item, "price", 0)
            )

            discount = safe_float(
                row_value(item, "discount", 0)
            )

            final_price = price

            if discount > 0:
                final_price = price - (
                    price * discount / 100
                )

            store_id = row_value(
                item,
                "store_id"
            )

            OrderItem.create(
                order_id=order_id,
                product_id=product_id,
                store_id=store_id,
                quantity=quantity,
                price=final_price
            )

            connection.execute(
                """
                UPDATE products
                SET quantity = MAX(quantity - ?, 0)
                WHERE id = ?
                """,
                (
                    quantity,
                    product_id
                )
            )

        connection.commit()

        Cart.clear(
            user["id"]
        )

        try:
            Notification.create(
                user["id"],
                "تم إنشاء طلبك 🛍️",
                f"تم تسجيل طلبك رقم #{order_id} بنجاح."
            )
        except Exception as notification_error:
            print(
                "NOTIFICATION ERROR:",
                notification_error
            )

        if request.is_json:
            return jsonify({
                "success": True,
                "order_id": order_id,
                "redirect": url_for(
                    "auth.orders"
                )
            })

        flash(
            "تم إنشاء الطلب بنجاح 🎉",
            "success"
        )

        return redirect(
            url_for("auth.orders")
        )

    except Exception as error:

        connection.rollback()

        print(
            "CHECKOUT ERROR:",
            error
        )

        if request.is_json:
            return jsonify({
                "success": False,
                "message": "تعذر إتمام الطلب."
            }), 500

        flash(
            "تعذر إتمام الطلب.",
            "error"
        )

        return redirect(
            url_for("auth.cart")
        )

    finally:
        connection.close()


# =========================================================
# FAVORITES
# =========================================================

@auth.route("/favorites")
def favorites():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    try:
        favorites_list = Favorite.all(
            user["id"]
        )
    except Exception:
        favorites_list = []

    return render_template(
        "favorites.html",
        user=user,
        favorites=favorites_list
    )


@auth.route("/favorites/toggle", methods=["POST"])
def favorites_toggle():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    product_id = safe_int(
        request.form.get("product_id")
    )

    if product_id <= 0:
        return jsonify({
            "success": False,
            "message": "المنتج غير صالح."
        }), 400

    try:

        existing = Favorite.all(
            user["id"]
        )

        already_exists = any(
            row_value(item, "product_id") == product_id
            for item in existing
        )

        if already_exists:

            Favorite.remove(
                user["id"],
                product_id
            )

            return jsonify({
                "success": True,
                "favorite": False
            })

        Favorite.add(
            user["id"],
            product_id
        )

        return jsonify({
            "success": True,
            "favorite": True
        })

    except Exception as error:

        print(
            "FAVORITE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "تعذر تحديث المفضلة."
        }), 500


# =========================================================
# REWARDS
# =========================================================

def check_rewards(user_id):

    try:

        orders = Order.by_user(
            user_id
        )

        delivered = 0

        for order in orders:

            if row_value(
                order,
                "status"
            ) == "delivered":

                delivered += 1

        milestones = [5, 10, 20]

        for milestone in milestones:

            if delivered >= milestone:

                try:

                    achieved = RewardMilestone.has_achieved(
                        user_id,
                        milestone
                    )

                except Exception:
                    achieved = False

                if not achieved:

                    try:

                        RewardMilestone.grant_milestone(
                            user_id,
                            milestone
                        )

                        RewardCard.create(
                            user_id=user_id,
                            title=f"مكافأة {milestone} طلبات",
                            description=(
                                f"أكملت {milestone} طلبات "
                                "في DZ MARKET 🇩🇿"
                            )
                        )

                    except Exception as reward_error:

                        print(
                            "REWARD ERROR:",
                            reward_error
                        )

    except Exception as error:

        print(
            "CHECK REWARDS ERROR:",
            error
        )


@auth.route("/cards")
def cards():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    try:
        check_rewards(
            user["id"]
        )
    except Exception:
        pass

    try:
        cards_list = RewardCard.by_user(
            user["id"]
        )
    except Exception:
        cards_list = []

    return render_template(
        "cards.html",
        user=user,
        cards=cards_list
    )


@auth.route("/cards/use", methods=["POST"])
def use_card():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    card_code = request.form.get(
        "code",
        ""
    ).strip()

    if not card_code:
        return jsonify({
            "success": False,
            "message": "رمز البطاقة مطلوب."
        }), 400

    try:

        card = RewardCard.find_by_code(
            card_code
        )

        if not card:
            return jsonify({
                "success": False,
                "message": "البطاقة غير موجودة."
            }), 404

        if row_value(
            card,
            "user_id"
        ) != user["id"]:

            return jsonify({
                "success": False,
                "message": "هذه البطاقة ليست لك."
            }), 403

        RewardCard.use(
            card_code
        )

        return jsonify({
            "success": True,
            "message": "تم استخدام البطاقة بنجاح 🎁"
        })

    except Exception as error:

        print(
            "CARD ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "تعذر استخدام البطاقة."
        }), 500


# =========================================================
# REFERRAL
# =========================================================

@auth.route("/referral")
def referral():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    try:
        referrals = Referral.by_inviter(
            user["id"]
        )
    except Exception:
        referrals = []

    return render_template(
        "referral.html",
        user=user,
        referrals=referrals
    )


# =========================================================
# CHAT / MESSAGES
# =========================================================

@auth.route("/messages")
def messages():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                m.*,
                u.full_name AS other_name,
                u.avatar AS other_avatar
            FROM messages m
            LEFT JOIN users u
                ON u.id =
                    CASE
                        WHEN m.sender_id = ?
                        THEN m.receiver_id
                        ELSE m.sender_id
                    END
            WHERE
                m.sender_id = ?
                OR m.receiver_id = ?
            ORDER BY m.created_at DESC
            """,
            (
                user["id"],
                user["id"],
                user["id"]
            )
        ).fetchall()

    except Exception as error:

        print(
            "MESSAGES ERROR:",
            error
        )

        rows = []

    finally:
        connection.close()

    return render_template(
        "messages.html",
        user=user,
        messages=rows
    )


@auth.route("/messages/<int:user_id>")
def chat(user_id):

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    if user_id == user["id"]:
        flash(
            "لا يمكنك فتح محادثة مع نفسك.",
            "error"
        )
        return redirect(
            url_for("auth.messages")
        )

    other = User.find_by_id(
        user_id
    )

    if not other:
        flash(
            "المستخدم غير موجود.",
            "error"
        )
        return redirect(
            url_for("auth.messages")
        )

    try:

        messages_list = Message.conversation(
            user["id"],
            user_id
        )

    except Exception:

        messages_list = []

    try:

        Message.mark_as_read(
            user["id"],
            user_id
        )

    except Exception:
        pass

    return render_template(
        "chat.html",
        user=user,
        current_user=user,
        other=other,
        messages=messages_list
    )


@auth.route("/messages/send", methods=["POST"])
def send_message():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    receiver_id = safe_int(
        request.form.get("receiver_id")
    )

    body = request.form.get(
        "body",
        ""
    ).strip()

    if receiver_id <= 0 or not body:
        return jsonify({
            "success": False,
            "message": "الرسالة غير صالحة."
        }), 400

    if receiver_id == user["id"]:
        return jsonify({
            "success": False,
            "message": "لا يمكنك مراسلة نفسك."
        }), 400

    receiver = User.find_by_id(
        receiver_id
    )

    if not receiver:
        return jsonify({
            "success": False,
            "message": "المستخدم غير موجود."
        }), 404

    if len(body) > 3000:
        return jsonify({
            "success": False,
            "message": "الرسالة طويلة جدًا."
        }), 400

    try:

        Message.create(
            sender_id=user["id"],
            receiver_id=receiver_id,
            body=body
        )

        try:
            Notification.create(
                receiver_id,
                "رسالة جديدة 💬",
                f"لديك رسالة جديدة من {user['full_name']}."
            )
        except Exception:
            pass

        return jsonify({
            "success": True,
            "message": "تم إرسال الرسالة."
        })

    except Exception as error:

        print(
            "SEND MESSAGE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "تعذر إرسال الرسالة."
        }), 500


# =========================================================
# CHAT SETTINGS
# =========================================================

@auth.route(
    "/chat-settings",
    methods=["GET", "POST"]
)
def chat_settings():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    if request.method == "POST":

        try:

            ChatSettings.update(
                user["id"],
                **request.form.to_dict()
            )

            flash(
                "تم تحديث إعدادات المحادثة.",
                "success"
            )

        except Exception as error:

            print(
                "CHAT SETTINGS ERROR:",
                error
            )

            flash(
                "تعذر تحديث الإعدادات.",
                "error"
            )

    try:

        settings = ChatSettings.get(
            user["id"]
        )

    except Exception:

        settings = None

    return render_template(
        "chat_settings.html",
        user=user,
        settings=settings
    )


# =========================================================
# COMPLAINTS
# =========================================================

@auth.route(
    "/complaints",
    methods=["GET", "POST"]
)
def complaints():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    if request.method == "POST":

        subject = request.form.get(
            "subject",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()

        order_id = safe_int(
            request.form.get("order_id"),
            0
        )

        if not subject or not message:
            flash(
                "العنوان والرسالة مطلوبان.",
                "error"
            )
            return redirect(
                url_for("auth.complaints")
            )

        try:

            Complaint.create(
                user_id=user["id"],
                subject=subject,
                message=message,
                order_id=order_id if order_id > 0 else None
            )

            flash(
                "تم إرسال الشكوى بنجاح 📢",
                "success"
            )

        except Exception as error:

            print(
                "COMPLAINT ERROR:",
                error
            )

            flash(
                "تعذر إرسال الشكوى.",
                "error"
            )

        return redirect(
            url_for("auth.complaints")
        )

    try:
        complaints_list = Complaint.by_user(
            user["id"]
        )
    except Exception:
        complaints_list = []

    return render_template(
        "complaints.html",
        user=user,
        complaints=complaints_list
    )


# =========================================================
# SELLER SECTION
# =========================================================

@auth.route("/seller")
def seller():

    guard = seller_required()

    if guard:
        return guard

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


@auth.route(
    "/seller/edit",
    methods=["GET", "POST"]
)
def seller_edit():

    guard = seller_required()

    if guard:
        return guard

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

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
                "error"
            )
            return redirect(
                url_for("auth.seller_edit")
            )

        try:

            if store:

                Store.update(
                    store["id"],
                    name=name,
                    description=description,
                    phone=phone,
                    wilaya=wilaya,
                    municipality=municipality
                )

            else:

                Store.create(
                    user_id=user["id"],
                    name=name,
                    description=description,
                    phone=phone,
                    wilaya=wilaya,
                    municipality=municipality
                )

            flash(
                "تم حفظ معلومات المتجر بنجاح 🏪",
                "success"
            )

            return redirect(
                url_for("auth.seller")
            )

        except Exception as error:

            print(
                "SELLER EDIT ERROR:",
                error
            )

            flash(
                "تعذر حفظ معلومات المتجر.",
                "error"
            )

    return render_template(
        "seller_edit.html",
        user=user,
        store=store
    )


# =========================================================
# SELLER PRODUCT CREATE
# =========================================================

@auth.route(
    "/seller/products/new",
    methods=["GET", "POST"]
)
def seller_product_new():

    guard = seller_required()

    if guard:
        return guard

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

    if not store:

        flash(
            "أنشئ متجرك أولًا.",
            "error"
        )

        return redirect(
            url_for("auth.seller_edit")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = safe_float(
            request.form.get("price", 0)
        )

        discount = safe_float(
            request.form.get("discount", 0)
        )

        quantity = safe_int(
            request.form.get("quantity", 0)
        )

        category = request.form.get(
            "category",
            ""
        ).strip()

        brand = request.form.get(
            "brand",
            ""
        ).strip()

        images = request.form.get(
            "images",
            ""
        ).strip()

        video = request.form.get(
            "video",
            ""
        ).strip()

        delivery_wilayas = request.form.get(
            "delivery_wilayas",
            ""
        ).strip()

        if not name:

            flash(
                "اسم المنتج مطلوب.",
                "error"
            )

            return redirect(
                url_for("auth.seller_product_new")
            )

        if price < 0 or discount < 0 or quantity < 0:

            flash(
                "تحقق من السعر والخصم والكمية.",
                "error"
            )

            return redirect(
                url_for("auth.seller_product_new")
            )

        if discount > 100:

            flash(
                "الخصم لا يمكن أن يتجاوز 100%.",
                "error"
            )

            return redirect(
                url_for("auth.seller_product_new")
            )

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
                delivery_wilayas=delivery_wilayas
            )

            flash(
                "تمت إضافة المنتج بنجاح 🎉",
                "success"
            )

            return redirect(
                url_for("auth.seller")
            )

        except Exception as error:

            print(
                "PRODUCT CREATE ERROR:",
                error
            )

            flash(
                "تعذر إضافة المنتج.",
                "error"
            )

    return render_template(
        "seller_product_form.html",
        product=None,
        store=store
    )


# =========================================================
# SELLER PRODUCT EDIT
# =========================================================

@auth.route(
    "/seller/products/<int:product_id>/edit",
    methods=["GET", "POST"]
)
def seller_product_edit(product_id):

    guard = seller_required()

    if guard:
        return guard

    user = current_user()

    store = Store.find_by_user_id(
        user["id"]
    )

    product = Product.find_by_id(
        product_id
    )

    if not store or not product:

        flash(
            "المنتج غير موجود.",
            "error"
        )

        return redirect(
            url_for("auth.seller")
        )

    if product["store_id"] != store["id"]:

        flash(
            "ليس لديك صلاحية تعديل هذا المنتج.",
            "error"
        )

        return redirect(
            url_for("auth.seller")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = safe_float(
            request.form.get("price", 0)
        )

        discount = safe_float(
            request.form.get("discount", 0)
        )

        quantity = safe_int(
            request.form.get("quantity", 0)
        )

        category = request.form.get(
            "category",
            ""
        ).strip()

        brand = request.form.get(
            "brand",
            ""
        ).strip()

        images = request.form.get(
            "images",
            ""
        ).strip()

        video = request.form.get(
            "video",
            ""
        ).strip()

        delivery_wilayas = request.form.get(
            "delivery_wilayas",
            ""
        ).strip()

        if not name:

            flash(
                "اسم المنتج مطلوب.",
                "error"
            )

            return redirect(
                url_for(
                    "auth.seller_product_edit",
                    product_id=product_id
                )
            )

        if price < 0 or discount < 0 or quantity < 0:

            flash(
                "تحقق من السعر والخصم والكمية.",
                "error"
            )

            return redirect(
                url_for(
                    "auth.seller_product_edit",
                    product_id=product_id
                )
            )

        if discount > 100:

            flash(
                "الخصم لا يمكن أن يتجاوز 100%.",
                "error"
            )

            return redirect(
                url_for(
                    "auth.seller_product_edit",
                    product_id=product_id
                )
            )

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
                delivery_wilayas=delivery_wilayas
            )

            flash(
                "تم تحديث المنتج بنجاح ✅",
                "success"
            )

            return redirect(
                url_for("auth.seller")
            )

        except Exception as error:

            print(
                "PRODUCT UPDATE ERROR:",
                error
            )

            flash(
                "تعذر تحديث المنتج.",
                "error"
            )

    return render_template(
        "seller_product_form.html",
        product=product,
        store=store
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@auth.route("/admin")
def admin():

    guard = admin_required()

    if guard:
        return guard

    connection = get_connection()

    try:

        stats = {}

        # ---------------------------------------------
        # BASIC COUNTS
        # ---------------------------------------------

        stats["users"] = count_table(
            connection,
            "users"
        )

        stats["products"] = count_table(
            connection,
            "products"
        )

        stats["orders"] = count_table(
            connection,
            "orders"
        )

        stats["messages"] = count_table(
            connection,
            "messages"
        )

        stats["complaints"] = count_table(
            connection,
            "complaints"
        )

        stats["reports"] = count_table(
            connection,
            "reports"
        )

        # ---------------------------------------------
        # SELLERS
        # ---------------------------------------------

        try:

            result = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM users
                WHERE role = 'seller'
                """
            ).fetchone()

            stats["sellers"] = (
                result["total"]
                if result
                else 0
            )

        except Exception:

            stats["sellers"] = 0

        # ---------------------------------------------
        # PENDING SELLERS
        # ---------------------------------------------

        store_columns = get_table_columns(
            connection,
            "stores"
        )

        pending_sellers = 0

        if "status" in store_columns:

            try:

                result = connection.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM stores
                    WHERE status IN
                    ('pending', 'pending_review')
                    """
                ).fetchone()

                pending_sellers = (
                    result["total"]
                    if result
                    else 0
                )

            except Exception:
                pending_sellers = 0

        elif "is_verified" in store_columns:

            try:

                result = connection.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM stores
                    WHERE is_verified = 0
                    """
                ).fetchone()

                pending_sellers = (
                    result["total"]
                    if result
                    else 0
                )

            except Exception:
                pending_sellers = 0

        stats["pending_sellers"] = pending_sellers

        # ---------------------------------------------
        # EXTRA BUSINESS METRICS
        # ---------------------------------------------

        try:

            result = connection.execute(
                """
                SELECT COALESCE(SUM(total_amount), 0)
                AS total
                FROM orders
                WHERE status != 'cancelled'
                """
            ).fetchone()

            stats["revenue"] = (
                result["total"]
                if result
                else 0
            )

        except Exception:

            stats["revenue"] = 0

        try:

            result = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM orders
                WHERE status = 'delivered'
                """
            ).fetchone()

            stats["delivered_orders"] = (
                result["total"]
                if result
                else 0
            )

        except Exception:

            stats["delivered_orders"] = 0

        try:

            result = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM stores
                """
            ).fetchone()

            stats["stores"] = (
                result["total"]
                if result
                else 0
            )

        except Exception:

            stats["stores"] = 0

    except Exception as error:

        print(
            "ADMIN STATS ERROR:",
            error
        )

        stats = {
            "users": 0,
            "sellers": 0,
            "products": 0,
            "orders": 0,
            "pending_sellers": 0,
            "complaints": 0,
            "reports": 0,
            "messages": 0,
            "revenue": 0,
            "delivered_orders": 0,
            "stores": 0
        }

    finally:

        connection.close()

    return render_template(
        "admin.html",
        stats=stats
    )


# =========================================================
# ADMIN API — LIVE STATISTICS
# =========================================================

@auth.route("/admin/api/stats")
def admin_api_stats():

    guard = admin_required()

    if guard:
        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 403

    connection = get_connection()

    try:

        stats = {
            "users": count_table(
                connection,
                "users"
            ),

            "products": count_table(
                connection,
                "products"
            ),

            "orders": count_table(
                connection,
                "orders"
            ),

            "messages": count_table(
                connection,
                "messages"
            ),

            "complaints": count_table(
                connection,
                "complaints"
            ),

            "reports": count_table(
                connection,
                "reports"
            )
        }

        result = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM users
            WHERE role = 'seller'
            """
        ).fetchone()

        stats["sellers"] = (
            result["total"]
            if result
            else 0
        )

        return jsonify({
            "success": True,
            "stats": stats
        })

    except Exception as error:

        print(
            "ADMIN API ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "تعذر جلب الإحصائيات."
        }), 500

    finally:

        connection.close()


# =========================================================
# API STATUS
# =========================================================

@auth.route("/api/status")
def api_status():

    database_status = "ok"

    connection = None

    try:

        connection = get_connection()

        connection.execute(
            "SELECT 1"
        ).fetchone()

    except Exception as error:

        print(
            "DATABASE STATUS ERROR:",
            error
        )

        database_status = "error"

    finally:

        if connection:
            connection.close()

    return jsonify({
        "success": database_status == "ok",
        "app": "DZ MARKET",
        "version": "1.0.0",
        "status": "online",
        "database": database_status
    })


# =========================================================
# ERROR HANDLING
# =========================================================

@auth.app_errorhandler(404)
def page_not_found(error):

    try:

        return render_template(
            "404.html"
        ), 404

    except Exception:

        return (
            "الصفحة غير موجودة.",
            404
        )


@auth.app_errorhandler(500)
def internal_server_error(error):

    print(
        "INTERNAL SERVER ERROR:",
        error
    )

    try:

        return render_template(
            "500.html"
        ), 500

    except Exception:

        return (
            "حدث خطأ داخلي في الخادم.",
            500
            )
