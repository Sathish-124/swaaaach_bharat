import pymysql
from flask_mail import Mail
from flask import current_app

# Use PyMySQL instead of MySQLdb
pymysql.install_as_MySQLdb()

class MySQLWrapper:
    @property
    def connection(self):
        cfg = current_app.config
        ssl_params = None
        if cfg.get("MYSQL_SSL_CA"):
            ssl_params = {"ca": cfg["MYSQL_SSL_CA"]}
        return pymysql.connect(
            host=cfg["MYSQL_HOST"],
            user=cfg["MYSQL_USER"],
            password=cfg["MYSQL_PASSWORD"],
            database=cfg["MYSQL_DB"],
            port=cfg.get("MYSQL_PORT", 3306),
            cursorclass=pymysql.cursors.DictCursor,
            ssl=ssl_params,
        )

mysql = MySQLWrapper()
mail = Mail()
