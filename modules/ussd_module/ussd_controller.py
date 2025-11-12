from flask import request, jsonify, json, Response
from api.password.crypt_password import hash_password, unhash_password
from api.payload.payload import Localtime
from main import mysql, app
from api.logs.logger import ErrorLogger, UssdLogger
import os, random, string
from modules.game_module.game_controller import GameEngines
from api.alphanumeric.generate import UniqueNumber

class Ussd:
    
    def request(self):
        # Get the request data from ussd
        
        request_data = request.get_json()
        UssdLogger().log(request_data)

        if request_data == None:
            message = {'status':402,
                       'error':'us_s01',
                       'description':'Request data is missing some details!'}

            ErrorLogger().logError(message)
            return message
        else:
            pass

        try:
            
            msisdn = request_data["msisdn"]
            session_id = request_data["sessionId"]            
            service_code = request_data["serviceCode"]
            text = request_data["ussdString"]
            
            details = {"msisdn":msisdn,
                       "text":text,
                       "service_code":service_code,
                       "session_id":session_id
                       }
            
            # if ((msisdn == "254112769729") or (msisdn == "254791477417")):
            #     cancel_response = "Process not allowed!"
            #     response = {"description":cancel_response, 
            #                 "status":1000}
            #     return response
            # else:
            #     pass
                
                
            #Call the initial ussd API data processor
            
            process_response = Ussd().initial_process(details)

            
            if int(process_response["status"]) in [1000, 1001, 1002]:
                return Response(response=process_response['description'], status=200)

            #User canceled a transaction
            elif int(process_response["status"]) == 999:
                return Response(response=process_response['description'], status=200) 
            
            else:
                message = {'status':process_response['status'],
                           'error':'us_s06',
                           'description':"Error updating customer details. Error description, " + process_response['description']}

                ErrorLogger().logError(message)            
                return Response(response=message)
            
        except Exception as error:
            message = {'status':402,
                       'error':'us_s07',
                       'description':"Request data is missing some details!. Error descriptions, " + format(error)}

            ErrorLogger().logError(message)            
            return Response(response=message)

            
    def initial_process(self, details):
        request_data = details
        if request_data == None:
            message = {'status':402,
                       'error':'us_s08',
                       'description':'Request data is missing some details!'}

            ErrorLogger().logError(message)
            return message
        
        msisdn = request_data["msisdn"]
        text = request_data["text"]
        service_code = request_data["service_code"]
        session_id = request_data["session_id"]
        
        request_time = Localtime().gettime()

        if text is not None:
            txt_string = text.split('*')
        else:
            txt_string = ''

        txt_string_len = len(txt_string) 
        user_input = txt_string[-1]

        if user_input == '':
            user_input = 00
        
        menu_text = ''
        
        #Initialize Menus
        
        main_menu_text = "CON WIN Ksh 2 MILLI\n\n"
        main_menu_text += f"1. Aviator (Ksh 20)\n"
        main_menu_text += f"2. Kikapu Milli (Ksh 40)\n"
        main_menu_text += f"0. Redeem Points\n"
        
        game_two_payment_info = "Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 40"

        # log request data to a json file
        request_data["datecreated"] = Localtime().gettime()
        request_data = str(request_data)
        
        file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Ussd_Incoming_Response.json")
        with open(file, "a") as fo:
            fo.write(request_data)
        
        details = {
            "session_id":session_id,
            "msisdn":msisdn,
            "request_time":request_time
        }
        
        #Establish database connection
        try:
            cur =  mysql.get_db().cursor()

        except mysql.get_db().Error as error:

            message = {
                    "status":500,
                    'error':'us_s09',
                    "description":"Couldn't connect to the Database!" + format(error)
                    }
            ErrorLogger().logError(message)
            return message
        
        ############################ Get Session ##################!!!!
        #Check if session ID already exists in the database
        try:
            cur.execute("""SELECT dialed FROM ussd_session WHERE session_id= %s """, (session_id))
            session_exists = cur.fetchone()
            if session_exists:
                dialed = session_exists['dialed']
                
            else:
                dialed = 1
                cur.execute("""INSERT INTO ussd_session (session_id, input_string, msisdn, request_time, dialed) VALUES (%s, %s, %s, %s, %s)""", (session_id, "XXXX", msisdn, request_time, dialed))
                mysql.get_db().commit()
                
            
        except mysql.get_db().Error as error:
            message = {'status':502,
                       'error':'us_s10',
                       'description':'Failed to fetch session data from database.!' + format(error)}
            ErrorLogger().logError(message)
            return message
        
        # Get Customer Database Input Strings
        try:
            cur.execute("""SELECT input_string FROM ussd_session WHERE session_id= %s """, (session_id))
            get_inputs = cur.fetchone()
            if get_inputs:
                user_inputs = get_inputs["input_string"]
                if user_inputs is not None:
                    inputs = user_inputs.split("*")
                    txt_length = len(inputs)                        
                else:
                    txt_length = 0
                    user_inputs = ''
            else:
                txt_length = 0
                user_inputs = ''
        
        except Exception as error:
            message = {'status':505,
                        'error':'us_s15',
                        'description':'Failed to fetch users string of inputs!' + format(error)}
            ErrorLogger().logError(message)
            return message
        
        # Punter dialed ussd 
        
        if (text == ""):
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", ("XXXX", session_id))
            mysql.get_db().commit()
            
            response = {"description":main_menu_text,
                        "status":1000}
            return response
        
        # Punter entered 00 to go back to Main Menu 
        elif user_input == '00':
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", ("XXXX", session_id))
            mysql.get_db().commit()
                    
            response = {"description":main_menu_text,
                        "status":1000}
            return response
        
        #Punter has selected Game 1 option on Main Menu. System displays Game 1 Menu
        elif txt_length == 1 and user_input == "1":
            # Update input_string
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", ("XXXX*1", session_id))

            # Game mechanics starts here
            multiplier_ranges = [(2, 5), (6, 9), (11, 100), (300, 999), (2000, 6999), (7000, 9999)]

            # Generate multipliers and shuffle them
            multipliers = [round(random.uniform(start, end), 1) for start, end in multiplier_ranges]
            random.shuffle(multipliers)

            # Prepare multiplier-to-label mapping once
            sorted_multipliers = sorted(multipliers)
            labels_by_rank = ["Boost", "Zoom", "Thrust", "Lift", "Jet", "Flyer"]
            multiplier_label_map = dict(zip(sorted_multipliers, labels_by_rank))

            # Build the game menu efficiently
            game_one_menu = ["CON Aviator - Chagua Ndege Yako :\n\n"]
            for i, multiplier in enumerate(multipliers):
                label = multiplier_label_map[multiplier]
                game_one_menu.append(f"{i+1}. x{multiplier} {label}\n")

            game_one_menu.append("\n00. Main Menu")
            
            # Join the menu list into a single string
            game_one_menu = ''.join(game_one_menu)

            # Batch the database update (game_number and multipliers)
            cur.execute("""
                UPDATE ussd_session 
                SET game_number = 1, multipliers = %s 
                WHERE session_id = %s
            """, (json.dumps(multipliers), session_id))
            
            # Commit the database updates in one go
            mysql.get_db().commit()

            # Prepare the response
            response = {
                "description": game_one_menu,
                "status": 1001
            }
            return response
        
        #Punter has selected Game 2 option on Main Menu. System displays Game 2 Menu
        elif txt_length == 1 and user_input == "2":
            # Update input string once at the beginning, reduce redundant commits
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", ("XXXX*2", session_id))
            
            # Commit only once after all updates for better performance
            # Game two mechanics starts here
            multiplier_ranges = [(50, 69), (70, 119), (120, 249), (260, 4999), (5000, 9999), (10000, 100000)]

            # Generate multipliers in one line using list comprehension and random.uniform
            multipliers = [round(random.uniform(start, end), 1) for start, end in multiplier_ranges]

            # Shuffle the multipliers once
            random.shuffle(multipliers)
            
            # Prepare multipliers for database update
            cur.execute("UPDATE ussd_session SET game_number = 2, multipliers = %s WHERE session_id = %s", 
                        (json.dumps(multipliers), session_id))

            mysql.get_db().commit()
            
            # Avoid sorting every time and directly use a sorted copy
            sorted_multipliers = sorted(multipliers)
            
            # Pre-define labels by rank, no change needed here
            labels_by_rank = ["Kikoba", "Uteo", "Kyondo", "Mfuko", "Sanduku", "Gunia"]

            # Create a dictionary mapping multiplier values to labels in one go
            multiplier_label_map = dict(zip(sorted_multipliers, labels_by_rank))

            # Prepare the game menu efficiently by building the string in one go
            game_two_menu = "CON Jaza na 40 - Chagua :\n\n" + "\n".join(
                [f"{i+1}. Ksh {multiplier} {multiplier_label_map[multiplier]}" for i, multiplier in enumerate(multipliers)]
            )
            
            # Append the main menu at the end of the string
            game_two_menu += "\n00. Main Menu"
            
            # Return the response with the generated game menu
            response = {"description": game_two_menu, "status": 1001}
            return response
        
        #Punter has selected 3 option on Main Menu. System displays Redeem Points 3 Menu
        elif txt_length == 1 and user_input == "0":
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", ("XXXX*0", session_id))
            mysql.get_db().commit()
            
            #select available points, insert into disbursement table.
            cur.execute("""SELECT balance FROM accumulated_points WHERE msisdn = %s""", (msisdn))
            points = cur.fetchone()
            if points is not None:
                points_balance = float(points['balance'])
            else:
                points_balance = 0
            
            # points_balance = 0 
            
            redeem_points = f"CON Your Balance is Ksh {points_balance}\n\n"
            
            redeem_points += "1. Withdraw. Min is Ksh 10\n"
            
            redeem_points += "\n00. Main Menu"
            
            response = {"description":redeem_points,
                        "status":1001}
            return response
        
        #Punter has selected any of the Boxes 1, 2, 3, 4, 5, 6, 7 options on Game 1 Menu.
        elif txt_length == 2 and int(inputs[1]) == 1 and int(user_input) in [1, 2, 3, 4, 5, 6, 7]:
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{user_input}", session_id))
            
            game_option = inputs[1]
            box_selected = user_input
            
            date_created = Localtime().gettime()
            status = 0
            cur.execute("""INSERT INTO game_one_staking (session_id, game_option, box_selected, mobile_number, date_created, status) VALUES (%s, %s, %s, %s, %s, %s)""", 
                                                        (session_id, game_option, box_selected,        msisdn, date_created, status))
            mysql.get_db().commit()
            
            game_one_payment_info = "END Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 20"
            
            response = {"description":game_one_payment_info,
                        "status":1002}
            return response
        
        #Punter has selected any of the Boxes 1, 2, 3, 4, 5, 6, 7 options on Game 2 Menu.
        elif txt_length == 2 and int(inputs[1]) == 2 and int(user_input) in [1, 2, 3, 4, 5, 6, 7]:
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{user_input}", session_id))
            #Send details to the game engine to initiate staking
            game_option = inputs[1]
            box_selected = user_input
            
            date_created = Localtime().gettime()
            status = 0
            cur.execute("""INSERT INTO game_two_staking (session_id, game_option, box_selected, mobile_number, date_created, status) VALUES (%s, %s, %s, %s, %s, %s)""", 
                                                        (session_id, game_option, box_selected,        msisdn, date_created, status))
            mysql.get_db().commit()
            
            game_two_payment_info = "END Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 40"
        
            response = {"description":game_two_payment_info,
                        "status":1002}
            return response
        
        
        #Punter has selected withdraw points
        elif txt_length == 2 and int(inputs[1]) == 0 and int(user_input) ==1:
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{user_input}", session_id))
            mysql.get_db().commit()
            #select available points, insert into disbursement table.
            cur.execute("""SELECT balance FROM accumulated_points WHERE msisdn = %s""", (msisdn))
            points = cur.fetchone()
            if points is not None:
                points_balance = float(points['balance'])
            else:
                points_balance = 0
            
            if points_balance >= 10:
                id = UniqueNumber().MpesaDisbursementRequestId()
                status = 0
                game_no = 0
                processed = 0
                
                first_char = 'z'
                random_chars = random.choices(string.ascii_lowercase, k=6)  # Start with 6 letters
                random_number = random.choice(string.digits)  # Choose one random number
                random_index = random.randint(0, 6)  # Random index for the number
                random_chars.insert(random_index, random_number)  # Insert number into the characters list
                ticket_number = first_char + ''.join(random_chars)
                date_created = Localtime().gettime()
            
                #deduct points before withdrawing
                cur.execute("""UPDATE accumulated_points SET balance = balance - %s WHERE msisdn = %s""",(points_balance, msisdn))
                
                cur.execute("""INSERT INTO mpesa_b2c_disbursement_requests(id, msisdn,         amount, game_no, ticket_number, status, processed, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                                          (id, msisdn, points_balance, game_no, ticket_number, status, processed, date_created))
                
                
                mysql.get_db().commit()
                
                redeem_points_info = "END You have redeemed your points successfully!"
            
            else:
                redeem_points_info = "END Minimum amount to withdraw is Ksh 10"
                
            response = {"description":redeem_points_info,
                        "status":1002}
            return response

        else:
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", ("XXXX", session_id))
            mysql.get_db().commit()
            
            response = {"description":main_menu_text,
                        "status":1000}
            return response
