from flask import Flask, render_template
from database import init_database
from routes import auth

app = Flask(__name__)

# مفتاح سري للجلسات والرسائل
app.secret_key = "dz-market-secret-key-change-this-later"

# تهيئة قاعدة البيانات
init_database()

# تسجيل مسارات الحسابات
app.register_blueprint(auth)


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
