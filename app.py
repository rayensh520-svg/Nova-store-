from flask import Flask, render_template
from database import init_database

app = Flask(__name__)

# تهيئة قاعدة البيانات عند تشغيل التطبيق
init_database()


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
