class Config:
    SECRET_KEY = "supersecretkey123"

    # ---- Aiven MySQL (REMOTE DB) ----
    MYSQL_HOST = "mysql-3b535963-cmr-5763.h.aivencloud.com"
    MYSQL_PORT = 13191
    MYSQL_USER = "avnadmin"
    MYSQL_PASSWORD = "AVINS_8k5E0L30VBc6Hd29Nk∅"   # <- put your real Aiven password
    MYSQL_DB = "defaultdb"
    MYSQL_CURSORCLASS = "DictCursor"
    MYSQL_SSL_CA = "ca.pem"   # we already committed this file

    # ---- EMAIL ----
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your_email@gmail.com'
    MAIL_PASSWORD = 'your_app_password_here'
