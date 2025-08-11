from flask import Flask 
from backend.core.database import init_db 
from backend.config import Config


def create_app(config_class=Config): 
    app = Flask(__name__) 
    app.config.from_object(config_class) 
