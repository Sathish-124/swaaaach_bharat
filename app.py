from flask import Flask
from config import Config
from extensions import mysql, mail
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # initialize extensions
    mysql.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)

    # register routes
    from routes.user_routes import user_routes
    from routes.admin_routes import admin_routes
    from routes.rider_routes import rider_routes

    app.register_blueprint(user_routes)
    app.register_blueprint(admin_routes)
    app.register_blueprint(rider_routes)

    @app.route("/")
    def home():
        return "Swaaaach Bharat – Flask + MySQL Working Successfully!"

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
