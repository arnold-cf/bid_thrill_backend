
from flask import request, Response, jsonify
from main import mysql, app
from api.payload.payload import Localtime
from api.logs.logger import TelegramLogger, ErrorLogger
import requests, re, os
from telegram.constants import ParseMode
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)
from modules.game_module.game_controller import GameEngines

class Telegram():
 
    
    def app_response(self):
        details = request.get_json()
        
        #in production remove this logging code
        log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Telegram_Logs.json")
        with open(log_file, "a") as file:
            date = Localtime().gettime()
            file.write(f"\n{date}: {details}")
        
        
        if details == None:
            message = {'status':402,
                       'description':'Request data is missing some details!'}
            return jsonify(message)
       
        try:  
            
            #Establish database connection
            try:
                cur =  mysql.get_db().cursor()

            except mysql.get_db().Error as error:

                message = {
                        "status":500,
                        'error':'tel_002',
                        "description":"Couldn't connect to the Database!" + format(error)
                        }
                ErrorLogger().logError(message)
                return message
            
            # if details and "message" in details:
            if details and 'message' in details and 'callback_query' not in details and 'chat' in details['message']:
                # Processing the message (normal message without callback_query)
                message_id = details['message']['chat']['id']
                first_name = details['message']['from']['first_name']
                user_id = details['message']['from']['id']
                message_content = details['message'].get('text', '')  # Safely handle missing 'text'

                # Check if 'username' exists in 'from' dictionary
                user_name = details['message']['from'].get('username', '')

                # Logging details (you can remove this part in production)
                this_details = {"The details": "These are chat details, they were received successfully"}
                log_file = os.path.join(app.config["UPLOAD_FOLDER"], "logs/Telegram_Logs.json")
                with open(log_file, "a") as file:
                    date = Localtime().gettime()
                    file.write(f"\n{date}: {this_details}")

            elif details and 'callback_query' in details and 'message' in details['callback_query']:
                # Processing the callback query (button press or interaction)
                message_id = details['callback_query']['message']['chat']['id']
                first_name = details['callback_query']['from']['first_name']
                user_id = details['callback_query']['from']['id']
                message_content = details['callback_query'].get('data', '')  # Safely handle missing 'data'

                # Check if 'username' exists in 'from' dictionary
                user_name = details['callback_query']['from'].get('username', '')

                # Logging details (you can remove this part in production)
                this_details = {"The details": "These are button details, they were received successfully"}
                log_file = os.path.join(app.config["UPLOAD_FOLDER"], "logs/Telegram_Logs.json")
                with open(log_file, "a") as file:
                    date = Localtime().gettime()
                    file.write(f"\n{date}: {this_details}")

            else:
                message_id = ''
                message_content = ''


            
            
            request_time = Localtime().getdate()
            
            
            main_menu = f"Shinda hadi 2.5 million\n\n"
            main_menu += f"1. Mega Box\n"
            main_menu += f"2. Lucky Roll\n"
            main_menu += f"3. Mega JackPot (2.5M)\n"
            main_menu += f"4. Lucky Strike\n"
            main_menu += f"5. Daily Draw\n"
            main_menu += f"6. Gold Hunt\n"
            main_menu += f"7. Help\n"
            
            game_one_menu = "CON Chagua Box\n\n"
            game_one_menu += "1. Mega Box 1\n"
            game_one_menu += "2. Mega Box 2\n"
            game_one_menu += "3. Mega Box 3\n"
            game_one_menu += "4. Mega Box 4\n"
            game_one_menu += "5. Mega Box 5\n"
            game_one_menu += "6. Mega Box 6\n"
            game_one_menu += "7. Mega Box 7\n"
            game_one_menu += "00. Main Menu\n"
            
            game_one_payment_info = "Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 20"
            
            roll_menu = f"Chagua Roll\n\n"
            roll_menu += "2. 2 ROLLS @45Ksh\n"
            roll_menu += "4. 4 ROLLS @90Ksh\n"
            roll_menu += "6. 6 ROLLS @140Ksh\n"
            roll_menu += "8. 8 ROLLS @380Ksh (BOOST X1.2)\n"
            roll_menu += "10. 10@ 500 (BOOST X1.5)\n"
            roll_menu += "00. Main Menu\n"
            roll_menu += "99. BACK\n"
            
            
            strike_menu = f"Chagua Box\n\n"
            strike_menu += "1. BOX 1\n"
            strike_menu += "2. BOX 2\n"
            strike_menu += "3. BOX 3\n"
            strike_menu += "4. BOX 4\n"
            strike_menu += "5  BOX 5\n"
            strike_menu += "6. BOX 6\n"
            strike_menu += "7. BOX 7\n"
            strike_menu += "8. BOX 8\n"
            strike_menu += "00. Main Menu\n"
            strike_menu += "99. BACK\n"
            
            jackpot_menu = f"Chomoka na 2,500,000\n\n"
            jackpot_menu += "1. MEGA JACKPOT 1\n"
            jackpot_menu += "2. MEGA JACKPOT 2\n" 
            jackpot_menu += "3. MEGA JACKPOT 3\n" 
            jackpot_menu += "4. MEGA JACKPOT 4\n" 
            jackpot_menu += "5. MEGA JACKPOT 5\n" 
            jackpot_menu += "6. MEGA JACKPOT 6\n" 
            jackpot_menu += "7. MEGA JACKPOT 7\n" 
            jackpot_menu += "00. Main Menu\n"
            jackpot_menu += "99. BACK\n"
            
                        
            try:
                cur.execute("""SELECT input_string FROM telegram_session WHERE session_id= %s """, (message_id))
                get_inputs = cur.fetchone()
                if get_inputs:
                    user_inputs = get_inputs["input_string"]
                    if user_inputs is not None and user_inputs != '':
                        inputs = user_inputs.split("*")
                        txt_length = len(inputs)    
                        
                        last_element = inputs[-1] if txt_length > 0 else ''
                        txt_length_empty = 0                    
                    else:
                        txt_length = 0
                        user_inputs = ''
                        last_element = ''
                        txt_length_empty = 0
                else:
                    txt_length = 0
                    user_inputs = ''
                    last_element = ''
                    txt_length_empty = 1
            
            except Exception as error:
                txt_length = 0
                txt_length_empty = 1
                user_inputs = ''
          
            if ((txt_length_empty == 1 and (message_content.lower() == "hi")) or  (txt_length_empty == 1 and (message_content.lower() == "hello")) or  (txt_length_empty == 1 and (message_content.lower() == "/start"))):
               
                cur.execute("""INSERT IGNORE INTO telegram_session (session_id, msisdn, request_time) VALUES (%s, %s, %s)""", (message_id, first_name, request_time))
                mysql.get_db().commit()
                
                rowcount = cur.rowcount
                if rowcount:
                    platform = 'telegram'
                    status = 1
                
                  
                else:
                    cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", ("", message_id))
                    mysql.get_db().commit()
                
                self.send_main_menu(message_id)
                # Telegram.tel_send_message(message_id, main_menu, parse_mode = "Markdown")
                # return Response(main_menu, status=200)
                
            elif ((txt_length_empty == 0 and (message_content.lower() == "hi")) or  (txt_length_empty == 0 and (message_content.lower() == "hello")) or  (txt_length_empty == 0 and (message_content.lower() == "/start"))):
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", ("", message_id))
                mysql.get_db().commit()
                
                self.send_main_menu(message_id)
                # Telegram.tel_send_message(message_id, main_menu, parse_mode = "Markdown")
                # return Response(main_menu, status=200)
                
            #On the main menu, punter selected Option 1 which is Game 1. Mega Box
            elif ((txt_length == 0 and message_content == "110001" and txt_length_empty ==0) or (txt_length == 0 and message_content == "1" and txt_length_empty ==0)):
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", ("main_menu*110001", message_id))
                mysql.get_db().commit()
                
                self.send_game_one_menu(message_id)
                
                # start_conversation = game_one_menu
            
                # Telegram.tel_send_message(message_id, start_conversation, parse_mode = "Markdown")
                # return Response(start_conversation, status=200)
            
            #On the main menu, punter selected Option 2 which is Game 2. Lucky Roll
            elif ((txt_length == 0 and message_content == "110002" and txt_length_empty ==0) or (txt_length == 0 and message_content == "2" and txt_length_empty ==0)):
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", ("main_menu*110002", message_id))
                mysql.get_db().commit()
                
                start_conversation = roll_menu
            
                Telegram.tel_send_message(message_id, start_conversation, parse_mode = "Markdown")
                # return Response(start_conversation, status=200)
                
            
            #On the main menu, punter selected Option 3 which is Game 3. Mega JackPot
            elif ((txt_length == 0 and message_content == "110003" and txt_length_empty ==0) or (txt_length == 0 and message_content == "3" and txt_length_empty ==0)):
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", ("main_menu*110003", message_id))
                mysql.get_db().commit()
                
                start_conversation = jackpot_menu
            
                Telegram.tel_send_message(message_id, start_conversation, parse_mode = "Markdown")
                # return Response(start_conversation, status=200)
            
            #On the main menu, punter selected Option 4 which is Game 4. Lucky Strike
            elif ((txt_length == 0 and message_content == "110004" and txt_length_empty ==0) or (txt_length == 0 and message_content == "4" and txt_length_empty ==0)):
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", ("main_menu*110004", message_id))
                mysql.get_db().commit()
                
                start_conversation = 'Enter 6 Numbers from 0-39 *separated by comma or space*'
            
                # Telegram.tel_send_message(message_id, start_conversation, parse_mode = "Markdown")
                return Response(start_conversation, status=200)
            
            #####
            ##### THIS IS THE MEGA BOX MENU SELECTIONS
            #####
            #On the main menu, punter selected Option 1 which is Game 1. Mega Box
            #On the Mega Box menu, Punter selected Option 1
            
            elif (((txt_length == 2) and (str(user_inputs.lower()) == 'main_menu*110001') and int(message_content) in [112001, 112002, 112003, 112004, 112005, 112006, 112007]) or ((txt_length == 2) and (str(user_inputs.lower()) == 'main_menu*110001') and int(message_content) in [1, 2, 3, 4, 5, 6, 7])): 
                
                pay_request_command = '/pay'
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{message_content}*{pay_request_command}", message_id))
                mysql.get_db().commit()
                
                start_conversation = "Enter MPESA Number To Pay"
                reply_markup = ''
                
                
                # main_menu_text = "Select one of the games below:\n\n"

                # # Send the message with the menu buttons
                # Telegram.tel_send_message(chat_id, main_menu_text, reply_markup)
            
                Telegram.tel_send_message(message_id, start_conversation, reply_markup)
                # return Response(start_conversation, status=200)
            
            elif ((txt_length == 4) and (str(inputs[3]) == '/pay')): 
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{message_content}", message_id))
                mysql.get_db().commit()
                
                mobile_number = message_content
                game_option = inputs[1]
                box_selected = inputs[2]
                
                mobileNumber = ''.join(mobile_number.split())   
                msisdn = '254' + mobileNumber[-9:]
        
                #Initiate Mpesa STK
                params = {"game_option":game_option,
                          "box_selected":box_selected,
                          "mobile_number":msisdn,
                          "session_id":message_id
                      }
            
                GameEngines().game_one(params)
                
                start_conversation = "Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 20"
                reply_markup = ''
            
                Telegram.tel_send_message(message_id, start_conversation, reply_markup)
                # return Response(start_conversation, status=200)
            
            #####
            ##### THIS IS THE LUCY ROLL MENU SELECTIONS
            #####
            #On the main menu, punter selected Option 2 which is Game 2. Lucky Roll
            #On the Lucky Roll menu, Punter selected Option 2 -> ROLLS @45Ksh
            elif txt_length == 2 and message_content == "2" and str(user_inputs.lower()) == 'main_menu*2':
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{message_content}", message_id))
                mysql.get_db().commit()
                
                #Send details to Game Engine for Lucky Roll, Option 2.
                #Initiate Mpesa Payment
                
                start_conversation = "Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 20"
            
                Telegram.tel_send_message(message_id, start_conversation, parse_mode = "Markdown")
                # return Response(start_conversation, status=200)
            
            #On the main menu, punter selected Option 2 which is Game 2. Lucky Roll
            #On the Lucky Roll menu, Punter selected Option 4 -> ROLLS @90Ksh
            elif txt_length == 2 and message_content == "4" and str(user_inputs.lower()) == 'main_menu*2':
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{message_content}", message_id))
                mysql.get_db().commit()
                
                #Send details to Game Engine for Lucky Roll, Option 4.
                #Initiate Mpesa Payment
                
                start_conversation = "Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 20"
            
                Telegram.tel_send_message(message_id, start_conversation, parse_mode = "Markdown")
                # return Response(start_conversation, status=200)
            
            #On the main menu, punter selected Option 2 which is Game 2. Lucky Roll
            #On the Lucky Roll menu, Punter selected Option 6 -> ROLLS @140Ksh
            elif txt_length == 2 and message_content == "6" and str(user_inputs.lower()) == 'main_menu*2':
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{message_content}", message_id))
                mysql.get_db().commit()
                
                #Send details to Game Engine for Lucky Roll, Option 8.
                #Initiate Mpesa Payment
                
                start_conversation = "Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 20"
            
                Telegram.tel_send_message(message_id, start_conversation, parse_mode = "Markdown")
                # return Response(start_conversation, status=200)
            
            
            #On the main menu, punter selected Option 2 which is Game 2. Lucky Roll
            #On the Lucky Roll menu, Punter selected Option 8 -> ROLLS @380Ksh (BOOST X1.2)
            elif txt_length == 2 and message_content == "8" and str(user_inputs.lower()) == 'main_menu*2':
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{message_content}", message_id))
                mysql.get_db().commit()
                
                #Send details to Game Engine for Lucky Roll, Option 8.
                #Initiate Mpesa Payment
                
                start_conversation = "Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 20"
            
                Telegram.tel_send_message(message_id, start_conversation, parse_mode = "Markdown")
                # return Response(start_conversation, status=200)
            
            #On the main menu, punter selected Option 2 which is Game 2. Lucky Roll
            #On the Lucky Roll menu, Punter selected Option 10 -> 500 (BOOST X1.5)
            elif txt_length == 2 and message_content == "10" and str(user_inputs.lower()) == 'main_menu*2':
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{message_content}", message_id))
                mysql.get_db().commit()
                
                #Send details to Game Engine for Lucky Roll, Option 10.
                #Initiate Mpesa Payment
                
                start_conversation = "Utapata request ya kuweka MPESA PIN yako kukamilisha BET ya Ksh 20"
            
                Telegram.tel_send_message(message_id, start_conversation, parse_mode = "Markdown")
                # return Response(start_conversation, status=200)
        
            
            elif ((str(message_content.lower()) =='/pay') or (txt_length == 0 and message_content =="2" and txt_length_empty ==0)):
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", ("/pay", message_id))
                mysql.get_db().commit()
                
                payment_request = f"Enter Mpesa Number to receive payment request.\n"
            
                Telegram.tel_send_message(message_id, payment_request, parse_mode = "Markdown")
                # return Response(payment_request, status=200)
                
            elif str(user_inputs.lower()) =='/pay' and message_content != "":
                
                ##check if a mobile number was provided 
                mobilenumber = ''.join(message_content.split()) 
                mobilenumber = mobilenumber[-9:] 
                if re.match("^[0-9]*$", mobilenumber):
                    
                    this_last_element = 'hkt1m0c'
                    cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{mobilenumber}*{this_last_element}", message_id))
                    mysql.get_db().commit()
                            
                    transactionstatus_initiated = f"Enter amount. Minumum is kshs 20\n"    
                    Telegram.tel_send_message(message_id,transactionstatus_initiated, parse_mode = "Markdown")
                    # return Response(transactionstatus_initiated, status=200)
                
                else:
                    transactionstatus_initiated = f"Your input is not correct!\n\n"
                    transactionstatus_initiated += f"Enter Mpesa Number to receive payment request.\n"
                    Telegram.tel_send_message(message_id,transactionstatus_initiated, parse_mode = "Markdown")
                    # return Response(transactionstatus_initiated, status=200)
                    
            
            elif ((str(message_content.lower()) =='/balance') or (txt_length == 0 and message_content == "3" and txt_length_empty ==0)):
                
                cur.execute("""SELECT account_balance FROM tokens_count WHERE customer_account = %s """, (user_id))
                fetch_balance = cur.fetchone()
                if fetch_balance:
                    balance = float(fetch_balance["account_balance"])
                else:
                    balance = 0
                
                check_balance = f"Your account balance is Ksh {balance:,.2f}\n\n"
                check_balance += f"Top up to access Elite AI Tools\n\n"
                check_balance += f"Type _/pay_ to initiate a payment.\n"
            
                Telegram.tel_send_message(message_id, check_balance, parse_mode = "Markdown")
                # return Response(check_balance, status=200)
                                
            elif txt_length == 3 and last_element =='hkt1m0c' and message_content != "":
                
                ##check if a amount provided is correct
                if re.match("^[0-9]*$", message_content):
                    amount = float(message_content) 
                    
                    if amount > 19:
                    
                        cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", (f"{user_inputs}*{message_content}", message_id))
                        mysql.get_db().commit()
                                    
                        #initiate mpesa stk push
                        mobilenumber = inputs[1]
                        details = {"mobile_number":mobilenumber, "amount":amount, "user_id":user_id}
                    
                        # Mpesa().mpesa_paybill_stk(details)
                    
                        help_line = '+254 7xx xxx xxx'
                        transactionstatus_initiated = f"You will receive a payment request to pay with Mpesa. Make the payment to unlock advanced features!\n\n"
                        transactionstatus_initiated += f"If you need help, call {help_line}\n"
                        Telegram.tel_send_message(message_id,transactionstatus_initiated, parse_mode = "Markdown")
                        # return Response(transactionstatus_initiated, status=200)
                        
                    else:
                        transactionstatus_initiated = f"Enter amount. Minumum is kshs 20\n" 
                        Telegram.tel_send_message(message_id, transactionstatus_initiated, parse_mode = "Markdown")
                        # return Response(transactionstatus_initiated, status=200)
                    
                else:
                    transactionstatus_initiated = f"Your input is not correct!\n\n"
                    transactionstatus_initiated += f"Enter amount. Minumum is kshs 20\n" 
                    Telegram.tel_send_message(message_id, transactionstatus_initiated, parse_mode = "Markdown")
                    # return Response(transactionstatus_initiated, status=200)
                                
            elif ((message_content.lower() =='/help') or (txt_length == 0 and message_content == "4" and txt_length_empty ==0)):
                
                cur.execute("""UPDATE telegram_session SET input_string = %s WHERE session_id = %s""", ("/help", message_id))
                mysql.get_db().commit()
                
                help = "*Lao Games Help Guide*\n\n"
                help += "Welcome to *Lao Games* help guide! This guide will help you understand how to play the games effectively and safely.\n\n"
                help += "*How to Play Lao Games*\n\n"
                help += "1. *To Get Started*\n"
                help += "   - Type _/start_ to get started\n\n"

                help += "2. *To Display Main Menu*\n"
                help += "   - Type *hi* to see the main menu options\n\n"



                help += "4. *To Make a Payment*\n"
                help += "   - Type _/pay_ to initiate a payment\n"
                help += "   - From the Main Menu, type *2*\n\n"

                help += "5. *To Check Account Balance*\n"
                help += "   - Type _/balance_ to check your account balance.\n"
                help += "   - From the Main Menu, type *3*\n\n"

                help += "6. *To Get Help*\n"
                help += "   - Type _/help_ for assistance\n"
                help += "   - From the Main Menu, type *4*\n\n"

                help += "7. *To Talk to Us*\n"
                help += "   - Call +254 7xx xxx xxx for direct assistance\n\n"
            
                Telegram.tel_send_message(message_id, help, parse_mode = "Markdown")
                # return Response(help, status=200)
                
                                          
            else:
                return Response(main_menu, status=200)
                
                    
            return Response('ok', status=200)
    
            # return jsonify(details)  
        #Error handling
        except Exception as error:         
            message = {'status':501,
                       'error':'tel_003',
                       'description':'Failed to execute Error description ' + format(error)}            
            ErrorLogger().logError(message)
            return jsonify(message)  
        finally:
                cur.close()
    
    def send_main_menu(self, chat_id):
        """Send the main menu with inline buttons."""
        # Define inline buttons for the main menu
        main_menu_options = [
            [InlineKeyboardButton('1. Mega Box', callback_data='110001')],
            [InlineKeyboardButton('2. Lucky Roll', callback_data='110002')],
            [InlineKeyboardButton('3. Mega JackPot (2.5M)', callback_data='110003')],
            [InlineKeyboardButton('4. Lucky Strike', callback_data='110004')],
            [InlineKeyboardButton('5. Daily Draw', callback_data='110005')],
            [InlineKeyboardButton('6. Gold Hunt', callback_data='110006')],
            [InlineKeyboardButton('7. Help', callback_data='110007')]
        ]
        reply_markup = InlineKeyboardMarkup(main_menu_options)
        
        # Main menu text
        main_menu_text = "Select one of the games below:\n\n"

        # Send the message with the menu buttons
        Telegram.tel_send_message(chat_id, main_menu_text, reply_markup)
        
    def send_game_one_menu(self, chat_id):
        """Send the game one menu with inline buttons."""
        # Define inline buttons for the game one menu
            
        game_one_menu_options = [
            [InlineKeyboardButton('1. Mega Box 1', callback_data='112001')],
            [InlineKeyboardButton('2. Mega Box 2', callback_data='112002')],
            [InlineKeyboardButton('3. Mega Box 3', callback_data='112003')],
            [InlineKeyboardButton('4. Mega Box 4', callback_data='112004')],
            [InlineKeyboardButton('5. Mega Box 5', callback_data='112005')],
            [InlineKeyboardButton('6. Mega Box 6', callback_data='112006')],
            [InlineKeyboardButton('6. Mega Box 7', callback_data='112006')],
            [InlineKeyboardButton('00. Main Menu', callback_data='00')]
        ]
        reply_markup = InlineKeyboardMarkup(game_one_menu_options)
        
        # Game one menu text
        game_one_menu_text = "Select one of the box below:\n\n"

        # Send the message with the menu buttons
        Telegram.tel_send_message(chat_id, game_one_menu_text, reply_markup)
                
    def tel_send_message(chat_id, text, reply_markup=None):
        bot_token = app.config['TELEGRAM_TOKEN']
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        
        payload = {
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': 'Markdown'
                    }
    
        if reply_markup:
            payload['reply_markup'] = reply_markup.to_json()
            
        r = requests.post(url,json=payload)
        return r
    
    

    
   