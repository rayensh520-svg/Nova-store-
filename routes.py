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

from models import (
    User,
    Store,
    Message,
    ChatSettings
)

auth = Blueprint("auth", __name__)


# ============================================================
# HELPERS
# ============================================================

def validate_password(password):
    if len(password) < 8:
        return False

    has_letter = any(char.isalpha() for char in password)
    has_number = any(char.isdigit() for char in password)

    return has_letter and has_number


def login_user(user, remember=False):
    session.clear()

    session["user_id"] = user["id"]
    session["role"] = user["role"]

    session.permanent = bool(remember)


# ============================================================
# REGISTER
# ============================================================

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

        confirm_password = request.form.get(
            "confirm_password", ""
        )

        role = request.form.get(
            "role", "buyer"
        ).strip().lower()

        accepted_terms = request.form.get(
            "accept_terms"
        )

        store_name = request.form.get(
            "store_name", ""
        ).strip()

        activity_type = request.form.get(
            "activity_type", ""
        ).strip()

        wilaya = request.form.get(
            "wilaya", ""
        ).strip()

        municipality = request.form.get(
            "municipality", ""
        ).strip()

        verification_note = request.form.get(
            "verification_note", ""
        ).strip()


        if role not in ("buyer", "seller"):
            role = "buyer"


        # -------------------------
        # BASIC VALIDATION
        # -------------------------

        if not full_name:
            flash(
                "يرجى إدخال الاسم الكامل.",
                "error"
            )
            return redirect(
                url_for("auth.register")
            )

        if not email:
            flash(
                "يرجى إدخال البريد الإلكتروني.",
                "error"
            )
            return redirect(
                url_for("auth.register")
            )

        if not phone:
            flash(
                "يرجى إدخال رقم الهاتف.",
                "error"
            )
            return redirect(
                url_for("auth.register")
            )

        if not password:
            flash(
                "يرجى إدخال كلمة المرور.",
                "error"
            )
            return redirect(
                url_for("auth.register")
            )

        if not confirm_password:
            flash(
                "يرجى تأكيد كلمة المرور.",
                "error"
            )
            return redirect(
                url_for("auth.register")
            )

        if not accepted_terms:
            flash(
                "يجب الموافقة على شروط الاستخدام.",
                "error"
            )
            return redirect(
                url_for("auth.register")
            )


        # -------------------------
        # PASSWORD
        # -------------------------

        if not validate_password(password):

            flash(
                "كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل، وحرف واحد ورقم واحد.",
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


        # -------------------------
        # EMAIL CHECK
        # -------------------------

        existing_user = User.find_by_email(
            email
        )

        if existing_user:

            flash(
                "هذا البريد الإلكتروني مسجل من قبل.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # -------------------------
        # SELLER VALIDATION
        # -------------------------

        if role == "seller":

            if not store_name:

                flash(
                    "يرجى إدخال اسم المتجر.",
                    "error"
                )

                return redirect(
                    url_for("auth.register")
                )

            if not activity_type:

                flash(
                    "يرجى تحديد نوع النشاط.",
                    "error"
                )

                return redirect(
                    url_for("auth.register")
                )

            if not wilaya:

                flash(
                    "يرجى تحديد الولاية.",
                    "error"
                )

                return redirect(
                    url_for("auth.register")
                )


        # -------------------------
        # CREATE USER
        # -------------------------

        password_hash = generate_password_hash(
            password
        )

        user_id = User.create(
            full_name=full_name,
            email=email,
            password=password_hash,
            role=role,
            phone=phone
        )


        if user_id is None:

            flash(
                "تعذر إنشاء الحساب. ربما البريد الإلكتروني مستخدم.",
                "error"
            )

            return redirect(
                url_for("auth.register")
            )


        # -------------------------
        # CREATE SELLER STORE
        # -------------------------

        if role == "seller":

            Store.create(
                user_id=user_id,
                name=store_name,
                description="",
                phone=phone,
                wilaya=wilaya,
                municipality=municipality
            )

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


        # -------------------------
        # LOGIN AFTER REGISTER
        # -------------------------

        user = User.find_by_id(
            user_id
        )

        if user:
            login_user(
                user,
                remember=True
            )


        flash(
            "تم إنشاء حسابك بنجاح 🎉",
            "success"
        )

        return redirect(
            url_for("home")
        )


    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        remember = (
            request.form.get("remember")
            == "on"
        )


        if not email or not password:

            flash(
                "يرجى إدخال البريد الإلكتروني وكلمة المرور.",
                "error"
            )

            return redirect(
                url_for("auth.login")
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


        stored_password = user["password"]


        try:

            password_correct = check_password_hash(
                stored_password,
                password
            )

        except (
            ValueError,
            TypeError
        ):

            password_correct = False


        if not password_correct:

            flash(
                "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
                "error"
            )

            return redirect(
                url_for("auth.login")
            )


        login_user(
            user,
            remember=remember
        )


        flash(
            "مرحبًا بك من جديد 👋",
            "success"
        )

        return redirect(
            url_for("home")
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
        "تم تسجيل الخروج بنجاح.",
        "success"
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# MESSAGES
# ============================================================

@auth.route("/messages")
def messages():

    user_id = session.get(
        "user_id"
    )


    if not user_id:

        flash(
            "سجّل الدخول أولًا للوصول إلى الرسائل.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    conversations = Message.conversation(
        user_id
    )


    return render_template(
        "messages.html",
        conversations=conversations
    )


# ============================================================
# SEND MESSAGE
# ============================================================

@auth.route(
    "/messages/send",
    methods=["POST"]
)
def send_message():

    user_id = session.get(
        "user_id"
    )


    if not user_id:

        flash(
            "يجب تسجيل الدخول أولًا.",
            "error"
        )

        return redirect(
            url_for("auth.login")
        )


    receiver_id = request.form.get(
        "receiver_id",
        type=int
    )

    text = request.form.get(
        "message",
        ""
    ).strip()


    if not receiver_id or not text:

        flash(
            "الرسالة غير مكتملة.",
            "error"
        )

        return redirect(
            url_for("auth.messages")
        )


    if receiver_id == user_id:

        flash(
            "لا يمكنك إرسال رسالة لنفسك.",
            "error"
        )

        return redirect(
            url_for("auth.messages")
        )


    receiver = User.find_by_id(
        receiver_id
    )


    if not receiver:

        flash(
            "المستخدم غير موجود.",
            "error"
        )

        return redirect(
            url_for("auth.messages")
        )


    Message.create(
        sender_id=user_id,
        receiver_id=receiver_id,
        body=text
    )


    return redirect(
        url_for("auth.messages")
    )


# ============================================================
# CHAT SETTINGS
# ============================================================

@auth.route(
    "/chat-settings",
    methods=["GET", "POST"]
)
def chat_settings():

    user_id = session.get(
        "user_id"
    )


    if not user_id:

        flash(
            "سجّل الدخول أولًا.",
            "error"
        )

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
            ) == "1"
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
            user_id=user_id,
            voice_type=voice_type,
            voice_enabled=voice_enabled,
            language=language,
            style=style
        )


        flash(
            "تم حفظ إعدادات الدردشة بنجاح 🎙️✨",
            "success"
        )

        return redirect(
            url_for("auth.chat_settings")
        )


    settings = ChatSettings.get(
        user_id
    )


    return render_template(
        "chat_settings.html",
        settings=settings
            )
