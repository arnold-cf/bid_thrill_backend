from flask import Blueprint

from modules.auction_module.auction_model import AuctionModel
from flask_jwt_extended import current_user, jwt_required

auction_bp = Blueprint("auction_blueprint", __name__)

# @game_bp.route("/game_one_engine", methods=["POST"])
# def game_one_engine():
#     return GameModel().game_one_engine()

# @game_bp.route("/mpesa-b2c", methods=["POST"])
# def mpesa_b2c():
#     return GameEngines().mpesa_b2c()





