from flask import Blueprint

from modules.payments_module.payments_controller import Payments
from flask_jwt_extended import current_user, jwt_required

payments_bp = Blueprint("payments_blueprint", __name__)

#find M_Pesa_Payment Paybill Stk response
@payments_bp.route('/sm-pay-bill-stk-callback', methods=['POST'])
def gg_pesa_paybill_stk_response():
    return Payments().gg_pesa_paybill_stk_response()

#C2B M_Pesa_Payment Paybill Validation
@payments_bp.route('/sm-validate-pay-url', methods=['POST'])
def sm_pay_bill_validatepayurl_():    
    return Payments().sm_pay_bill_validatepayurl_()

#C2B M_Pesa_Payment Paybill Confirmation
@payments_bp.route('/sm-confirm-pay-url', methods=['POST'])
def sm_pay_bill_confirmpayurl_():
    return Payments().sm_pay_bill_confirmpayurl_()

#B2C Initiated
@payments_bp.route('/b2c-initiated-disbursement', methods=['POST'])
@jwt_required()
def b2c_disbursement():
    user = current_user
    return Payments().b2c_disbursement(user)

#B2C callback response
@payments_bp.route('/b2c_callback_', methods=['POST'])
def b2c_callback_():
    return Payments().b2c_callback_()

#B2C timeout
@payments_bp.route('/b2c_timeout_', methods=['POST'])
def b2c_timeout_():
    return Payments().b2c_timeout_()

#B2C results
@payments_bp.route('/b2c_results_', methods=['POST'])
def b2c_results_():
    return Payments().b2c_results_()

#B2C balance cron job
@payments_bp.route('/b2c_cron_results_', methods=['POST'])
def b2c_cron_results_():
    return Payments().b2c_cron_results_()



