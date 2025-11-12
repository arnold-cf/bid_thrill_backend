import jwt
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from api.payload.payload import Localtime
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity
)
import main


def sign_token(details):
    try:

        access_token_expiration = timedelta(days=1)
        refresh_token_expiration = timedelta(days=24)

        payload = {
            '_id': details['user_id'],
            'email': details['email'],
            'first_name': details['first_name'],
            '_type': details['user_type']
        }

        access_token = create_access_token(
            identity=payload, expires_delta=access_token_expiration)
        refresh_token = create_refresh_token(
            identity=payload, expires_delta=refresh_token_expiration)

        return access_token, refresh_token
    except Exception as e:
        return jsonify(str(e)), 500


def verify_token(token):
    try:
        payload = jwt.decode(token, key=main.app.config["SECRET_KEY"])
        return payload
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


def sign_permissions(token):
    try:
        start_date = Localtime().gettime()
        now = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
        expiry_time = now + timedelta(minutes=1440)

        payload = {
            'iat': now,
            'exp': expiry_time,
            '_id': token
        }

        encoded_token = jwt.encode(
            payload=payload, key=main.app.config["SECRET_KEY"]).decode("utf-8")
        return encoded_token
    except Exception as e:
        return jsonify(str(e)), 500


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')
        if not token:
            return jsonify({
                'message': "No authentication token!"
            }), 402

        try:
            data = jwt.decode(token, main.app.config['SECRET_KEY'])

            cur = main.mysql.get_db().cursor()
            cur.execute(
                """SELECT id, email FROM customers WHERE id = %s""", data['_id'])
            user = cur.fetchone()
            cur.close()

        except:
            return jsonify({
                'message': "Invalid token!"
            }), 402

        return f(user, *args, **kwargs)
    return decorated


def refresh_token():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)

    return access_token
