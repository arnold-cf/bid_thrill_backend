from flask import request, jsonify, json
from api.password.crypt_password import hash_password, unhash_password
from api.payload.payload import Localtime
from main import mysql, app
from api.logs.logger import ErrorLogger
from api.middleware.tokens.jwt import sign_token, refresh_token


class Administrator:

    def login(self):
        data = request.get_json()

        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'status': 402,
                'description': 'Request data is missing some details!'
            }), 402

        email = data['email']
        password = data['password']
        
        try:
            cur = mysql.get_db().cursor()
        except Exception:
            return jsonify({
                'status': 500,
                'description': "Couldn't connect to the Database!"
            }), 500

        try:
            cur.execute("SELECT * FROM administrators WHERE email = %s", [email])
            admin = cur.fetchone()

            if not admin:
                return jsonify({
                    'status': 404,
                    'description': 'Record not found!'
                }), 404

            admin_password = admin['password'].encode()
            if not unhash_password(password.encode(), admin_password):
                return jsonify({
                    'status': 401,
                    'description': 'Invalid password!'
                }), 401

            access_token, refresh_token = sign_token({
                'email': admin['email'],
                'user_id': admin['id'],
                'user_type': admin['admin_type'],
                'first_name': admin['first_name']
            })

            data = {
                'id': admin['id'],
                'first_name': admin['first_name'],
                'last_name': admin['last_name'],
                'admin_type': admin['admin_type'],
                'access_token': access_token,
                'refresh_token': refresh_token,
                'is_first_time_login': bool(admin['first_time_login']),
                'theme': admin['theme']
            }

            return jsonify({
                'data': data,
                'status': 200,
                'description': 'Login successful'
            }), 200

        except Exception as error:
            return jsonify({
                'status': 500,
                'description': f'Error during login process: {str(error)}'
            }), 500

        finally:
            cur.close()

    def update_initial_password(self, user):
        data = request.get_json()

        if not data:
            message = {
                'status': 402,
                'description': 'Request data is missing some details!'
            }
            return jsonify(message), 402

        new_password = data["new_password"]

        try:  # Test DB connection
            cur = mysql.get_db().cursor()
        except:
            message = {
                'status': 500,
                'description': "Couldn't connect to the Database!"
            }
            return jsonify(message)

        user_id = user['id']

        try:
            cur.execute(
                """SELECT * FROM administrators WHERE admin_id = %s""", (user_id))
            admin = cur.fetchone()

        except Exception as error:
            message = {
                'status': 501,
                'description': 'Failed to update password. Error: ' + str(error)
            }
            ErrorLogger().logError(message)
            return jsonify(message), 501

        if not admin:
            message = {
                'status': 404,
                'description': 'User not found!'
            }
            return jsonify(message), 404

        new_password = hash_password(new_password.encode())

        try:
            is_first_time_login = False
            cur.execute(
                """UPDATE administrators SET password = %s, first_time_login = %s WHERE admin_id = %s""", (new_password, is_first_time_login, user_id))

            if cur.rowcount > 0:
                message = {
                    'status': 200,
                    'description': 'Password updated successfully'
                }
                return jsonify(message), 200

        except Exception as error:
            message = {
                'status': 501,
                'description': 'Failed to update password. Error: ' + str(error)
            }
            ErrorLogger().logError(message)
            return jsonify(message), 501

        finally:
            mysql.get_db().commit()
            cur.close()
            
    def change_password(self):
        data = request.get_json()

        if not data:
            message = {
                'status': 402,
                'description': 'Request data is missing some details!'
            }
            return jsonify(message), 402

        email = data["email"]
        current_password = data["current_password"]
        new_password = data["new_password"]

        if new_password == current_password:
            message = {
                'status': 401,
                'description': 'New password must be different from the current password!'
            }
            return jsonify(message), 401

        try:  # Test DB connection
            cur = mysql.get_db().cursor()
        except:
            message = {
                'status': 500,
                'description': "Couldn't connect to the Database!"
            }
            return jsonify(message)

        try:
            cur.execute(
                """SELECT * FROM administrators WHERE email = %s""", (email,))
            admin = cur.fetchone()

            if not admin:
                message = {
                    'status': 404,
                    'description': 'User not found!'
                }
                return jsonify(message), 404

            password = admin['password']

            if unhash_password(current_password.encode(), password):
                new_password = hash_password(new_password.encode())

                cur.execute(
                    """UPDATE administrators SET password = %s WHERE email = %s""", (new_password, email))

                message = {
                    'status': 200,
                    'description': 'Password updated successfully'
                }
                return jsonify(message), 200

            else:
                message = {
                    'status': 401,
                    'description': 'Invalid password!'
                }
                return jsonify(message), 401

        except Exception as error:
            message = {
                'status': 501,
                'description': 'Failed to update password. Error: ' + str(error)
            }
            ErrorLogger().logError(message)
            return jsonify(message), 501

        finally:
            mysql.get_db().commit()
            cur.close()

    def renew_token(self):
        try:
            auth = refresh_token()

            message = {
                "auth": auth,
                "status": 200
            }
            return jsonify(message)

        except Exception as e:
            return json.jsonify(str(e)), 500

            
