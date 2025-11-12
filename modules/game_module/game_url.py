from flask import Blueprint

from modules.game_module.game_model import GameModel
from modules.game_module.game_controller import GameEngines
from flask_jwt_extended import current_user, jwt_required

game_bp = Blueprint("game_blueprint", __name__)

# @game_bp.route("/game_one_engine", methods=["POST"])
# def game_one_engine():
#     return GameModel().game_one_engine()

# @game_bp.route("/mpesa-b2c", methods=["POST"])
# def mpesa_b2c():
#     return GameEngines().mpesa_b2c()





