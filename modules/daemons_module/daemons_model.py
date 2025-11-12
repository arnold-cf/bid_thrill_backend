from flask import request, Response, jsonify, json
from datetime import datetime, timedelta
from api.payload.payload import Localtime
from dateutil.relativedelta import relativedelta
from api.logs.logger import ErrorLogger
from main import mysql, app
import requests


class Daemons():
    
    def get_pending_responses(self):
        try:
            cur = mysql.get_db().cursor()
        except Exception:
            return jsonify({
                'status': 500,
                'description': "Couldn't connect to the Database!"
            }), 500

        #Try except block to handle execute task
        try:
            
            count = 0
            cur.execute("""SELECT id, ticket_number, box_selected FROM game_one WHERE paid = 0 AND fetched_success =0 AND fetched <=3 LIMIT 100""")
            entries = cur.fetchall() 
            if entries:
                for entry in entries:
                    id = entry["id"]                    
                    ticket_number = entry["ticket_number"]                    
                    box_selected = entry["box_selected"] 
                    
                    #updated fetched 
                    
                    account_number = 'Box' + str(box_selected) + str('(') + str(ticket_number) + str(')')
                    
                    #Update queued status
                    cur.execute("""UPDATE game_one set fetched = fetched + 1 WHERE id = %s""", (id))
                    mysql.get_db().commit()
                
                    url = "https://www.lunahypeprotocol.codefremics.com/api/v2/payg/gg_stk_find_response"
                    
                    payload = json.dumps({
                        "account_number":account_number
                        })
                    headers = {
                        'Content-Type': 'application/json'
                        }
        
                    response = requests.request("POST", url, headers=headers, data=payload)
                    count = count + 1              
                
                if count > 0:
                    message = {"status":200,
                               "description":"Unprocessed responses were fetched!"}

                    return message
                else:
                    message = {"status":201,
                               "description":"Unprocessed responses were not fetched!"}

                    return message
                    
            else:
                message = {"status":201,
                           "description":"Transaction was canceled! No record for unprocessed responses!"}
                return message

        except Exception as error:
            message = {"status":501,
                       "description":"Transaction execution failed. Error description" + format(error)}
            ErrorLogger().logError(message)
            
            return message
        finally:
            cur.close()
            
    