from flask import Blueprint

from modules.telegram_module.telegram_controller import Telegram
from flask_jwt_extended import current_user, jwt_required

tel_bp = Blueprint("telegram_blueprint", __name__)

@tel_bp.route("/app-response", methods=["POST"])
def app_response():
    return Telegram().app_response()


