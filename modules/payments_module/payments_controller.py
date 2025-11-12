from flask import jsonify, request, json
from asyncio.log import logger
from datetime import datetime
import os, base64, requests, math, pymysql
from requests.auth import HTTPBasicAuth
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from api.logs.logger import MpesaLogger, ErrorLogger
from api.payload.payload import Localtime
from api.alphanumeric.generate import UniqueNumber
from modules.sms_module.sms_model import SMS
from modules.auction_module.auction_model import AuctionModel
from main import mysql, app

class Payments:
    # Mpesa Till number
    def generate_c2b_till_access_token(self):
        try:
            consumer_key =  app.config['MPESA_C2B_TILL_CONSUMER_KEY']
            consumer_secret =  app.config['MPESA_C2B_TILL_CONSUMER_SECRET']
            
            url = app.config['MPESA_C2B_TILL_TOKEN_URL']
            res = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
            
            # json_resp = json.loads(res.text)
            json_resp = res.json()
            access_token = json_resp['access_token']

            return access_token
        except Exception as e:
            print(e)
            return None
    
    # Mpesa Till number
    def generate_c2b_paybill_access_token(self):
        try:
            consumer_key =  app.config['MPESA_C2B_PAYBILL_CONSUMER_KEY']
            consumer_secret =  app.config['MPESA_C2B_PAYBILL_CONSUMER_SECRET']
            
            url = app.config['MPESA_C2B_PAYBILL_TOKEN_URL']
            res = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
            
            # json_resp = json.loads(res.text)
            json_resp = res.json()
            access_token = json_resp['access_token']

            return access_token
        except Exception as e:
            print(e)
            return None
    
    # Mpesa Till number
    def generate_c2b_paybill_access_pwd(self):
        business_code = str(app.config['MPESA_C2B_PAYBILL_NUMBER'])
        pass_key = app.config['MPESA_C2B_PAYBILL_PASSKEY']
        # business_code = str(app.config['MPESA_C2B_SHORTCODE_TEST'])
        # pass_key = app.config['MPESA_PASSKEY_TEST']
        lipa_time = datetime.now().strftime('%Y%m%d%H%M%S')

        pswd = base64.b64encode((business_code+pass_key+lipa_time).encode())

        return pswd, lipa_time
    
    # Mpesa B2C Paybill number
    def generate_b2c_access_token(self):
        try:
            consumer_key = app.config['MPESA_B2C_CONSUMER_KEY']
            consumer_secret = app.config['MPESA_B2C_CONSUMER_SECRET']
            url = app.config['MPESA_B2C_TOKEN_URL'] 
            res = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
            json_resp = res.json()
            access_token = json_resp['access_token']

            return access_token
        except Exception as e:
            print(e)
            return None
    
    # Mpesa C2B Paybill number
    def gg_pesa_paybill_stk(self, details): 
        #Get the request data 
        if details == None:
                message = {"description":"All details are required!",
                           "status":402}
                MpesaLogger().log(message)
                return message
        
        auction_id = details["auction_id"]
        ticket_number = details["ticket_number"]
        stkamount = float(details["amount"])
        mobile_number = details["mobile_number"]
        
        accountnumber =  str(ticket_number)
        
        mobilenumber = ''.join(mobile_number.split()) 
        msisdn ='254' + mobilenumber[-9:] 
        
        amount = math.ceil(stkamount)
        
        # Connect to db1 and insert transaction details
        try:
            cur = mysql.get_db().cursor()
        except pymysql.MySQLError as e:
            message = {'status': 500, 'description': "Couldn't connect to db1: " + str(e)}
            return jsonify(message)
                
        #Try except block to handle execute task
        
        try:
            access_token = Payments().generate_c2b_paybill_access_token()
            paybill_Number = app.config['MPESA_C2B_PAYBILL_NUMBER']
           
            api_url = app.config['MPESA_C2B_PAYBILL_STK_URL']
            password, lipa_time = Payments().generate_c2b_paybill_access_pwd()
            password = password.decode('utf8')
            callback_url = app.config['MPESA_C2B_PAYBILL_STK_CALLBACK_URL']
            
            headers = {
                'Content-Type': "application/json",
                'Authorization': f"Bearer {access_token}"
            }
            payload = {
                "BusinessShortCode": paybill_Number,
                "Password": password,
                "Timestamp": lipa_time,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": msisdn,
                "PartyB": paybill_Number,
                "PhoneNumber": msisdn,
                "CallBackURL": callback_url,
                "AccountReference": accountnumber,
                "TransactionDesc": "Deposit"
            }

            res = requests.post(api_url, json=payload, headers=headers)
            response = json.loads(res.text)
            
            created_at = Localtime().gettime()
            log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Mpesa_c2b_paybill_stk_Request.json")
            with open(log_file, "a") as file:
                date = Localtime().gettime()
                file.write(f"\n{date}: {response}")

            response_code = response['ResponseCode']

            if response_code == '0':
                MerchantRequestID = response['MerchantRequestID']
                CheckoutRequestID = response['CheckoutRequestID']
                ResponseDescription = response['ResponseDescription']
                CustomerMessage = response['CustomerMessage']
                requestId = "processed"
                errorCode = "processed"
                errorMessage = "processed"
                amount = float(amount)
                status = 1 #stk push was initiated successfully
                
                cur.execute('''INSERT INTO mpesa_paybill_stk_requests (msisdn, amount, ticket_number, auction_id, MerchantRequestID, CheckoutRequestID, ResponseCode, ResponseDescription, CustomerMessage, requestId, errorCode, errorMessage, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                                                                      (msisdn, amount, ticket_number, auction_id, MerchantRequestID, CheckoutRequestID, response_code, ResponseDescription, CustomerMessage, requestId, errorCode, errorMessage, status, created_at))
                mysql.get_db().commit()
                
                message = {
                    "description": "Mpesa paybill stk push was successful",
                    "status": 200                    
                }
                return message

            
            else:
                
                MerchantRequestID = "failed"
                CheckoutRequestID = "failed"
                ResponseDescription = "failed"
                CustomerMessage = "failed"
                requestId = response['requestId']
                errorCode = response['errorCode']
                errorMessage = response['errorMessage']
                status = 0 #stk push initiation failed 
                cur.execute('''INSERT INTO mpesa_paybill_stk_requests (msisdn, amount, ticket_number, auction_id, MerchantRequestID, CheckoutRequestID, ResponseCode, ResponseDescription, CustomerMessage, requestId, errorCode, errorMessage, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                                                                      (msisdn, amount, ticket_number, auction_id, MerchantRequestID, CheckoutRequestID, response_code, ResponseDescription, CustomerMessage, requestId, errorCode, errorMessage, status, created_at))
                mysql.get_db().commit()

                message = {
                    "description": "Mpesa paybill stk push failed",
                    'error':'mp_012',
                    "status": 201                    
                }
                MpesaLogger().log(message)
                return message

        except Exception as error:
            message = {'status':501,
                       'error':'mp_013',
                       'description':'Transaction had an error. Error description ' + format(error)}
            MpesaLogger().log(message)
            return message 
        finally:
            cur.close()
    
    # Mpesa C2B Paybill number
    def gg_pesa_paybill_stk_response(self): 
        #Get the request data 
        details = request.get_json() 
        if details == None:
                message = {"description":"All details are required!",
                        'error':'mp_014',
                        "status":402}
                MpesaLogger().log(message)
                return message
            
        log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Mpesa_C2B_Paybill_STK_Callback_Response.json")
        with open(log_file, "a") as file:
            # json_str = json.dumps(data)
            date = Localtime().gettime()
            file.write(f"\n{date}: {details}")
            
        # account_number = details["account_number"]
        
        # Connect to db1 and insert transaction details
        try:
            cur = mysql.get_db().cursor()
        except pymysql.MySQLError as e:
            message = {'status': 500, 'description': "Couldn't connect to db1: " + str(e)}
            return jsonify(message)
        
        try:
            
            result_body = details['Body']['stkCallback']
            MerchantRequestID = result_body['MerchantRequestID']
            CheckoutRequestID = result_body['CheckoutRequestID']
            ResultCode = int(result_body['ResultCode'])            
            
            if ResultCode == 0:
                trans_amount = float(result_body['CallbackMetadata']['Item'][0]['Value'])            
                mpesa_ref = result_body['CallbackMetadata']['Item'][1]['Value']
                #trans_date = result_body['CallbackMetadata']['Item'][2]['Value']
                #msisdn = result_body['CallbackMetadata']['Item'][3]['Value']

                cur.execute("""SELECT ticket_number, auction_id, amount, msisdn FROM mpesa_paybill_stk_requests WHERE MerchantRequestID = %s AND CheckoutRequestID = %s""", (MerchantRequestID, CheckoutRequestID))
                stk_request = cur.fetchone()
                if stk_request:
                    ticket_number = stk_request["ticket_number"]
                    amount = float(stk_request["amount"])
                    msisdn = stk_request["msisdn"]
                    auction_id = stk_request["auction_id"]

                    #UPDATE STK request status to 2 - processed
                    cur.execute("""UPDATE mpesa_paybill_stk_requests SET status = 2 WHERE MerchantRequestID = %s AND CheckoutRequestID = %s""",(MerchantRequestID, CheckoutRequestID))
                    mysql.get_db().commit()
                    
                    cur.execute("""UPDATE item_one_bids SET status = 1 WHERE ticket_number = %s""",(ticket_number))
                    mysql.get_db().commit()
                    
                    #mpesa_c2b_transactions
                    entry_id =  UniqueNumber().mpesaC2BPaybillRequestId()
                    created_at = Localtime().gettime()

                    cur.execute("""INSERT IGNORE INTO mpesa_paybill_stk_responses (id, ticket_number, auction_id, msisdn, amount, mpesa_ref, merchant_request_id, checkout_request_id, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                                                            (entry_id, ticket_number, auction_id, msisdn, amount, mpesa_ref, MerchantRequestID,   CheckoutRequestID,   created_at))
                    mysql.get_db().commit()
                    
                    rowcount = cur.rowcount
                    if rowcount:
                        game_details = {
                                "ticket_number":ticket_number,
                                "auction_id":auction_id,
                                "msisdn":msisdn,
                                "bet_amount":amount,
                                "mpesa_ref":mpesa_ref,
                                "MerchantRequestID":MerchantRequestID
                            }
                        
                        if ticket_number.startswith('m'):
                            AuctionModel().auction_item_one_engine(game_details)
                            
                        elif ticket_number.startswith('n'):
                            pass
                            AuctionModel().auction_item_two_engine(game_details)
                        
                        elif ticket_number.startswith('p'):
                            pass
                            AuctionModel().auction_item_three_engine(game_details)
                        
                        elif ticket_number.startswith('q'):
                            pass
                            AuctionModel().auction_item_four_engine(game_details)
                        
                        elif ticket_number.startswith('r'):
                            pass
                            AuctionModel().auction_item_five_engine(game_details)
                        
                        else:
                            pass
        
                message = {
                    "description": "Mpesa response was found",
                    "status": 200                    
                }
                return message
            else:
                
                cur.execute("""SELECT msisdn, amount, account_number, ticket_number, ResponseCode, MerchantRequestID FROM mpesa_paybill_stk_requests WHERE MerchantRequestID = %s""", (MerchantRequestID))
                get_res = cur.fetchone()
                if get_res:
                    msisdn = get_res["msisdn"]
                    amount = float(get_res["amount"])
                    account_number = get_res["account_number"]
                    ticket_number = get_res["ticket_number"]
                    ResponseCode = get_res["ResponseCode"]
                    MerchantRequestID = get_res["MerchantRequestID"]
                    
                    gameone_details = {
                                    "account_number":account_number,
                                    "ticket_number":ticket_number,
                                    "msisdn":msisdn,
                                    "bet_amount":amount,
                                    "MerchantRequestID":MerchantRequestID,
                                    "ResponseCode":ResponseCode
                                }
                    
                    #Send back failed stk responses
                    # Payments().game_one_engine_failed_stk(gameone_details)
                
                ## Resend STK Push
                message = {
                    "description": "Mpesa response was not found!",
                    "status": 201                  
                }
                return message
                
        
        except Exception as error:
            message = {'status':501,
                    'error':'mp_016',
                    'description':'Transaction had an error. Error description ' + format(error)}
            MpesaLogger().log(message)
            return message 
        finally:
            cur.close()
            
    # Mpesa C2B Paybill number
    def sm_pay_bill_validatepayurl_(self):
        try:
            request_data = request.get_json()
            
            log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Mpesa_C2B_Paybill_Validation_Logs.json")
            with open(log_file, "a") as file:
                date = Localtime().gettime()
                file.write(f"\n{date}: {request_data}")
                
            # bill_reference_no = request_data['BillRefNumber']
            # shortcode = request_data['BusinessShortCode']
            
            context = {
                    "ResultCode": 0,
                    "ResultDesc": "Accepted"
                }
            return jsonify(context)
        except Exception as e:
            print(f"C2B exception: {str(e)}")
            context = {
                "ResultCode": "C2B00016",
                "ResultDesc": "Rejected"
            }
            return jsonify(context)
    
    # Mpesa C2B Paybill number
    def sm_pay_bill_confirmpayurl_(self):
         # Open A connection to the database
        try:
            cur =  mysql.get_db().cursor()
        except:
            message = {"description":"Couldn't connect to the Database!", 
                        "error":"il_r007",
                        "status": 500}
            ErrorLogger().logError(message)
            return message
                    
        try:
            data = request.get_json()
        
            log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Mpesa_C2B_Paybill_Confirmation_Logs.json")
            with open(log_file, "a") as file:
                # json_str = json.dumps(data)
                date = Localtime().gettime()
                file.write(f"\n{date}: {data}")
                
            if data['TransAmount']:
                TransAmount = float(data['TransAmount'])
                if TransAmount > 0:                
                    amount = TransAmount
                    mpesa_ref = data['TransID']
                    BillRefNumber = data['BillRefNumber']
                    TransactionType = data['TransactionType']
                    TransTime = data['TransTime']
                    BusinessShortCode = data['BusinessShortCode']
                    InvoiceNumber = data['InvoiceNumber']
                    OrgAccountBalance = data['OrgAccountBalance']
                    ThirdPartyTransID = data['ThirdPartyTransID']
                    MSISDN = data['MSISDN']
                    FirstName = data['FirstName']
                        
                    date_created = Localtime().gettime()
                    
                    # cur.execute('''SELECT id, mobile_number from customers WHERE mobile_number = %s''', (BillRefNumber))
                    # customer = cur.fetchone()
                    # if customer:
                    #     customer_id = customer["id"]
                    #     customer_msisdn = customer["mobile_number"]
                        
                    #mpesa_c2b_transactions
                    id =  UniqueNumber().mpesaPaybillTransactionId()
                    
                    cur.execute("""INSERT IGNORE INTO mpesa_c2b_paybill_transactions (id, MSISDN, TransactionType, TransAmount,   TransID, TransTime, BusinessShortCode, BillRefNumber, InvoiceNumber, OrgAccountBalance, ThirdPartyTransID, FirstName, date_created) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                                                                     (id, MSISDN, TransactionType,      amount, mpesa_ref, TransTime, BusinessShortCode, BillRefNumber, InvoiceNumber, OrgAccountBalance, ThirdPartyTransID, FirstName, date_created))
                    mysql.get_db().commit()
                    rowcount = cur.rowcount
                    if rowcount:
                        details = {
                            'amount': amount,
                            'trans_ref':mpesa_ref,
                            'shortcode':'1'
                        }
        
                        message = {'status':200,
                                   'description':'Mpesa C2B Paybill was Successful!'}
                        # MpesaLogger().log(message)
                        
                        return message
                    else:
                        message = {'status':200,
                                    'description':'Mpesa C2B Paybill Transaction Already Exists!'}
                        # MpesaLogger().log(message)
                        
                        return message
                    

        except Exception as error:
            message = {'status':501,
                       'error':'mp_042',
                       'description':'Transaction had an error. Error description ' + format(error)}
            MpesaLogger().log(message)            
            return message 
 
    # Mpesa B2C Paybill number
    def b2c_disbursement(self, details):
    
        if details == None:
            message = {"status": 402,
                       "description": "All details are required!"}
            return message
        
        try:
            msisdn = details['msisdn']
            amount = details['amount']
            amount = math.ceil(amount)
            b2c_request_id = details['b2c_request_id']

            access_token = self.generate_b2c_access_token()
            api_url = app.config['MPESA_B2C_API_URL']  
            initiator = app.config['MPESA_B2C_INITIATOR_NAME']
            queue_timeout_url = app.config['MPESA_B2C_TIMEOUT_URL']
            b2c_callback = app.config['MPESA_B2C_CALLBACK_URL']
            security_cred = app.config['MPESA_B2C_SECURITY_CRED']
            business_code = app.config['MPESA_B2C_SHORTCODE']

            headers = {
                'Content-Type': "application/json",
                'Authorization': f"Bearer {access_token}"
            }
            payload = {
                "InitiatorName": initiator,
                "SecurityCredential": security_cred,
                "CommandID": "BusinessPayment",
                "Amount": amount,
                "PartyA": business_code,
                "PartyB": msisdn,
                "Remarks": "Money Disbursement",
                "QueueTimeOutURL": queue_timeout_url,
                "ResultURL": b2c_callback,
                "Occassion": "Disbursement",
            }
           
            # response = requests.post(api_url, json=payload, headers=headers)
            response = requests.request("POST", api_url, data=json.dumps(payload), headers=headers)
            response_body = response.json()
           
            log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Mpesa_B2C_Requests.json")
            with open(log_file, "a") as file:
                date = Localtime().gettime()
                file.write(f"\n{date}: {response_body}")

            status = response_body["ResponseCode"]
            if status == "0":
                conversationID = response_body["ConversationID"]                
                originatorConversationID = response_body["OriginatorConversationID"]                
                
                # Open A connection to the database
                try:
                    cur = mysql.get_db().cursor()
                except:
                    message = {'status':500,
                               'description':"Couldn't connect to the Database!"}
                    ErrorLogger().logError(message) 
                    return message
                
                #Status = 1 -> Transaction was initiated successfully
                cur.execute("""UPDATE mpesa_b2c_disbursement_requests set status = 1, ConversationID = %s, OriginatorConversationID = %s WHERE id = %s""", (conversationID, originatorConversationID, b2c_request_id))
                mysql.get_db().commit()
                rowcount = cur.rowcount
                if rowcount:
                    message = {'status':200,
                              'description':"Mpesa B2C was successful!"}
                    return message
                
                else:
                    message = {'status':201,
                               'error':'mp_032',
                               'description':"Mpesa B2C was not successful!"}
                    MpesaLogger().log(message)
                    return message
                
            else:
                message = {'status':201,
                           'error':'mp_033',
                           'description':"Mpesa B2C was not successful!"}
                MpesaLogger().log(message)
                return message

        except Exception as error:
            message = {'status':501,
                       'error':'mp_034',
                       'description':'Transaction had an error. Error description ' + format(error)}
            MpesaLogger().log(message)
            return message 
        
    #Mpesa B2C Paybill number
    def b2c_callback_(self):
        data = request.get_json()
        
        log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Mpesa_B2C_Response.json")
        with open(log_file, "a") as file:
            date = Localtime().gettime()
            file.write(f"\n{date}: {data}")
        
        try:   
            result_body = data['Result']
            ResultCode =  int(result_body['ResultCode'])
            ResultDesc =  result_body['ResultDesc']
            originatorConversationID =  result_body['OriginatorConversationID']
            conversationID =  result_body['ConversationID']
            transactionID =  result_body['TransactionID']
            
            if ResultCode == 0:
                #transaction was successful
                TransactionAmount =  float(result_body['ResultParameters']['ResultParameter'][0]['Value'])
                ReceiverPartyPublicName =  result_body['ResultParameters']['ResultParameter'][2]['Value']
                TransactionCompletedDateTime =  result_body['ResultParameters']['ResultParameter'][3]['Value']
                B2CUtilityAccountAvailableFunds =  float(result_body['ResultParameters']['ResultParameter'][4]['Value'])
                B2CWorkingAccountAvailableFunds =  float(result_body['ResultParameters']['ResultParameter'][5]['Value'])
                
                #Open A connection to the database
                try:
                    cur =  mysql.get_db().cursor()
                except:
                    message = {"status":500,
                                "description":"Couldn't connect to the Database!"}            
                    return message
                
                #Status = 1 -> Transaction was processed successfully
                cur.execute("""SELECT id, msisdn FROM mpesa_b2c_disbursement_requests WHERE status =1 AND ConversationID = %s AND OriginatorConversationID = %s """, (conversationID, originatorConversationID))
                get_b2c_request = cur.fetchone()                 
                if get_b2c_request: 
                    b2c_request_id =  get_b2c_request["id"] 
                    msisdn = get_b2c_request["msisdn"] 
                    
                    amount = TransactionAmount
                    status = 1
                    created_at = Localtime().gettime()  
                    mpesa_reference = transactionID 
                    
                    mpesa_time = TransactionCompletedDateTime
                    utility_balance = B2CUtilityAccountAvailableFunds 
                    working_balance = B2CWorkingAccountAvailableFunds
                    
                    thisresponse = ReceiverPartyPublicName.split("-")            
                    mobile_number = thisresponse[0]
                    recipient_name = thisresponse[1]
                    
                    id = UniqueNumber().MpesaDisbursementResponseId()
                    cur.execute("""INSERT INTO mpesa_b2c_disbursement_response(id, b2c_request_id, msisdn, amount, ConversationID, OriginatorConversationID, mpesa_reference, mobile_number, recipient_name, mpesa_time, utility_balance, working_balance, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                                              (id, b2c_request_id, msisdn, amount, conversationID, originatorConversationID, mpesa_reference, mobile_number, recipient_name, mpesa_time, utility_balance, working_balance, status, created_at))
                    mysql.get_db().commit()                         

                    rowcount = cur.rowcount
                    if rowcount:
                        message = {'status':200,
                                   'description':"Mpesa B2C was successful!"}
                        return message
                    
                    else:
                        message = {'status':201,
                                   'error':'mp_037',
                                   'description':"Mpesa B2C was not successful!"}
                        MpesaLogger().log(message)
                        return message
                
                else:
                    message = {'status':201,
                               'error':'mp_038',
                               'description':"Mpesa B2C was not successful!"}
                    MpesaLogger().log(message)
                    return message
                
            else:
                message = {'status':201,
                           'reference':transactionID,
                           'description':ResultDesc}
                ErrorLogger().logError(message) 
                return message

        # Error handling
        except Exception as error:
            message = {'status':501,
                       'error':'mp_039',
                       'description':'Transaction had an error. Error description ' + format(error)}
            ErrorLogger().logError(message) 
            return message
        
    # Mpesa B2C Paybill number
    def b2c_timeout_(self):
        data = request.get_json()
        log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/mpesa_B2C_Timeouts_Response.json")
        with open(log_file, "a") as file:
            date = Localtime().gettime()
            file.write(f"\n{date}: {data}")

        message = {"status":200,
                   "description":"Transaction was successful"}
        return jsonify(message)
    
    # Mpesa B2C Paybill number
    def b2c_results_(self):
        data = request.get_json()
        
        log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/mpesa_B2C_Results_Response.json")
        with open(log_file, "a") as file:
            date = Localtime().gettime()
            file.write(f"\n{date}: {data}")

        message = {"status":200,
                   "description":"Transaction was successful"}
        return jsonify(message)
    
    # Mpesa B2C Paybill number
    def b2c_cron_results_(self):
        data = request.get_json()
        
        ResultCode = data['Result']['ResultCode']
        if ResultCode == 0:
            ConversationID = data['Result']['ConversationID']
            TransactionID = data['Result']['TransactionID']
            ResultDesc = data['Result']['ResultDesc']
            OriginatorConversationID = data['Result']['OriginatorConversationID']
            
            payload = data['Result']['ResultParameters']['ResultParameter'][1]['Value']
            payload = payload.split("&")
            
            payload_date = data['Result']['ResultParameters']['ResultParameter'][2]['Value']
            
            payloaddate = []
            for x in str(payload_date):
                payloaddate.append(int(x))
            
            #payload_
            date_year = str(payloaddate[0]) + str(payloaddate[1]) + str(payloaddate[2]) + str(payloaddate[3])
            date_month = str(payloaddate[4]) + str(payloaddate[5])
            date_day = str(payloaddate[6]) + str(payloaddate[7])
            date_hour = str(payloaddate[8]) + str(payloaddate[9])
            date_minute = str(payloaddate[10]) + str(payloaddate[11])
            date_second = str(payloaddate[12]) + str(payloaddate[13])
            
            date_checked = date_year + "-" + date_month + "-" + date_day + " " + date_hour + ":" + date_minute + ":" + date_second
                       
            workingaccount = payload[0]
            workingaccountbalance = workingaccount.split("|")
            
            working_acc_balance = workingaccountbalance[2]
            
            utilityaccount = payload[1]
            utilityaccountbalance = utilityaccount.split("|")
            
            utility_acc_balance = utilityaccountbalance[2]
            
            chargespaidaccount = payload[2]
            chargespaidaccountbalance = chargespaidaccount.split("|")
            
            chargespaid_acc_balance = chargespaidaccountbalance[2]
            
            merchantaccount = payload[3]
            merchantaccountbalance = merchantaccount.split("|")
            
            merchant_acc_balance = merchantaccountbalance[2]
            
            ########################################################################
            #######INSERT INTO DB############################ 
            #Open A connection to the database
            try:
                cur =  mysql.get_db().cursor()
            except:
                message = {"status":500,
                            "description":"Couldn't connect to the Database!"}            
                return message
            
            shortcode = 3034197
            
            date_created = Localtime().gettime()
            status = ResultCode
                
            cur.execute("""UPDATE mpesa_paybill_b2c_balance SET working_acc_balance = %s, utility_acc_balance = %s, chargespaid_acc_balance = %s, merchant_acc_balance = %s, date_checked = %s, date_created = %s, status = %s, ResultDesc = %s, OriginatorConversationID = %s, ConversationID = %s, TransactionID = %s WHERE shortcode = %s""", 
                                                               (working_acc_balance,      utility_acc_balance,      chargespaid_acc_balance,      merchant_acc_balance,      date_checked,      date_created,      status,      ResultDesc,      OriginatorConversationID,      ConversationID,      TransactionID, shortcode))
            mysql.get_db().commit()

            message = {"status":200,
                       "description":"Transaction was successful"}
            return jsonify(message)
        else:
            message = {"status":201,
                       'error':'mp_040',
                       "description":"Transaction was not successful"}
            MpesaLogger().log(message)
            return jsonify(message)