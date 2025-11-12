from flask import Blueprint

from modules.administrator_authentication.administrator_controller import Administrator
from flask_jwt_extended import current_user, jwt_required

administrator_auth_bp = Blueprint("admininistrar_blueprint", __name__)

@administrator_auth_bp.route("/login", methods=["POST"])
def login():
    return Administrator().login()

@administrator_auth_bp.route("/update-initial-password", methods=["PUT"])
@jwt_required()
def update_initial_password():
    user = current_user
    return Administrator().update_initial_password(user)

@administrator_auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user = current_user
    return Administrator().change_password(user)


@administrator_auth_bp.route("/renew-token", methods=["POST"])
@jwt_required(refresh=True)
def renew_token():
    user = current_user
    return Administrator().renew_token(user)


