import os
from flask import Flask
from sched import scheduler
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv('.env')

app = Flask(__name__)

# App Configurations
app.config['MYSQL_DATABASE_HOST'] = os.environ.get('MYSQL_DATABASE_HOST')
app.config['MYSQL_DATABASE_USER'] = os.environ.get('MYSQL_DATABASE_USER')
app.config['MYSQL_DATABASE_PASSWORD'] = os.environ.get('MYSQL_DATABASE_PASSWORD')
app.config['MYSQL_DATABASE_DB'] = os.environ.get('MYSQL_DATABASE_NAME')
app.config['MYSQL_DATABASE_PORT'] = 3306

# sms config
app.config['SMS_API_KEY'] = os.environ.get('SMS_API_KEY')
app.config['SMS_CLIENT_ID'] = os.environ.get('SMS_CLIENT_ID')
app.config['SMS_ACCESS_KEY'] = os.environ.get('SMS_ACCESS_KEY')
app.config['SMS_SENDER_ID'] = os.environ.get('SMS_SENDER_ID')
app.config['SMS_API_URL'] = os.environ.get('SMS_API_URL')

app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

app.config['TELEGRAM_TOKEN'] = os.environ.get('TELEGRAM_TOKEN')

#Mpesa C2B Paybill Config
app.config['MPESA_C2B_PAYBILL_CONSUMER_KEY'] = os.environ.get("MPESA_C2B_PAYBILL_CONSUMER_KEY")
app.config['MPESA_C2B_PAYBILL_CONSUMER_SECRET'] = os.environ.get("MPESA_C2B_PAYBILL_CONSUMER_SECRET")
app.config['MPESA_C2B_PAYBILL_TOKEN_URL'] = os.environ.get("MPESA_C2B_PAYBILL_TOKEN_URL")
app.config['MPESA_C2B_PAYBILL_NUMBER'] = int(os.environ.get("MPESA_C2B_PAYBILL_NUMBER"))
app.config['MPESA_C2B_PAYBILL_PASSKEY'] = os.environ.get("MPESA_C2B_PAYBILL_PASSKEY")
app.config['MPESA_C2B_PAYBILL_STK_URL'] = os.environ.get("MPESA_C2B_PAYBILL_STK_URL")
app.config['MPESA_C2B_PAYBILL_STK_CALLBACK_URL'] = os.environ.get("MPESA_C2B_PAYBILL_STK_CALLBACK_URL")
app.config['MPESA_C2B_PAYBILL_REGISTER_URLS'] = os.environ.get("MPESA_C2B_PAYBILL_REGISTER_URLS") 

#Mpesa C2B Paybill callback url
app.config['MPESA_C2B_PAYBILL_CONFIRMATION_URL'] = os.environ.get('MPESA_C2B_PAYBILL_CONFIRMATION_URL') 
app.config['MPESA_C2B_PAYBILL_VALIDATION_URL'] = os.environ.get('MPESA_C2B_PAYBILL_VALIDATION_URL')

#Mpesa B2C Paybill 
app.config['MPESA_B2C_API_URL'] = os.environ.get('MPESA_B2C_API_URL')
app.config['MPESA_B2C_TIMEOUT_URL'] = os.environ.get('MPESA_B2C_TIMEOUT_URL')
app.config['MPESA_B2C_RESULTS_URL'] = os.environ.get('MPESA_B2C_RESULTS_URL')
app.config['MPESA_B2C_CRON_RESULTS_URL'] = os.environ.get('MPESA_B2C_CRON_RESULTS_URL')
app.config['MPESA_B2C_CALLBACK_URL'] = os.environ.get('MPESA_B2C_CALLBACK_URL')
app.config['MPESA_B2C_SECURITY_CRED'] = os.environ.get('MPESA_B2C_SECURITY_CRED')
app.config['MPESA_B2C_SHORTCODE'] = os.environ.get('MPESA_B2C_SHORTCODE')
app.config['MPESA_B2C_INITIATOR_NAME'] = os.environ.get('MPESA_B2C_INITIATOR_NAME')
app.config['MPESA_B2C_CONSUMER_KEY'] = os.environ.get('MPESA_B2C_CONSUMER_KEY')
app.config['MPESA_B2C_CONSUMER_SECRET'] = os.environ.get('MPESA_B2C_CONSUMER_SECRET')
app.config['MPESA_B2C_TOKEN_URL'] = os.environ.get('MPESA_B2C_TOKEN_URL')

jwt = JWTManager(app)
CORS(app)

mysql = MySQL(cursorclass=DictCursor)
mysql.init_app(app)

# Importing the blueprints
from modules.administrator_authentication.administrator_url import administrator_auth_bp
from modules.ussd_module.ussd_url import ussd_bp
# from modules.telegram_module.telegram_url import tel_bp
from modules.auction_module.auction_url import auction_bp
from modules.payments_module.payments_url import payments_bp
from modules.sms_module.sms_urls import sms_bp

app.register_blueprint(administrator_auth_bp, url_prefix="/app/ver_02/auth")  
app.register_blueprint(ussd_bp, url_prefix="/api/v2/ussd")
# app.register_blueprint(tel_bp, url_prefix="/app/ver_02/tel")
app.register_blueprint(auction_bp, url_prefix="/app/ver_02/engine")
app.register_blueprint(payments_bp, url_prefix="/app/ver_02/cents")
app.register_blueprint(sms_bp, url_prefix="/app/ver_02/sms")

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    user = {"id": identity['_id'], 'user_type': identity['_type']}
    return user

# Upload folder
UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

