from flask import Flask

from config import Config

def create_app():
app = Flask(name)
app.config.from_object(Config)

return app
