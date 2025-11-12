
from flask import request, jsonify, json
import os, requests,math, pymysql
from api.logs.logger import ErrorLogger
from api.payload.payload import Localtime
from main import mysql, app

class SMS:
    def deliver_sms(self, details):
        try:

            mpesa_ref = details['mpesa_ref']
            amount = float(details['amount'])
            amount = math.ceil(amount)
            account_number = details['account_number']
                                        
            # Connect to db1 and insert transaction details
            try:
                cur = mysql.get_db().cursor()
            except pymysql.MySQLError as e:
                message = {'status': 500, 'description': "Couldn't connect to db1: " + str(e)}
                return jsonify(message)
            
            send_date = Localtime().gettime() 
            
            cur.execute("""SELECT c.mobile_number, d.first_name FROM customers AS c INNER JOIN customer_details AS d ON c.id = d.customer_id WHERE c.account = %s""",(account_number))
            entry = cur.fetchone()     
            if entry:
                phone_number = entry["mobile_number"] 
                first_name = entry["first_name"] 
            else:
                phone_number = ""
                first_name = ""
            
            mobileNumber = ''.join(phone_number.split())   
            msisdn = '254' + mobileNumber[-9:]  
            
            sms_content = f"Dear {first_name}, your payment of Ksh {amount:,.2f} has been received. Mpesa receipt number is {mpesa_ref}\n"
            sms_content += "Helpline: 0701 986 294"
            
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
        
            if json_res['ErrorCode'] == 0:
                status = 1
                
                cur.execute('''INSERT INTO sms_log (msisdn, message, created_at, status) VALUES (%s, %s, %s, %s)''',
                                                    (msisdn, content, send_date,  status))
                mysql.get_db().commit()
                record = cur.rowcount
                if not record:
                    response = {
                        'description': "SMS sending successful but could not be saved!",
                        'status': 201,
                        'error':'sp_a58',
                    }
                else:
                    response = {
                        'description': "SMS sending successful and saved!",
                        'status': 200
                    }
                return response                
                
            else: 
                status = 0
                
                cur.execute("""INSERT INTO sms_log (msisdn, message, created_at, status) VALUES (%s, %s, %s, %s)""", 
                                                   (msisdn, content, send_date,  status))
                mysql.get_db().commit()

                record = cur.rowcount
                response = {
                    'description': "SMS sending failed",
                    'status': 201,
                    'error':'sp_a56'
                }
                # log details 
                log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/sms_log.json")
                with open(log_file, "a") as file:
                    file.write(f"\n{send_date}: #{account_number} {response}")
                return response


        # Error handling
        except Exception as error:
            cur.close()
            message = {'status':501,
                       'error':'sp_a57',
                       'description':'Transaction had an error. Error description ' + format(error)}
            ErrorLogger().logError(message) 
            return message 
        finally:
            cur.close()
    
    def points_sms(self):
        
        details = request.get_json()
        
        status = details['status']
        if status == "1":
            pass
        else:
            message = {'status': 201, 
                        'description': "Failed"}
            return jsonify(message)
                                
        # Connect to db1 and insert transaction details
        try:
            cur = mysql.get_db().cursor()
        except pymysql.MySQLError as e:
            message = {'status': 500, 'description': "Couldn't connect to db1: " + str(e)}
            return jsonify(message)
        
        try:
            send_date = Localtime().gettime() 
            
            cur.execute("""SELECT msisdn, balance FROM accumulated_points WHERE balance > 0""")
            entries = cur.fetchall()     
            if entries:
                for entry in entries: 
                    msisdn = entry["msisdn"] 
                    balance = float(entry["balance"]) 
                
                    sms_content = "AVIATOR Signals Zimepick!\n\n"
                    sms_content += "DIAL *835*55#\n\n"
                    sms_content += "Changamka Ushinde Ksh 900,000\n\n"
                    sms_content += f"POINTS zako ni Ksh {balance:,.2f}"
                    
                    
                    
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
                
                    if json_res['ErrorCode'] == 0:
                        status = 1
                        
                        cur.execute('''INSERT INTO sms_log (mobile_number, sms_content, date_created, delivered_status) VALUES (%s, %s, %s, %s)''',
                                                                  (msisdn,     content,    send_date,           status))
                        mysql.get_db().commit()
                        
                    else: 
                        status = 0
                        
                        cur.execute("""INSERT INTO sms_log (mobile_number, sms_content, date_created, delivered_status) VALUES (%s, %s, %s, %s)""", 
                                                                  (msisdn,     content,    send_date,           status))
                        mysql.get_db().commit()

                        # record = cur.rowcount
                        
                        response = {
                            'description': "SMS sending failed",
                            'status': 201,
                        }
                        #Log details 
                        log_file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/sms_log.json")
                        with open(log_file, "a") as file:
                            file.write(f"\n{send_date}: #{msisdn} {response}")
                
                
                response = {
                    'description': "SMS sending successful and saved!",
                    'status': 200
                }
                return response 
                
            else:
                response = {
                        'description': "No record was found!",
                        'status': 201
                    }
                return response


        # Error handling
        except Exception as error:
            cur.close()
            message = {'status':501,
                       'description':'Transaction had an error. Error description ' + format(error)}
            ErrorLogger().logError(message) 
            return message 
        finally:
            cur.close()