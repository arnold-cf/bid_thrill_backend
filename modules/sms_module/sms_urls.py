from flask import Blueprint
from modules.sms_module.sms_model import SMS
from flask_jwt_extended import current_user, jwt_required

sms_bp = Blueprint('sms_blueprint', __name__)

@sms_bp.route("/points-sms", methods=["POST"])
def points_sms():
    return SMS().points_sms()











