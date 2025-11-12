from flask import request, jsonify, json, Response
from api.password.crypt_password import hash_password, unhash_password
from api.payload.payload import Localtime
from datetime import datetime, timedelta
from main import mysql, app
from api.logs.logger import ErrorLogger, UssdLogger
import os, random, string
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
        
        main_menu_text = "CON Select Active Bid\n\n"
        main_menu_text += f"1. TV LG 32\" (Ksh 30)\n"
        main_menu_text += f"2. Vivo Y19s (Ksh 40)\n"
        main_menu_text += f"3. Fridge Ramtons (Ksh 20)\n"
        main_menu_text += f"4. E-Nduthi (Ksh 60)\n"
        main_menu_text += f"5. 5k Shopping (Ksh 35)\n"
        main_menu_text += f"0. My Bids\n"
        
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
        
        # Participant dialed ussd 
        
        if (text == ""):
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", ("XXXX", session_id))
            mysql.get_db().commit()
            
            response = {"description":main_menu_text,
                        "status":1000}
            return response
        
        # Participant entered 00 to go back to Main Menu 
        elif user_input == '00':
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", ("XXXX", session_id))
            mysql.get_db().commit()
                    
            response = {"description":main_menu_text,
                        "status":1000}
            return response
        
        #Participant has selected Item 1 option on Main Menu. System displays Item 1 Auction
        elif txt_length == 1 and user_input == "1":
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{user_input}", session_id))
            
            item_option = 1
            # retail_price = 15000
            amount = float(30)
            
            date_created = Localtime().gettime()
            status = 0
            
            cur.execute("""SELECT id, end_date FROM item_one_auctions WHERE status = 1 AND item_id = 1""")
            get_auction_details = cur.fetchone()
            auction_id = get_auction_details['id']
            end_date = get_auction_details['end_date']
            biddingtime = self.get_remaining_time(end_date)
            
            
            #Generate ticket 
            first_char = 'm'
            random_chars = random.choices(string.ascii_lowercase, k=6)  
            random_number = random.choice(string.digits)  
            random_index = random.randint(0, 6) 
            random_chars.insert(random_index, random_number) 
            ticket_number = first_char + ''.join(random_chars)
                
            cur.execute("""INSERT INTO item_one_bids (session_id, item_option, auction_id, ticket_number, amount, mobile_number, date_created, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                     (session_id, item_option, auction_id, ticket_number, amount,        msisdn, date_created, status))
            mysql.get_db().commit()
            
            item_one_payment_info = f"END LG TV 32\" LED (15k)\nResults in {biddingtime}\nEnter MPESA PIN kulipa Ksh {int(amount)}"
            
            response = {"description":item_one_payment_info,
                        "status":1001}
            return response
        
        #Participant has selected Item 2 option on Main Menu. System displays Item 2 Auction
        elif txt_length == 1 and user_input == "2":
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{user_input}", session_id))
            
            item_option = 2
            # retail_price = 20000
            amount = float(40)
            
            date_created = Localtime().gettime()
            status = 0
            
            cur.execute("""SELECT id, end_date FROM item_two_auctions WHERE status = 1 AND item_id = 2""")
            get_auction_details = cur.fetchone()
            auction_id = get_auction_details['id']
            end_date = get_auction_details['end_date']
            biddingtime = self.get_remaining_time(end_date)
            
            
            #Generate ticket 
            first_char = 'n'
            random_chars = random.choices(string.ascii_lowercase, k=6)  
            random_number = random.choice(string.digits)  
            random_index = random.randint(0, 6) 
            random_chars.insert(random_index, random_number) 
            ticket_number = first_char + ''.join(random_chars)
                
            cur.execute("""INSERT INTO item_two_bids (session_id, item_option, auction_id, ticket_number, amount, mobile_number, date_created, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                     (session_id, item_option, auction_id, ticket_number, amount,        msisdn, date_created, status))
            mysql.get_db().commit()
            
            item_two_payment_info = f"END Vivo Y19s (20k)\nResults in {biddingtime}\nEnter MPESA PIN kulipa Ksh {int(amount)}"
            
            response = {"description":item_two_payment_info,
                        "status":1001}
            return response
        
        #Participant has selected Item 3 option on Main Menu. System displays Item 3 Auction
        elif txt_length == 1 and user_input == "3":
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{user_input}", session_id))
            
            item_option = 3
            # retail_price = 15000
            amount = float(20)
            
            date_created = Localtime().gettime()
            status = 0
            
            cur.execute("""SELECT id, end_date FROM item_three_auctions WHERE status = 1 AND item_id = 3""")
            get_auction_details = cur.fetchone()
            auction_id = get_auction_details['id']
            end_date = get_auction_details['end_date']
            biddingtime = self.get_remaining_time(end_date)
            
            
            #Generate ticket 
            first_char = 'p'
            random_chars = random.choices(string.ascii_lowercase, k=6)  
            random_number = random.choice(string.digits)  
            random_index = random.randint(0, 6) 
            random_chars.insert(random_index, random_number) 
            ticket_number = first_char + ''.join(random_chars)
                
            cur.execute("""INSERT INTO item_three_bids (session_id, item_option, auction_id, ticket_number, amount, mobile_number, date_created, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                     (session_id, item_option, auction_id, ticket_number, amount,        msisdn, date_created, status))
            mysql.get_db().commit()
            
            item_three_payment_info = f"END Fridge Ramtons 88L (15k)\nResults in {biddingtime}\nEnter MPESA PIN kulipa Ksh {int(amount)}"
            
            response = {"description":item_three_payment_info,
                        "status":1001}
            return response
        
        #Participant has selected Item 4 option on Main Menu. System displays Item 4 Auction
        elif txt_length == 1 and user_input == "4":
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{user_input}", session_id))
            
            item_option = 4
            # retail_price = 180000
            amount = float(60)
            
            date_created = Localtime().gettime()
            status = 0
            
            cur.execute("""SELECT id, end_date FROM item_four_auctions WHERE status = 1 AND item_id = 4""")
            get_auction_details = cur.fetchone()
            auction_id = get_auction_details['id']
            end_date = get_auction_details['end_date']
            biddingtime = self.get_remaining_time(end_date)
            
            
            #Generate ticket 
            first_char = 'q'
            random_chars = random.choices(string.ascii_lowercase, k=6)  
            random_number = random.choice(string.digits)  
            random_index = random.randint(0, 6) 
            random_chars.insert(random_index, random_number) 
            ticket_number = first_char + ''.join(random_chars)
                
            cur.execute("""INSERT INTO item_four_bids (session_id, item_option, auction_id, ticket_number, amount, mobile_number, date_created, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                      (session_id, item_option, auction_id, ticket_number, amount,        msisdn, date_created, status))
            mysql.get_db().commit()
            
            item_four_payment_info = f"END E-Nduthi (200k)\nResults in {biddingtime}\nEnter MPESA PIN kulipa Ksh {int(amount)}"
            
            response = {"description":item_four_payment_info,
                        "status":1001}
            return response
        
        #Participant has selected Item 5 option on Main Menu. System displays Item 5 Auction
        elif txt_length == 1 and user_input == "5":
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{user_input}", session_id))
            
            item_option = 5
            # retail_price = 5000
            amount = float(35)
            
            date_created = Localtime().gettime()
            status = 0
            
            cur.execute("""SELECT id, end_date FROM item_five_auctions WHERE status = 1 AND item_id = 5""")
            get_auction_details = cur.fetchone()
            auction_id = get_auction_details['id']
            end_date = get_auction_details['end_date']
            biddingtime = self.get_remaining_time(end_date)
            
            
            #Generate ticket 
            first_char = 'r'
            random_chars = random.choices(string.ascii_lowercase, k=6)  
            random_number = random.choice(string.digits)  
            random_index = random.randint(0, 6) 
            random_chars.insert(random_index, random_number) 
            ticket_number = first_char + ''.join(random_chars)
                
            cur.execute("""INSERT INTO item_five_bids (session_id, item_option, auction_id, ticket_number, amount, mobile_number, date_created, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", 
                                                      (session_id, item_option, auction_id, ticket_number, amount,        msisdn, date_created, status))
            mysql.get_db().commit()
            
            item_five_payment_info = f"END 5k Shopping\nResults in {biddingtime}\nEnter MPESA PIN kulipa Ksh {int(amount)}"
            
            response = {"description":item_five_payment_info,
                        "status":1001}
            return response
    
        #Participant has selected 0 option on Main Menu. System displays List of Bids Menu
        elif txt_length == 1 and user_input == "0":
            cur.execute("""UPDATE ussd_session SET input_string = %s WHERE session_id = %s""",("XXXX*0", session_id))
            mysql.get_db().commit()

            # Helper to fetch active auction id for a table
            def get_active_auction_id(table, item_id):
                cur.execute(f"""SELECT id FROM {table} WHERE status = 1 AND item_id = %s LIMIT 1""", (item_id,))
                r = cur.fetchone()
                return (r["id"] if r else None)

            # Helper to count user's bids for auction in last 13 hours
            def count_user_bids(auction_id, msisdn):
                if not auction_id:
                    return 0
                cur.execute("""SELECT COUNT(*) AS total_bids FROM mpesa_paybill_stk_responses WHERE auction_id = %s AND msisdn = %s AND created_at >= (NOW() - INTERVAL 13 HOUR)""",(auction_id, msisdn))
                row = cur.fetchone()
                return int(row["total_bids"]) if row and "total_bids" in row else 0

            # Map: (table_name, item_id, label)
            items = [
                ("item_one_auctions",   1, "SMART TV"),
                ("item_two_auctions",   2, "Phone"),
                ("item_three_auctions", 3, "Fridge"),
                ("item_four_auctions",  4, "E-Nduthi"),
                ("item_five_auctions",  5, "Shopping"),
            ]

            lines = []
            for idx, (table, item_id, label) in enumerate(items, start=1):
                auction_id = get_active_auction_id(table, item_id)
                bids_count = count_user_bids(auction_id, msisdn)
                # Show auction id only if you want it visible:
                # lines.append(f"{idx}. {label} (#{auction_id if auction_id else '-'}) – {bids_count} bids")
                lines.append(f"{idx}. {label} – {bids_count} bids")

            my_bids = "CON My Bids\n\n" + "\n".join(lines) + "\n\n00. Back"

            response = {"description": my_bids, "status": 1001}
            return response


    def get_remaining_time(self, end_datetime):
        local = Localtime()
        now_str = local.gettime()  # "YYYY-MM-DD HH:MM:SS"
        now = datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")

        if isinstance(end_datetime, str):
            end_datetime = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")

        remaining_mins = int((end_datetime - now).total_seconds() // 60)

        if remaining_mins <= 0:
            return "Auction closed"
        if remaining_mins < 60:
            return f"{remaining_mins} mins"
        hrs, mins = divmod(remaining_mins, 60)
        return f"{hrs} hrs {mins} mins" if mins else f"{hrs} hrs"