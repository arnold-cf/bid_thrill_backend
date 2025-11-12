from flask import request, jsonify, json, Response
from api.payload.payload import Localtime
from main import mysql, app
from api.logs.logger import ErrorLogger, UssdLogger
import random, requests
from api.alphanumeric.generate import UniqueNumber

class GameModel:
            
    #InitiPayment received
    def game_one_engine(self, details):
        
        ticket_number = details["ticket_number"]
        msisdn = details["msisdn"] 
        bet_amount = float(details["bet_amount"])
        mpesa_ref = details["mpesa_ref"]
        MerchantRequestID = details["MerchantRequestID"]

        # Connect to db1 and insert transaction details
        try:
            cur = mysql.get_db().cursor()
        except Exception:
            return jsonify({
                'status': 500,
                'description': "Couldn't connect to the Database!"
            }), 500
        
        try:
            #Game engine logic
            date_created = Localtime().getdate()
            multiplier_value = 0
            multipliers = []
            cur.execute("""SELECT box_selected, bet_amount, mobile_number, ussd_session FROM game_one WHERE ticket_number = %s""", (ticket_number))
            get_ticket = cur.fetchone()
            if get_ticket:
                box_selected = int(get_ticket["box_selected"])
                bet_amount = float(get_ticket["bet_amount"])
                mobile_number = get_ticket["mobile_number"]
                ussd_session = get_ticket["ussd_session"]
                
                cur.execute("""SELECT multipliers FROM ussd_session WHERE session_id = %s AND msisdn = %s""", (ussd_session, mobile_number))
                get_session = cur.fetchone()
                if get_session:
                    
                    multipliers = json.loads(get_session["multipliers"])  
                    if 1 <= box_selected <= len(multipliers):
                        multiplier_value = float(multipliers[box_selected - 1])
                        
                        # Step 1: Sort multipliers for ranking
                        sorted_multipliers = sorted(multipliers)
                        
                        # Step 2: Define labels by rank
                        labels_by_rank = ["Boost", "Zoom", "Thrust", "Lift", "Jet", "Flyer"]
                        
                        # Step 3: Create mapping of multiplier value to label
                        multiplier_label_map = {
                            value: label for value, label in zip(sorted_multipliers, labels_by_rank)
                        }
                        
                        # Step 4: Build the final label
                        label = multiplier_label_map.get(multiplier_value, "")
                        multiplier_label = f"x{multiplier_value} : {label}"
                
                    random_number = self.generate_weighted_random(box_selected)
                    b2c_mpesa_balance = 20000 #get actual value
                    
                    #First, Check if outcome should be a win or a loss. 
                    cur.execute("""SELECT next_results, number_of_play FROM game_one_stats WHERE msisdn = %s""", (mobile_number))
                    get_outcome = cur.fetchone()
                    if get_outcome:
                        next_results = int(get_outcome["next_results"])
                        number_of_play = int(get_outcome["number_of_play"])
                    else:
                        next_results = 0
                        number_of_play = 0
                        this_ticket = 0
                        
                        cur.execute("INSERT INTO game_one_stats (msisdn, ticket_number, date_created) VALUES (%s, %s, %s)",
                                                         (mobile_number,   this_ticket, date_created))
                        mysql.get_db().commit()
                    
                    #game won
                    if (next_results == 1 and (int(box_selected) == int(random_number) and (multiplier_value < 11) and (b2c_mpesa_balance >= 20000))):
                        
                        #COMPUTE THE AMOUNT WON!.. If Punter Deposited 20/=, stake amount is 20 - 8 (60% or amount deposited was used to stake), multiply 12 by the multiplier and send it to the PUNTER
                        stake_amount = bet_amount * 60/100
                        amountwon = multiplier_value * stake_amount
                        
                        if amountwon <= bet_amount:
                            amount_won = bet_amount + 5
                        else:
                            amount_won = amountwon
                                
                        cur.execute("""UPDATE game_one SET paid = 1, won = 1, fetched_success = 1, amount_won = %s, stake_amount = %s, mpesa_ref = %s, MerchantRequestID = %s, random_number = %s WHERE ticket_number = %s AND mobile_number = %s""", (amount_won, stake_amount, mpesa_ref, MerchantRequestID, random_number, ticket_number, mobile_number))
                        mysql.get_db().commit()
                        
                        cur.execute("""UPDATE game_one_stats SET number_of_play = number_of_play + 1, number_of_wins = number_of_wins + 1, previous_results = 1, next_results = 0, date_updated = %s WHERE msisdn = %s AND ticket_number != %s""", (date_created, mobile_number, ticket_number))
                        mysql.get_db().commit()
                        
                        #### SEND REQUEST TO B2C TO DISBURSE THE FUNDS
                        id = UniqueNumber().MpesaDisbursementRequestId()
                        status = 0
                        game_no = 1
                        processed = 0
                        cur.execute("""INSERT INTO mpesa_b2c_disbursement_requests(id, msisdn,     amount, game_no, ticket_number, status, processed, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                                                  (id, msisdn, amount_won, game_no, ticket_number, status, processed, date_created))
                        
                        ## Send this to game won function
                
                        #Send SMS 
                        sms_content = "Congratulations!!\n\n"
                        sms_content += f"UMESHINDA!\n\n"
                        sms_content += f"Ulichagua:\n"
                        
                        amount_won = float(amount_won)
                        sms_content += f"{box_selected}. Peperusha {label} Ksh {amount_won:,.2f}\n\n"
                        sms_content += f"Cheza tena\n"
                        sms_content += f"Dial *835*55#\n\n"
                        
                        date_created = Localtime().getdate()
                        delivered_status = 0
                        cur.execute("""INSERT INTO sms_log (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status) VALUES (%s, %s, %s, %s, %s, %s)""", 
                                                           (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status))
                        mysql.get_db().commit()
                        smsid = cur.lastrowid
                            
                        #sms sent
                        sms_details = {
                            "msisdn":mobile_number,
                            "sms_content":sms_content,
                            "ticket_number":ticket_number,
                            "smsid":smsid
                        }
                        self.game_sms_engine(sms_details)
                    
                    #game lost
                    ####REGULATE THE ENGINE TO FAVOR A PUNTER WHO HAS LOST MANY TIMES.
                    
                    else :
                        if ((next_results == 1) and (multiplier_value < 10) and (b2c_mpesa_balance >= 350)):
                             
                            #player should win. 
                            stake_amount = bet_amount * 60/100
                            amountwon = multiplier_value * stake_amount
                            
                            if amountwon <= bet_amount:
                                amount_won = bet_amount + 5
                            else:
                                amount_won = amountwon
                            
                            cur.execute("""INSERT INTO game_one_second_chances (ticket_number, box_selected, bet_amount, amount_won, stake_amount, mobile_number, mpesa_ref, MerchantRequestID, date_created) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                                               (ticket_number, box_selected, bet_amount, amount_won, stake_amount, mobile_number, mpesa_ref, MerchantRequestID, date_created))
                            
                            cur.execute("""UPDATE game_one_stats SET number_of_play = number_of_play + 1, number_of_wins = number_of_wins + 1, previous_results = 1, next_results = 0, date_updated = %s, ticket_number = %s WHERE msisdn = %s AND ticket_number != %s""", (date_created, ticket_number, mobile_number, ticket_number))
                            
                            cur.execute("""UPDATE game_one SET paid = 1, won = 1, fetched_success = 1, mpesa_ref = %s, MerchantRequestID = %s, random_number = %s WHERE ticket_number = %s AND mobile_number = %s""", (mpesa_ref, MerchantRequestID, random_number, ticket_number, mobile_number))
                           
                            #### SEND REQUEST TO B2C TO DISBURSE THE FUNDS
                            id = UniqueNumber().MpesaDisbursementRequestId()
                            status = 0
                            game_no = 1
                            processed = 0
                            cur.execute("""INSERT INTO mpesa_b2c_disbursement_requests(id, msisdn,     amount, game_no, ticket_number, status, processed, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                                                      (id, msisdn, amount_won, game_no, ticket_number, status, processed, date_created))
                            
                            #Send SMS 
                            sms_content = "Congratulations!!\n\n"
                            sms_content += f"UMESHINDA!\n\n"
                            sms_content += f"Ulichagua:\n"
                            
                            amount_won = float(amount_won)
                            sms_content += f"{box_selected}. Peperusha {label} Ksh {amount_won:,.2f}\n\n"
                            sms_content += f"Cheza tena\n"
                            sms_content += f"Dial *835*55#\n"
                            
                            delivered_status = 0
                            cur.execute("""INSERT INTO sms_log (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status) VALUES (%s, %s, %s, %s, %s, %s)""", 
                                                               (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status))
                            mysql.get_db().commit()
                            smsid = cur.lastrowid
                                
                            #sms sent
                            sms_details = {
                                "msisdn":mobile_number,
                                "sms_content":sms_content,
                                "ticket_number":ticket_number,
                                "smsid":smsid
                            }
                            self.game_sms_engine(sms_details)
                        
                        else:
                            #player should loose.
                            cur.execute("""UPDATE game_one SET paid=1, won = 2, fetched_success = 1, mpesa_ref = %s, MerchantRequestID = %s, random_number = %s WHERE ticket_number = %s AND mobile_number = %s""", (mpesa_ref, MerchantRequestID, random_number, ticket_number, mobile_number))
                            
                            if ((mobile_number == "254112769729") or (mobile_number == "254112769729")):
                                max_plays = 10000
                            else:
                                max_plays = 100
                                
                            number_of_wins = 25

                            # Calculate approximately how big each section is
                            section_size = max_plays // number_of_wins

                            winning_plays = []

                            for i in range(number_of_wins):
                                start = i * section_size + 1
                                end = (i + 1) * section_size

                                # Make sure last section reaches max_plays
                                if i == number_of_wins - 1:
                                    end = max_plays

                                # Randomly pick one play within this section
                                win_play = random.randint(start, end)
                                winning_plays.append(win_play)

                            winning_plays.sort()

                            # Game simulation
                            while number_of_play < max_plays:
                                number_of_play += 1

                                if number_of_play in winning_plays:
                                    #WIN at Play
                                    cur.execute("""UPDATE game_one_stats SET number_of_play = number_of_play + 1, number_of_losses = number_of_losses + 1, previous_results = 0, next_results = 1, date_updated = %s, ticket_number = %s WHERE msisdn = %s AND ticket_number != %s""", (date_created, ticket_number, mobile_number, ticket_number))
                                else:
                                    #LOSS at Play
                                    cur.execute("""UPDATE game_one_stats SET number_of_play = number_of_play + 1, number_of_losses = number_of_losses + 1, previous_results = 0, next_results = 0, date_updated = %s, ticket_number = %s WHERE msisdn = %s AND ticket_number != %s""", (date_created, ticket_number, mobile_number, ticket_number))
                                
                            if int(box_selected) == int(random_number):
                                
                                thisrandom_number = self.generate_weighted_random(box_selected)
                            else:
                                thisrandom_number = int(random_number)
                            
                            if 1 <= thisrandom_number <= len(multipliers):
                                multiplier_value = float(multipliers[thisrandom_number - 1])
                            
                            this_amount = multiplier_value * bet_amount * 5
                            this_amount = float(this_amount)
                            
                            #### GIVE BONUS
                            points = 3 #bet amount is 20

                            # Check if MSISDN exists
                            cur.execute("""SELECT balance FROM accumulated_points WHERE msisdn = %s""",(mobile_number,))
                            record = cur.fetchone()

                            if record is not None:
                                cur.execute("""UPDATE accumulated_points SET balance = balance + %s WHERE msisdn = %s""",(points, mobile_number))
                            else:
                                cur.execute("""INSERT INTO accumulated_points (msisdn, balance) VALUES (%s, %s)""",(mobile_number, points))
                                
                            mysql.get_db().commit()
                            
                            sms_content = f"Sorry, you missed Aviator Ksh {this_amount:,.2f}\n\n"
                            sms_content += f"Cheza tena\n\n"
                            sms_content += f"Dial *835*55#\n\n"
                            
                            game_no = 1
                            delivered_status = 0
                            
                            cur.execute("""INSERT INTO sms_log (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status) VALUES (%s, %s, %s, %s, %s, %s)""", 
                                                               (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status))
                            mysql.get_db().commit()
                            smsid = cur.lastrowid
                            
                            #sms sent
                            sms_details = {
                                "msisdn":msisdn,
                                "sms_content":sms_content,
                                "ticket_number":ticket_number,
                                "smsid":smsid
                            }
                            self.game_sms_engine(sms_details)
                    
                else:
                    message = {
                            'status': 201,
                            'description': "Game session was not found!"
                            }
                    return jsonify(message)
                    
                message = {
                    'status': 200,
                    'description': "Game closed successfully!"
                }
                return jsonify(message)
            
            else:
                message = {
                    'status': 201,
                    'description': "Ticket was not found!"
                }
                return jsonify(message)
                
            
        except Exception as error:
            message = {'status':501,
                       'error':'mp_042',
                       'description':'Transaction had an error. Error description ' + format(error)}
                       
            return message
        finally:
            cur.close()
    
    def game_two_engine(self, details):
        
        ticket_number = details["ticket_number"]
        msisdn = details["msisdn"] 
        bet_amount = float(details["bet_amount"])
        mpesa_ref = details["mpesa_ref"]
        MerchantRequestID = details["MerchantRequestID"]

        # Connect to db1 and insert transaction details
        try:
            cur = mysql.get_db().cursor()
        except Exception:
            return jsonify({
                'status': 500,
                'description': "Couldn't connect to the Database!"
            }), 500
        
        try:
            
            #Game engine logic
            date_created = Localtime().getdate()
            multiplier_value = 0
            multipliers = []
            cur.execute("""SELECT box_selected, bet_amount, mobile_number, ussd_session FROM game_two WHERE ticket_number = %s""", (ticket_number))
            get_ticket = cur.fetchone()
            if get_ticket:
                box_selected = int(get_ticket["box_selected"])
                bet_amount = float(get_ticket["bet_amount"])
                mobile_number = get_ticket["mobile_number"]
                ussd_session = get_ticket["ussd_session"]
                
                cur.execute("""SELECT multipliers FROM ussd_session WHERE session_id = %s AND msisdn = %s""", (ussd_session, mobile_number))
                get_session = cur.fetchone()
                if get_session:
                    
                    multipliers = json.loads(get_session["multipliers"])  
                    if 1 <= box_selected <= len(multipliers):
                        multiplier_value = float(multipliers[box_selected - 1])
                        
                        # Step 1: Sort multipliers for ranking
                        sorted_multipliers = sorted(multipliers)
                        
                        # Step 2: Define labels by rank
                        labels_by_rank = ["Kikoba", "Uteo", "Kyondo", "Mfuko", "Sanduku", "Gunia"]
                        
                        # Step 3: Create mapping of multiplier value to label
                        multiplier_label_map = {
                            value: label for value, label in zip(sorted_multipliers, labels_by_rank)
                        }
                        
                        # Step 4: Build the final label
                        label = multiplier_label_map.get(multiplier_value, "")
                        multiplier_label = f"{label} x{multiplier_value}"
                
                    random_number = self.generate_weighted_random(box_selected)
                    b2c_mpesa_balance = 5000 #get actual value
                    
                    #First, Check if outcome should be a win or a loss. 
                    cur.execute("""SELECT next_results, number_of_play FROM game_two_stats WHERE msisdn = %s""", (mobile_number))
                    get_outcome = cur.fetchone()
                    if get_outcome:
                        next_results = int(get_outcome["next_results"])
                        number_of_play = int(get_outcome["number_of_play"])
                    else:
                        next_results = 0
                        number_of_play = 0
                        this_ticket = 0
                        
                        cur.execute("INSERT INTO game_two_stats (msisdn, ticket_number, date_created) VALUES (%s, %s, %s)",
                                                         (mobile_number,   this_ticket, date_created))
                        mysql.get_db().commit()
                
                    #game won
                    if (next_results == 1 and (int(box_selected) == int(random_number) and (multiplier_value < 250) and (b2c_mpesa_balance >= 5000))):
                        
                        ####
                        #### COMPUTE THE AMOUNT WON!.. Punter has to select which basket is missing 40/= to be full. Only use 60% of the stake amount to bet
                        ####
                        amount_won = multiplier_value
                        cashoutamount = multiplier_value * 60/100
                        
                        if cashoutamount <= bet_amount:
                            cashout_amount = bet_amount + 10
                        else:
                            cashout_amount = cashoutamount
                        cur.execute("""UPDATE game_two SET paid = 1, won = 1, fetched_success = 1, amount_won = %s, cashout_amount = %s, mpesa_ref = %s, MerchantRequestID = %s, random_number = %s WHERE ticket_number = %s AND mobile_number = %s""", (amount_won, cashout_amount, mpesa_ref, MerchantRequestID, random_number, ticket_number, mobile_number))
                        mysql.get_db().commit()
                        
                        cur.execute("""UPDATE game_two_stats SET number_of_play = number_of_play + 1, number_of_wins = number_of_wins + 1, previous_results = 1, next_results = 0, date_updated = %s WHERE msisdn = %s AND ticket_number != %s""", (date_created, mobile_number, ticket_number))
                        mysql.get_db().commit()
                        
                        #### SEND REQUEST TO B2C TO DISBURSE THE FUNDS
                        id = UniqueNumber().MpesaDisbursementRequestId()
                        status = 0
                        game_no = 2
                        processed = 0
                        cur.execute("""INSERT INTO mpesa_b2c_disbursement_requests(id, msisdn,         amount, game_no, ticket_number, status, processed, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                                                  (id, msisdn, cashout_amount, game_no, ticket_number, status, processed, date_created))
                        
                        ## Send this to game won function
                
                        #Send SMS 
                        sms_content = "Congratulations!!\n\n"
                        sms_content += f"UMESHINDA!\n\n"
                        sms_content += f"Ulichagua:\n"
                        
                        cashout_amount = float(cashout_amount)
                        sms_content += f"{box_selected}. Jaza {label} Ksh {cashout_amount:,.2f}\n\n"
                        sms_content += f"Cheza tena!\n"
                        sms_content += f"Dial *835*55#\n\n"
                        
                        date_created = Localtime().getdate()
                        delivered_status = 0
                        cur.execute("""INSERT INTO sms_log (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status) VALUES (%s, %s, %s, %s, %s, %s)""", 
                                                           (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status))
                        mysql.get_db().commit()
                        smsid = cur.lastrowid
                            
                        #sms sent
                        sms_details = {
                            "msisdn":mobile_number,
                            "sms_content":sms_content,
                            "ticket_number":ticket_number,
                            "smsid":smsid
                        }
                        self.game_sms_engine(sms_details)
                    
                    #game lost
                    ####
                    #### REGULATE THE ENGINE TO FAVOR A PUNTER WHO HAS LOST MANY TIMES.
                    ####
                    else :
                        
                        if ((next_results == 1) and (multiplier_value < 250) and (b2c_mpesa_balance >= 500)):
                             
                            #player should win. 
                            cashout_amount = multiplier_value * 60/100
                            amount_won = multiplier_value
                            
                            if cashout_amount <= bet_amount:
                                cashout_amount = bet_amount + 10
                            else:
                                cashout_amount = cashout_amount
                            cur.execute("""INSERT INTO game_two_second_chances (ticket_number, box_selected, bet_amount, amount_won, cashout_amount, mobile_number, mpesa_ref, MerchantRequestID, date_created) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                                               (ticket_number, box_selected, bet_amount, amount_won, cashout_amount, mobile_number, mpesa_ref, MerchantRequestID, date_created))
                            
                            
                            cur.execute("""UPDATE game_two_stats SET number_of_play = number_of_play + 1, number_of_wins = number_of_wins + 1, previous_results = 1, next_results = 0, date_updated = %s, ticket_number = %s WHERE msisdn = %s AND ticket_number != %s""", (date_created, ticket_number, mobile_number, ticket_number))
                            
                            
                            cur.execute("""UPDATE game_two SET paid = 1, won = 1, fetched_success = 1, mpesa_ref = %s, MerchantRequestID = %s, random_number = %s WHERE ticket_number = %s AND mobile_number = %s""", (mpesa_ref, MerchantRequestID, random_number, ticket_number, mobile_number))
                            mysql.get_db().commit()
                            
                            #### SEND REQUEST TO B2C TO DISBURSE THE FUNDS
                            id = UniqueNumber().MpesaDisbursementRequestId()
                            status = 0
                            game_no = 2
                            processed = 0
                            cur.execute("""INSERT INTO mpesa_b2c_disbursement_requests(id, msisdn,         amount, game_no, ticket_number, status, processed, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                                                      (id, msisdn, cashout_amount, game_no, ticket_number, status, processed, date_created))
                            
                            ## Send this to game won function
                            #Send SMS 
                            sms_content = "Congratulations!!\n\n"
                            sms_content += f"UMESHINDA!\n\n"
                            sms_content += f"Ulichagua:\n"
                            
                            cashout_amount = float(cashout_amount)
                            sms_content += f"{box_selected}. Jaza {label} Ksh {cashout_amount:,.2f}\n\n"
                            sms_content += f"Cheza tena\n\n"
                            sms_content += f"Dial *835*55#\n\n"
                            
                            delivered_status = 0
                            cur.execute("""INSERT INTO sms_log (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status) VALUES (%s, %s, %s, %s, %s, %s)""", 
                                                               (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status))
                            mysql.get_db().commit()
                            smsid = cur.lastrowid
                                
                            #sms sent
                            sms_details = {
                                "msisdn":mobile_number,
                                "sms_content":sms_content,
                                "ticket_number":ticket_number,
                                "smsid":smsid
                            }
                            self.game_sms_engine(sms_details)
                        
                        else:
                            #player should loss.
                            cur.execute("""UPDATE game_two SET paid = 1, won = 2, fetched_success = 1, mpesa_ref = %s, MerchantRequestID = %s, random_number = %s WHERE ticket_number = %s AND mobile_number = %s""", (mpesa_ref, MerchantRequestID, random_number, ticket_number, mobile_number))
                            
                            if ((mobile_number == "254112769729") or (mobile_number == "254112769729")):
                                max_plays = 10000
                            else:
                                max_plays = 100
                            
                            number_of_wins = 25

                            # Calculate approximately how big each section is
                            section_size = max_plays // number_of_wins

                            winning_plays = []

                            for i in range(number_of_wins):
                                start = i * section_size + 1
                                end = (i + 1) * section_size

                                # Make sure last section reaches max_plays
                                if i == number_of_wins - 1:
                                    end = max_plays

                                # Randomly pick one play within this section
                                win_play = random.randint(start, end)
                                winning_plays.append(win_play)

                            winning_plays.sort()

                            # Game simulation
                            while number_of_play < max_plays:
                                number_of_play += 1

                                if number_of_play in winning_plays:
                                    cur.execute("""UPDATE game_two_stats SET number_of_play = number_of_play + 1, number_of_losses = number_of_losses + 1, previous_results = 0, next_results = 1, date_updated = %s, ticket_number = %s WHERE msisdn = %s AND ticket_number != %s""", (date_created, ticket_number, mobile_number, ticket_number))
                                else:
                                    cur.execute("""UPDATE game_two_stats SET number_of_play = number_of_play + 1, number_of_losses = number_of_losses + 1, previous_results = 0, next_results = 0, date_updated = %s, ticket_number = %s WHERE msisdn = %s AND ticket_number != %s""", (date_created, ticket_number, mobile_number, ticket_number))
                                
                            ## Send this to game lost function
                            if int(box_selected) == int(random_number):
                                thisrandom_number = self.generate_weighted_random(box_selected)
                            else:
                                thisrandom_number = int(random_number)
                            
                            
                            if 1 <= thisrandom_number <= len(multipliers):
                                multiplier_value = float(multipliers[thisrandom_number - 1])
                                # Step 1: Sort multipliers for ranking
                                sorted_multipliers = sorted(multipliers)
                                
                                # Step 2: Define labels by rank
                                labels_by_rank = ["Kikoba", "Uteo", "Kyondo", "Mfuko", "Sanduku", "Gunia"]
                                
                                # Step 3: Create mapping of multiplier value to label
                                multiplier_label_map = {
                                    value: label for value, label in zip(sorted_multipliers, labels_by_rank)
                                }
                                
                                # Step 4: Build the final label
                                missed_label = multiplier_label_map.get(multiplier_value, "")
                            
                            #### GIVE BONUS
                            
                            points = 5 #bet amount is 40

                            # Check if MSISDN exists
                            cur.execute("""SELECT balance FROM accumulated_points WHERE msisdn = %s""",(mobile_number,))
                            record = cur.fetchone()

                            if record is not None:
                                cur.execute("""UPDATE accumulated_points SET balance = balance + %s WHERE msisdn = %s""",(points, mobile_number))
                            else:
                                cur.execute("""INSERT INTO accumulated_points (msisdn, balance) VALUES (%s, %s)""",(mobile_number, points))
                                
                            mysql.get_db().commit()
                            
                            this_amount = multiplier_value * 5
                            this_amount = float(this_amount)
                            
                            sms_content = f"Sorry, you missed jaza {missed_label}. Ksh {this_amount:,.2f}\n\n"
                            sms_content += f"Cheza tena\n\n"
                            sms_content += f"Dial *835*55#\n\n"
                            
                            game_no = 2
                            date_created = Localtime().getdate()
                            delivered_status = 0
                            cur.execute("""INSERT INTO sms_log (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status) VALUES (%s, %s, %s, %s, %s, %s)""", 
                                                               (ticket_number, game_no, mobile_number, sms_content, date_created, delivered_status))
                            mysql.get_db().commit()
                            smsid = cur.lastrowid
                            
                            #sms sent
                            sms_details = {
                                "msisdn":msisdn,
                                "sms_content":sms_content,
                                "ticket_number":ticket_number,
                                "smsid":smsid
                            }
                            self.game_sms_engine(sms_details)
            
                else:
                    message = {
                            'status': 201,
                            'description': "Game session was not found!"
                            }
                    return jsonify(message)
                    
                message = {
                    'status': 200,
                    'description': "Game closed successfully!"
                }
                return jsonify(message)
            
            else:
                message = {
                    'status': 201,
                    'description': "Ticket was not found!"
                }
                return jsonify(message)
                
            
        except Exception as error:
            message = {'status':501,
                       'error':'mp_042',
                       'description':'Transaction had an error. Error description ' + format(error)}
                       
            return message
        finally:
            cur.close()
            
    def game_sms_engine(self, details):
        
        phone_number = details["msisdn"]
        sms_content = details["sms_content"]
        ticket_number = details["ticket_number"]
        smsid = details["smsid"]
        
        mobileNumber = ''.join(phone_number.split())   
        msisdn = '254' + mobileNumber[-9:]  
        
        url = app.config['SMS_API_URL']            
        content = sms_content[0:400]
        
        payload = {
            "SenderId": app.config['SMS_SENDER_ID'],
            "MessageParameters": [{"Number": msisdn, "Text": content}],
            "ApiKey": app.config['SMS_API_KEY'],
            "ClientId": app.config['SMS_CLIENT_ID'],
        }
        headers = {
            'Content-Type': "application/json",
            'AccessKey': app.config['SMS_ACCESS_KEY'],
        }
        res = requests.request("POST", url, data=json.dumps(payload), headers=headers)
        json_res = json.loads(res.text)
        
        ##insert into the database
        if json_res['ErrorCode'] == 0:
            
            cur =  mysql.get_db().cursor()
            cur.execute("""UPDATE sms_log SET delivered_status = 1 WHERE id = %s AND ticket_number = %s""", (smsid, ticket_number))
            mysql.get_db().commit()
        
        else:
            pass
        
        response = {    
                    'payload':json_res,
                    'description': "SMS sending successful and saved!",
                    'status': 200
                    }
        return response 
        
    def generate_weighted_random(self, player_choice):
        # 30% win probability (random number matches the input)
        ### win_probability = 1.00 → 100% chance of winning (everyone always wins)
        # win_probability = 0.40
        win_probability = 0.30
        # win_probability = 1
        
        if player_choice not in range(1, 7):
            raise ValueError("Player choice must be between 1 and 6")
        
        # Decide win or lose based on probability
        if random.random() <= win_probability:
            # Win: return the same number the player chose
            return player_choice
        else:
            # Lose: return a different number
            other_numbers = [n for n in range(1, 7) if n != player_choice]
            return random.choice(other_numbers)
            


        