from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "admin_login"
login_manager.login_message = "Inicia sesión para acceder al panel."
login_manager.login_message_category = "warning"
