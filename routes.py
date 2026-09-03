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


# =========================================================
# BLUEPRINT
# =========================================================

auth = Blueprint(
    "auth",
    __name__
)


# =========================================================
# HELPERS
# =========================================================

def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return User.find_by_id(user_id)


def login_required():

    return "user_id" in session


def calculate_cart_total(items):

    total = 0

    for item in items:

        price = float(
            item["price"] or 0
        )

        discount = float(
            item["discount"] or 0
        )

        quantity = int(
            item["quantity"] or 1
        )

        final_price = price

        if discount > 0:

            final_price = (
                price
                -
                (price * discount / 100)
            )

        total += (
            final_price
            * quantity
        )

    return round(total, 2)


def check_rewards(user_id):

    completed_orders = (
        RewardMilestone.completed_orders(
            user_id
        )
    )

    rewards = {
        5: (
            "مبروك! وصلتِ إلى 5 طلبات 🎉",
            "بطاقة خصم 10%",
            10
        ),

        10: (
            "رائع! وصلتِ إلى 10 طلبات 🏆",
            "بطاقة خصم 15%",
            15
        ),

        20: (
            "إنجاز كبير! 20 طلب مكتمل 👑",
            "بطاقة خصم 20%",
            20
        )
    }


    for milestone, data in rewards.items():

        if completed_orders >= milestone:

            if not RewardMilestone.has_achieved(
                user_id,
                milestone
            ):

                title = data[1]
                discount = data[2]

                card_id = RewardCard.create(
                    user_id=user_id,
                    title=title,
                    description=(
                        f"مكافأة إتمام "
                        f"{milestone} طلبات"
                    ),
                    discount_percent=discount,
                    reward_type="discount",
                    source=f"milestone_{milestone}"
                )

                RewardMilestone.grant_milestone(
                    user_id,
                    milestone,
                    card_id
                )

                Notification.create(
                    user_id,
                    "مكافأة جديدة 🎁",
                    data[0]
                )


# =========================================================
# REGISTER
# =========================================================

@auth.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

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
        )

        referral_code = request.form.get(
            "referral_code",
            ""
        ).strip().upper()


        if not full_name or not email:

            flash(
                "يرجى ملء المعلومات المطلوبة.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        if password != confirm_password:

            flash(
                "كلمتا المرور غير متطابقتين.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        if len(password) < 6:

            flash(
                "كلمة المرور يجب أن تحتوي على 6 أحرف على الأقل.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        if role not in {
            "buyer",
            "seller"
        }:

            role = "buyer"


        existing = User.find_by_email(
            email
        )

        if existing:

            flash(
                "هذا البريد الإلكتروني مسجل مسبقًا.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        hashed_password = (
            generate_password_hash(
                password
            )
        )


        user_id = User.create(
            full_name=full_name,
            email=email,
            password=hashed_password,
            role=role,
            phone=phone
        )


        if not user_id:

            flash(
                "تعذر إنشاء الحساب.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # ---------------------------------------------
        # SELLER STORE
        # ---------------------------------------------

        if role == "seller":

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


            User.update_profile(
                user_id,
                wilaya=wilaya,
                municipality=municipality
            )


            connection_store = Store.create(
                user_id=user_id,
                name=store_name or full_name,
                description=activity_type,
                phone=phone,
                wilaya=wilaya,
                municipality=municipality
            )


        # ---------------------------------------------
        # REFERRAL
        # ---------------------------------------------

        if referral_code:

            inviter = User.find_by_referral_code(
                referral_code
            )

            if inviter:

                Referral.create(
                    inviter_id=inviter["id"],
                    invited_user_id=user_id,
                    referral_code=referral_code
                )


        # ---------------------------------------------
        # LOGIN
        # ---------------------------------------------

        session["user_id"] = user_id

        session["role"] = role

        flash(
            "تم إنشاء حسابك بنجاح 🇩🇿",
            "success"
        )

        return redirect(
            url_for("home")
        )


    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@auth.route(
    "/login",
    methods=["GET", "POST"]
)
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


        user = User.find_by_email(
            email
        )


        if not user:

            flash(
                "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )


        if not check_password_hash(
            user["password"],
            password
        ):

            flash(
                "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )


        session["user_id"] = user["id"]

        session["role"] = user["role"]


        Notification.create(
            user["id"],
            "تم تسجيل الدخول",
            f"تم تسجيل الدخول إلى حسابك باستخدام {email}."
        )


        check_rewards(
            user["id"]
        )


        return redirect(
            url_for("home")
        )


    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# ACCOUNT
# =========================================================

@auth.route("/account")
def account():

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    check_rewards(
        user["id"]
    )


    return render_template(
        "account.html",
        user=user
    )


# =========================================================
# ORDERS
# =========================================================

@auth.route("/orders")
def orders():

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    check_rewards(
        user["id"]
    )


    user_orders = Order.by_user(
        user["id"]
    )


    return render_template(
        "orders.html",
        orders=user_orders
    )


# =========================================================
# ORDER DETAILS
# =========================================================

@auth.route(
    "/orders/<int:order_id>"
)
def order_details(order_id):

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    order = Order.find_by_id(
        order_id
    )


    if not order:

        return redirect(
            url_for("auth.orders")
        )


    if order["user_id"] != user["id"]:

        return redirect(
            url_for("auth.orders")
        )


    items = OrderItem.by_order(
        order_id
    )


    return render_template(
        "orders.html",
        orders=[order],
        order_items=items
    )


# =========================================================
# CART
# =========================================================

@auth.route(
    "/cart",
    methods=["GET"]
)
def cart():

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    items = Cart.get_items(
        user["id"]
    )


    total = calculate_cart_total(
        items
    )


    return render_template(
        "cart.html",
        items=items,
        total=total
    )


# =========================================================
# CART ADD
# =========================================================

@auth.route(
    "/cart/add",
    methods=["POST"]
)
def cart_add():

    user = current_user()

    if not user:

        return jsonify({
            "success": False,
            "message": "يجب تسجيل الدخول."
        }), 401


    product_id = request.form.get(
        "product_id",
        type=int
    )

    quantity = request.form.get(
        "quantity",
        1,
        type=int
    )


    if not product_id:

        return jsonify({
            "success": False,
            "message": "المنتج غير صالح."
        }), 400


    product = Product.find_by_id(
        product_id
    )


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
        "message": "تمت إضافة المنتج إلى السلة 🛒"
    })


# =========================================================
# CART UPDATE
# =========================================================

@auth.route(
    "/cart/update",
    methods=["POST"]
)
def cart_update():

    user = current_user()

    if not user:

        return jsonify({
            "success": False
        }), 401


    product_id = request.form.get(
        "product_id",
        type=int
    )

    quantity = request.form.get(
        "quantity",
        type=int
    )


    if not product_id or quantity is None:

        return jsonify({
            "success": False,
            "message": "بيانات غير صالحة."
        }), 400


    Cart.update_quantity(
        user["id"],
        product_id,
        quantity
    )


    return redirect(
        url_for("auth.cart")
    )


# =========================================================
# CART REMOVE
# =========================================================

@auth.route(
    "/cart/remove",
    methods=["POST"]
)
def cart_remove():

    user = current_user()

    if not user:

        return jsonify({
            "success": False
        }), 401


    product_id = request.form.get(
        "product_id",
        type=int
    )


    if product_id:

        Cart.remove(
            user["id"],
            product_id
        )


    return redirect(
        url_for("auth.cart")
    )


# =========================================================
# CART CLEAR
# =========================================================

@auth.route(
    "/cart/clear",
    methods=["POST"]
)
def cart_clear():

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    Cart.clear(
        user["id"]
    )


    return redirect(
        url_for("auth.cart")
    )


# =========================================================
# CARDS
# =========================================================

@auth.route("/cards")
def cards():

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    check_rewards(
        user["id"]
    )


    user_cards = RewardCard.by_user(
        user["id"]
    )


    return render_template(
        "cards.html",
        cards=user_cards
    )


# =========================================================
# USE CARD
# =========================================================

@auth.route(
    "/cards/use",
    methods=["POST"]
)
def use_card():

    user = current_user()

    if not user:

        return jsonify({
            "success": False
        }), 401


    code = request.form.get(
        "code",
        ""
    ).strip().upper()


    if not code:

        return jsonify({
            "success": False,
            "message": "رمز البطاقة مفقود."
        }), 400


    card = RewardCard.find_by_code(
        user["id"],
        code
    )


    if not card:

        return jsonify({
            "success": False,
            "message": "البطاقة غير صالحة أو مستعملة."
        }), 400


    RewardCard.use(
        user["id"],
        code
    )


    return jsonify({
        "success": True,
        "message": "تم استخدام البطاقة بنجاح 🎉"
    })


# =========================================================
# REFERRAL
# =========================================================

@auth.route("/referral")
def referral():

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    referrals = Referral.by_inviter(
        user["id"]
    )


    return jsonify({

        "referral_code":
            user["referral_code"],

        "referrals": [
            {
                "name":
                    item["full_name"],

                "email":
                    item["email"],

                "status":
                    item["status"]
            }

            for item in referrals
        ]
    })


# =========================================================
# FAVORITES
# =========================================================

@auth.route("/favorites")
def favorites():

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    products = Favorite.all(
        user["id"]
    )


    return jsonify({
        "products": [
            {
                "id": p["id"],
                "name": p["name"],
                "price": p["price"]
            }
            for p in products
        ]
    })


# =========================================================
# MESSAGES
# =========================================================

@auth.route("/messages")
def messages():

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    conversations = Message.conversation(
        user["id"]
    )


    return render_template(
        "messages.html",
        conversations=conversations
    )


# =========================================================
# SEND MESSAGE
# =========================================================

@auth.route(
    "/messages/send",
    methods=["POST"]
)
def send_message():

    user = current_user()

    if not user:

        return jsonify({
            "success": False
        }), 401


    receiver_id = request.form.get(
        "receiver_id",
        type=int
    )

    body = request.form.get(
        "body",
        ""
    ).strip()


    if not receiver_id or not body:

        return jsonify({
            "success": False,
            "message": "الرسالة غير صالحة."
        }), 400


    receiver = User.find_by_id(
        receiver_id
    )


    if not receiver:

        return jsonify({
            "success": False,
            "message": "المستخدم غير موجود."
        }), 404


    message_id = Message.create(
        user["id"],
        receiver_id,
        body
    )


    Notification.create(
        receiver_id,
        "رسالة جديدة 💬",
        f"لديك رسالة جديدة من {user['full_name']}."
    )


    return jsonify({
        "success": True,
        "message_id": message_id
    })


# =========================================================
# CHAT SETTINGS
# =========================================================

@auth.route(
    "/chat-settings",
    methods=["GET", "POST"]
)
def chat_settings():

    user = current_user()

    if not user:

        return redirect(
            url_for("auth.login")
        )


    if request.method == "POST":

        voice_type = request.form.get(
            "voice_type",
            "female"
        )

        voice_enabled = (
            request.form.get(
                "voice_enabled"
            )
            == "on"
        )

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
            voice_type,
            voice_enabled,
            language,
            style
        )


        flash(
            "تم حفظ إعدادات المساعد بنجاح.",
            "success"
        )


        return redirect(
            url_for("auth.chat_settings")
        )


    settings = ChatSettings.get(
        user["id"]
    )


    return render_template(
        "chat_settings.html",
        settings=settings
    )


# =========================================================
# COMPLAINT
# =========================================================

@auth.route(
    "/complaints",
    methods=["POST"]
)
def create_complaint():

    user = current_user()

    if not user:

        return jsonify({
            "success": False
        }), 401


    subject = request.form.get(
        "subject",
        ""
    ).strip()

    message = request.form.get(
        "message",
        ""
    ).strip()

    order_id = request.form.get(
        "order_id",
        type=int
    )


    if not message:

        return jsonify({
            "success": False,
            "message": "اكتب تفاصيل الشكوى."
        }), 400


    complaint_id = Complaint.create(
        user_id=user["id"],
        message=message,
        order_id=order_id,
        subject=subject
    )


    Notification.create(
        user["id"],
        "تم إرسال الشكوى",
        "تم استلام شكواك وسيتم التعامل معها."
    )


    return jsonify({
        "success": True,
        "complaint_id": complaint_id
    })


# =========================================================
# HEALTH
# =========================================================

@auth.route("/api/status")
def api_status():

    return jsonify({
        "status": "ok",
        "app": "DZ MARKET",
        "version": "1.0"
    })
