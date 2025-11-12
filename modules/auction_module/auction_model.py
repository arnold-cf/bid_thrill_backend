from flask import request, jsonify, json, Response
from api.payload.payload import Localtime
from main import mysql, app
from api.logs.logger import ErrorLogger, UssdLogger
import random, requests
from api.alphanumeric.generate import UniqueNumber

class AuctionModel:
    
    def auction_item_one_engine(self, details):
        pass 
    
    def auction_item_two_engine(self, details):
        pass 
    
    def auction_item_three_engine(self, details):
        pass 
    
    def auction_item_four_engine(self, details):
        pass 
    
    def auction_item_five_engine(self, details):
        pass 
                 
    def auction_sms_engine(self, details):
        
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
        

            


        