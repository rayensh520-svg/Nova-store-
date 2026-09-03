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
from werkzeug.security import generate_password_hash, check_password_hash

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
    RewardCard,
    Referral,
    RewardMilestone,
    ChatSettings
)

auth = Blueprint("auth", __name__)


# =========================================================
# HELPERS
# =========================================================

def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return User.find_by_id(user_id)


def login_required():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    return None


def row_value(row, key, default=None):
    if row is None:
        return default

    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def calculate_cart_total(items):
    total = 0

    for item in items:
        price = float(row_value(item, "price", 0) or 0)
        discount = float(row_value(item, "discount", 0) or 0)
        quantity = int(row_value(item, "quantity", 1) or 1)

        final_price = price

        if discount > 0:
            final_price = price - (price * discount / 100)

        total += final_price * quantity

    return round(total, 2)


def check_rewards(user_id):
    try:
        completed = RewardMilestone.completed_orders(user_id)

        for milestone in [5, 10, 20]:
            if completed >= milestone and not RewardMilestone.has_achieved(
                user_id,
                milestone
            ):
                card = RewardCard.create(
                    user_id=user_id,
                    title=f"مكافأة {milestone} طلبات 🎁",
                    description=f"مبروك! أكملت {milestone} طلبات.",
                    discount_percent=10,
                    reward_type="discount",
                    source="milestone"
                )

                RewardMilestone.grant_milestone(
                    user_id,
                    milestone,
                    card
                )

    except Exception:
        pass


# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    role = request.form.get("role", "buyer")

    if not full_name or not email or not password:
        flash("يرجى ملء جميع المعلومات المطلوبة.", "error")
        return redirect(url_for("auth.register"))

    if password != confirm_password:
        flash("كلمتا المرور غير متطابقتين.", "error")
        return redirect(url_for("auth.register"))

    if len(password) < 8:
        flash("كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل.", "error")
        return redirect(url_for("auth.register"))

    if role not in ["buyer", "seller"]:
        role = "buyer"

    if User.find_by_email(email):
        flash("هذا البريد الإلكتروني مستعمل من قبل.", "error")
        return redirect(url_for("auth.login"))

    hashed_password = generate_password_hash(password)

    referral_code = request.form.get("referral_code", "").strip() or None

    user_id = User.create(
        full_name=full_name,
        email=email,
        phone=phone,
        password=hashed_password,
        role=role,
        referral_code=referral_code
    )

    # معالجة الإحالة إن وجدت
    if referral_code:
        try:
            inviter = User.find_by_referral_code(referral_code)

            if inviter and inviter["id"] != user_id:
                Referral.create(
                    inviter_id=inviter["id"],
                    invited_user_id=user_id,
                    referral_code=referral_code
                )
        except Exception:
            pass

    # إنشاء متجر للبائع
    if role == "seller":
        try:
            store_name = request.form.get("store_name", "").strip()

            if store_name:
                Store.create(
                    user_id=user_id,
                    name=store_name,
                    description="",
                    phone=phone,
                    wilaya=request.form.get("wilaya", ""),
                    municipality=request.form.get("municipality", "")
                )
        except Exception:
            pass

    flash("تم إنشاء حسابك بنجاح 🎉", "success")
    return redirect(url_for("auth.login"))


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.find_by_email(email)

    if not user or not check_password_hash(user["password"], password):
        flash("البريد الإلكتروني أو كلمة المرور غير صحيحة.", "error")
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]

    flash("تم تسجيل الدخول بنجاح 👋", "success")

    return redirect(url_for("home"))


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
def logout():

    session.clear()

    flash("تم تسجيل الخروج.", "success")

    return redirect(url_for("auth.login"))


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

    orders_list = Order.by_user(user["id"])

    return render_template(
        "orders.html",
        orders=orders_list
    )


@auth.route("/orders/<int:order_id>")
def order_details(order_id):

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    order = Order.find_by_id(order_id)

    if not order:
        flash("الطلب غير موجود.", "error")
        return redirect(url_for("auth.orders"))

    if order["user_id"] != user["id"] and user["role"] != "admin":
        flash("ليس لديك صلاحية للوصول لهذا الطلب.", "error")
        return redirect(url_for("auth.orders"))

    items = OrderItem.by_order(order_id)

    return render_template(
        "orders.html",
        orders=[order],
        order_items=items
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

    items = Cart.get_items(user["id"])
    total = calculate_cart_total(items)

    return render_template(
        "cart.html",
        items=items,
        total=total
    )


@auth.route("/cart/add", methods=["POST"])
def cart_add():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id") or request.form.get("product_id")
    quantity = data.get("quantity") or request.form.get("quantity") or 1

    if not product_id:
        return jsonify({
            "success": False,
            "message": "المنتج غير محدد."
        }), 400

    try:
        product_id = int(product_id)
        quantity = max(1, int(quantity))

        product = Product.find_by_id(product_id)

        if not product:
            return jsonify({
                "success": False,
                "message": "المنتج غير موجود."
            }), 404

        Cart.add(
            user["id"],
            product_id,
            quantity
        )

        return jsonify({
            "success": True,
            "message": "تمت إضافة المنتج للسلة 🛒"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "تعذر إضافة المنتج."
        }), 400


@auth.route("/cart/update", methods=["POST"])
def cart_update():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id") or request.form.get("product_id")
    quantity = data.get("quantity") or request.form.get("quantity")

    if not product_id or quantity is None:
        return jsonify({
            "success": False,
            "message": "بيانات غير مكتملة."
        }), 400

    try:
        Cart.update_quantity(
            user["id"],
            int(product_id),
            max(1, int(quantity))
        )

        return jsonify({
            "success": True
        })

    except Exception:

        return jsonify({
            "success": False,
            "message": "تعذر تحديث الكمية."
        }), 400


@auth.route("/cart/remove", methods=["POST"])
def cart_remove():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id") or request.form.get("product_id")

    if not product_id:
        return jsonify({
            "success": False
        }), 400

    try:
        Cart.remove(
            user["id"],
            int(product_id)
        )

        return jsonify({
            "success": True
        })

    except Exception:

        return jsonify({
            "success": False
        }), 400


@auth.route("/cart/clear", methods=["POST"])
def cart_clear():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    Cart.clear(user["id"])

    return jsonify({
        "success": True
    })


# =========================================================
# CHECKOUT
# =========================================================

@auth.route("/checkout", methods=["POST"])
def checkout():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    items = Cart.get_items(user["id"])

    if not items:
        return jsonify({
            "success": False,
            "message": "السلة فارغة."
        }), 400

    total = calculate_cart_total(items)

    try:

        wilaya = row_value(user, "wilaya")
        municipality = row_value(user, "municipality")

        order_id = Order.create(
            user_id=user["id"],
            total_amount=total,
            delivery_wilaya=wilaya,
            delivery_municipality=municipality
        )

        for item in items:

            OrderItem.create(
                order_id=order_id,
                product_id=item["product_id"],
                store_id=row_value(item, "store_id"),
                quantity=item["quantity"],
                price=item["price"]
            )

        Cart.clear(user["id"])

        Notification.create(
            user["id"],
            "تم إنشاء طلبك بنجاح 🎉",
            f"تم تسجيل الطلب رقم #{order_id}."
        )

        check_rewards(user["id"])

        return jsonify({
            "success": True,
            "order_id": order_id,
            "message": "تم تأكيد الطلب بنجاح 🎉"
        })

    except Exception:

        return jsonify({
            "success": False,
            "message": "حدث خطأ أثناء تأكيد الطلب."
        }), 500


# =========================================================
# CARDS / REWARDS
# =========================================================

@auth.route("/cards")
def cards():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    cards_list = RewardCard.by_user(user["id"])

    return render_template(
        "cards.html",
        cards=cards_list
    )


@auth.route("/cards/use", methods=["POST"])
def use_card():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    data = request.get_json(silent=True) or {}

    code = data.get("code") or request.form.get("code")

    if not code:
        return jsonify({
            "success": False,
            "message": "رمز البطاقة غير موجود."
        }), 400

    card = RewardCard.find_by_code(
        user["id"],
        code
    )

    if not card:
        return jsonify({
            "success": False,
            "message": "البطاقة غير موجودة."
        }), 404

    try:
        RewardCard.use(card["id"])

        return jsonify({
            "success": True,
            "message": "تم استعمال البطاقة بنجاح 🎁"
        })

    except Exception:

        return jsonify({
            "success": False,
            "message": "تعذر استعمال البطاقة."
        }), 400


# =========================================================
# REFERRAL
# =========================================================

@auth.route("/referral")
def referral():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    referrals = Referral.by_inviter(user["id"])

    return jsonify({
        "success": True,
        "referral_code": row_value(user, "referral_code"),
        "referrals": [
            dict(referral)
            for referral in referrals
        ]
    })


# =========================================================
# FAVORITES
# =========================================================

@auth.route("/favorites")
def favorites():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    favorites_list = Favorite.all(user["id"])

    return jsonify({
        "success": True,
        "favorites": [
            dict(item)
            for item in favorites_list
        ]
    })


# =========================================================
# MESSAGES
# =========================================================

@auth.route("/messages")
def messages():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    conversations = Message.conversation(user["id"])

    return render_template(
        "messages.html",
        conversations=conversations
    )


@auth.route("/messages/<int:user_id>")
def conversation(user_id):

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    if user_id == user["id"]:
        return redirect(url_for("auth.messages"))

    other = User.find_by_id(user_id)

    if not other:
        flash("المستخدم غير موجود.", "error")
        return redirect(url_for("auth.messages"))

    # جلب رسائل المحادثة بين المستخدمين
    try:
        messages_list = Message.between(
            user["id"],
            user_id
        )
    except AttributeError:
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

    data = request.get_json(silent=True) or {}

    receiver_id = (
        data.get("receiver_id")
        or request.form.get("receiver_id")
    )

    body = (
        data.get("body")
        or request.form.get("body")
        or ""
    ).strip()

    if not receiver_id or not body:
        flash("الرسالة فارغة.", "error")

        if receiver_id:
            return redirect(
                url_for(
                    "auth.conversation",
                    user_id=int(receiver_id)
                )
            )

        return redirect(url_for("auth.messages"))

    try:
        receiver_id = int(receiver_id)
    except ValueError:
        return redirect(url_for("auth.messages"))

    receiver = User.find_by_id(receiver_id)

    if not receiver:
        flash("المستخدم غير موجود.", "error")
        return redirect(url_for("auth.messages"))

    if receiver_id == user["id"]:
        flash("لا يمكنك إرسال رسالة لنفسك.", "error")
        return redirect(url_for("auth.messages"))

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

    # إذا كان الطلب AJAX
    if request.is_json:
        return jsonify({
            "success": True,
            "message": "تم إرسال الرسالة."
        })

    return redirect(
        url_for(
            "auth.conversation",
            user_id=receiver_id
        )
    )


# =========================================================
# CHAT SETTINGS
# =========================================================

@auth.route("/chat/settings", methods=["GET", "POST"])
def chat_settings():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    if request.method == "POST":

        voice_type = request.form.get(
            "voice_type",
            "female"
        )

        voice_enabled = 1 if request.form.get(
            "voice_enabled"
        ) else 0

        language = request.form.get(
            "language",
            "ar"
        )

        style = request.form.get(
            "style",
            "friendly"
        )

        ChatSettings.update(
            user["id"],
            voice_type=voice_type,
            voice_enabled=voice_enabled,
            language=language,
            style=style
        )

        flash("تم حفظ إعدادات المحادثة.", "success")

        return redirect(
            url_for("auth.chat_settings")
        )

    settings = ChatSettings.get(user["id"])

    return render_template(
        "chat_settings.html",
        settings=settings
    )


# =========================================================
# COMPLAINTS
# =========================================================

@auth.route("/complaints", methods=["POST"])
def complaints():

    guard = login_required()

    if guard:
        return guard

    user = current_user()

    data = request.get_json(silent=True) or {}

    subject = (
        data.get("subject")
        or request.form.get("subject")
        or "شكوى"
    )

    body = (
        data.get("body")
        or request.form.get("body")
        or ""
    ).strip()

    if not body:
        return jsonify({
            "success": False,
            "message": "اكتب تفاصيل الشكوى."
        }), 400

    Complaint.create(
        user_id=user["id"],
        subject=subject,
        body=body
    )

    return jsonify({
        "success": True,
        "message": "تم إرسال الشكوى بنجاح."
    })


# =========================================================
# API STATUS
# =========================================================

@auth.route("/api/status")
def api_status():

    return jsonify({
        "status": "ok",
        "app": "DZ MARKET",
        "version": "1.0",
        "message": "DZ MARKET is running 🇩🇿"
    })
