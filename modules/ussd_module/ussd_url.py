from flask import Blueprint

from modules.ussd_module.ussd_controller import Ussd
from flask_jwt_extended import current_user, jwt_required

ussd_bp = Blueprint("ussd_blueprint", __name__)

@ussd_bp.route("/requests", methods=["POST"])
def request():
    return Ussd().request()


