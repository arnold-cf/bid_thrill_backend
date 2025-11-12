from flask import request, jsonify, json, Response
from api.password.crypt_password import hash_password, unhash_password
from api.payload.payload import Localtime
from modules.payments_module.payments_controller import Payments
from main import mysql, app
from api.logs.logger import ErrorLogger, UssdLogger
from api.alphanumeric.generate import UniqueNumber
import os, re, math, string, random, requests

class GameEngines:
    
    # def generate_game_one_random_ticket(self):
    #     first_char = 'm'
    #     random_chars = random.choices(string.ascii_lowercase, k=6)  # Start with 6 letters
    #     random_number = random.choice(string.digits)  # Choose one random number
    #     random_index = random.randint(0, 6)  # Random index for the number
    #     random_chars.insert(random_index, random_number)  # Insert number into the characters list
    #     random_string = first_char + ''.join(random_chars)
        
    #     return random_string
    
    
    def generate_game_two_random_ticket(self):
        first_char = 'w'
        random_chars = random.choices(string.ascii_lowercase, k=6)  # Start with 6 letters
        random_number = random.choice(string.digits)  # Choose one random number
        random_index = random.randint(0, 6)  # Random index for the number
        random_chars.insert(random_index, random_number)  # Insert number into the characters list
        random_string = first_char + ''.join(random_chars)
        
        return random_string
        

    #Game one Mega Box
    def game_one(self, request_data):
        with app.app_context():
        
            game_option = request_data["game_option"]
            box_selected = request_data["box_selected"] 
            mobile_number = request_data["mobile_number"]
            ussd_session = request_data["session_id"]
            
            try:
                
                first_char = 'm'
                random_chars = random.choices(string.ascii_lowercase, k=6)  # Start with 6 letters
                random_number = random.choice(string.digits)  # Choose one random number
                random_index = random.randint(0, 6)  # Random index for the number
                random_chars.insert(random_index, random_number)  # Insert number into the characters list
                ticket_number = first_char + ''.join(random_chars)
            
                # ticket_number = self.generate_game_one_random_ticket()
                date_created = Localtime().getdate()
                
                game_number = int(game_option)
                box_selected = int(box_selected)
                bet_amount = 20
                mobile_number = mobile_number
                ussd_session = ussd_session
                
                #Generate a ticket by posting data into game one bets 
                cur = mysql.get_db().cursor()
                cur.execute("""INSERT INTO game_one (ticket_number, game_number, box_selected, bet_amount, mobile_number, ussd_session, date_created) VALUES (%s, %s, %s, %s, %s, %s, %s)""", 
                                                    (ticket_number, game_number, box_selected, bet_amount, mobile_number, ussd_session, date_created))
                mysql.get_db().commit()
                rw_count = cur.rowcount
                if rw_count:
                    
                    cur.execute("""SELECT multipliers FROM ussd_session WHERE session_id = %s""", (ussd_session))
                    get_game_options = cur.fetchone()

                    if get_game_options:
                        multipliers = json.loads(get_game_options["multipliers"])  
                        if 1 <= box_selected <= len(multipliers):
                            multiplier_value = multipliers[box_selected - 1]

                            # Optimization: Use a tuple of sorted multipliers as a cache key
                            sorted_multipliers = sorted(set(multipliers))  # Avoid duplicate keys
                            labels_by_rank = ["Boost", "Zoom", "Thrust", "Lift", "Jet", "Flyer"]

                            # Only take as many labels as there are unique multipliers
                            multiplier_label_map = dict(zip(sorted_multipliers, labels_by_rank[:len(sorted_multipliers)]))

                            multiplier_label = multiplier_label_map.get(multiplier_value, "")
                            # multiplier_label = f"x{multiplier_value} : {label}"
                        
                        else:
                            multiplier_value = 0
                            multiplier_label = ''
                            
                    else:
                        multiplier_value = 0
                        multiplier_label = ''
                        
                    #Send STK request with game one ticket id 
                    send_stk_push = {
                        "ticket_number":ticket_number,
                        "box_selected":box_selected,
                        "multiplier_label":multiplier_label,
                        "bet_amount":bet_amount,
                        "mobile_number":mobile_number
                    }
                    Payments().gg_pesa_paybill_stk(send_stk_push)
                    
                    message = {
                        'status': 200,
                        'description': "Payment initiated successfully!"
                    }
                    return jsonify(message)
                    
                    #Run the random number generator when a payment has been received
                
            
            except Exception as error:
                return jsonify({
                    'status': 500,
                    'description': f'Error on game one engine: {str(error)}'
                }), 500

            finally:
                cur.close()
    
    #Game two Kikapu Box
    def game_two(self, request_data):
        
        game_option = request_data["game_option"]
        box_selected = request_data["box_selected"] 
        mobile_number = request_data["mobile_number"]
        ussd_session = request_data["session_id"]
        
        try:
            cur = mysql.get_db().cursor()
        except Exception:
            return jsonify({
                'status': 500,
                'description': "Couldn't connect to the Database!"
            }), 500
        
        try:
            
            ticket_number = self.generate_game_two_random_ticket()
            date_created = Localtime().getdate()
            
            game_number = int(game_option)
            box_selected = int(box_selected)
            bet_amount = 40
            mobile_number = mobile_number
            ussd_session = ussd_session
            
            #Generate a ticket by posting data into game one bets 
            cur.execute("""INSERT INTO game_two (ticket_number, game_number, box_selected, bet_amount, mobile_number, ussd_session, date_created) VALUES (%s, %s, %s, %s, %s, %s, %s)""", 
                                                (ticket_number, game_number, box_selected, bet_amount, mobile_number, ussd_session, date_created))
            mysql.get_db().commit()
            rw_count = cur.rowcount
            if rw_count:
                
                cur.execute("""SELECT multipliers FROM ussd_session WHERE session_id = %s AND msisdn = %s""", (ussd_session, mobile_number))
                get_game_options = cur.fetchone()

                if get_game_options:
                    multipliers = json.loads(get_game_options["multipliers"])  
                    if 1 <= box_selected <= len(multipliers):
                        multiplier_value = multipliers[box_selected - 1]
                        
                        # Step 1: Sort multipliers for ranking
                        sorted_multipliers = sorted(set(multipliers))
                        
                        # Step 2: Define labels by rank
                        labels_by_rank = [
                            "Kikoba", "Uteo", "Kyondo",
                            "Mfuko", "Sanduku", "Gunia"
                        ]
                        
                        # Step 3: Create mapping of multiplier value to label
                        multiplier_label_map = dict(zip(sorted_multipliers, labels_by_rank[:len(sorted_multipliers)]))

                        multiplier_label = multiplier_label_map.get(multiplier_value, "")
                        # multiplier_label = f"Ksh {multiplier_value} : {label}"
                    
                    else:
                        multiplier_value = 0
                        multiplier_label = ''
                        
                else:
                    multiplier_value = 0
                    multiplier_label = ''
                       
                #Send STK request with game one ticket id 
                send_stk_push = {
                    "ticket_number":ticket_number,
                    "box_selected":box_selected,
                    "multiplier_label":multiplier_label,
                    "bet_amount":bet_amount,
                    "mobile_number":mobile_number
                }
                Payments().gg_pesa_paybill_stk(send_stk_push)
                
                message = {
                    'status': 200,
                    'description': "Payment initiated successfully!"
                }
                return jsonify(message)
                
                #Run the random number generator when a payment has been received
        
        except Exception as error:
            return jsonify({
                'status': 500,
                'description': f'Error on game one engine: {str(error)}'
            }), 500

        finally:
            cur.close()                                 
    
    # def mpesa_b2c(self):
    #     details = request.get_json()
    #     if details == None:
    #         message = {"status":402,
    #                    'error':'LD_01',
    #                    "description":"All details are required!"}
    #         ErrorLogger().logError(message) 
    #         return message

    #     amount = float(details["amount"])
    #     amount = round(amount, 2)
    #     msisdn = details["disbursement_no"]
    #     created_at = Localtime().gettime()

    #     # Open A connection to the database
    #     try:
    #         cur = mysql.get_db().cursor()
    #     except:
    #         message = {'status':500,
    #                    'error':'LD_02',
    #                    'description':"Couldn't connect to the Database!"}
    #         ErrorLogger().logError(message) 
    #         return message

    #     try:
    #         id = UniqueNumber().MpesaDisbursementRequestId()
    #         status = 0
    #         cur.execute("""INSERT INTO mpesa_b2c_disbursement_requests(id, msisdn, amount, status, created_at) VALUES (%s, %s, %s, %s, %s)""", 
    #                                                                   (id, msisdn, amount, status, created_at))
    #         mysql.get_db().commit()
            
    #         details = {
    #             "msisdn":msisdn,
    #             "amount":amount,
    #             "b2c_request_id":id
    #         }
            
    #         disburse_loan_amount = Payments().b2c_disbursement(details)

    #         if int(disburse_loan_amount["status"]) == 200:               

    #             message = {'status':200,
    #                        'description':"Mpesa B2C was successful!"}
    #             return message
            
    #         else:
    #             return disburse_loan_amount
            
    #         # message = {'status':200,
    #         #            'description':"Mpesa B2C was successful!"}
    #         # return message

    #      # Error handling
    #     except Exception as error:
    #         message = {'status':501,
    #                    'error':'LD_04',
    #                    'description':'Transaction had an error. Error description ' + format(error)}
    #         ErrorLogger().logError(message) 
    #         return message 
    #     finally:
    #         cur.close()