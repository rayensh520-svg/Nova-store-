from flask import Flask


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "nova-development-secret-key"

    @app.get("/")
    def home():
        return "NOVA STORE — Online"

    @app.get("/health")
    def health():
        return {
            "ok": True,
            "app": "NOVA STORE",
            "status": "online"
        }

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )
