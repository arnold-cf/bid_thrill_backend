from flask import request, Response, json, jsonify
from api.logs.logger import ErrorLogger
import uuid

class UniqueNumber():
    
    def mpesaC2BPaybillRequestId(self):  #FS 
        try:   
            get_uuid_ = str(uuid.uuid4())
            get_uuid = get_uuid_.replace("-", "")
            get_uuid = str(get_uuid)
            this_id = 'FS' + str(get_uuid[-11:])
                    
            return this_id
        except Exception as error:
            message = {"status":501,
                       "description": f"Error generating mpesa paybill stk request id. Error description" + format(error)}
            ErrorLogger().logError(message)            
            return message
        
    
    def mpesaPaybillTransactionId(self):  #FC
        try:   
            get_uuid_ = str(uuid.uuid4())
            get_uuid = get_uuid_.replace("-", "")
            get_uuid = str(get_uuid)
            this_id = 'FC' + str(get_uuid[-11:])
                    
            return this_id
        except Exception as error:
            message = {"status":501,
                       "description": f"Error generating mpesa paybill transaction id. Error description" + format(error)}
            ErrorLogger().logError(message)            
            return message
        
    
    def MpesaDisbursementResponseId(self):  #MF
        try:   
            get_uuid_ = str(uuid.uuid4())
            get_uuid = get_uuid_.replace("-", "")
            get_uuid = str(get_uuid)
            this_id = 'MF' + str(get_uuid[-11:])
                    
            return this_id
        except Exception as error:
            message = {"status":501,
                       "description": f"Error generating mpesa disbursement response id. Error description" + format(error)}
            ErrorLogger().logError(message)            
            return message
        
    
    def MpesaDisbursementRequestId(self):  #MD
        try:   
            get_uuid_ = str(uuid.uuid4())
            get_uuid = get_uuid_.replace("-", "")
            get_uuid = str(get_uuid)
            this_id = 'MD' + str(get_uuid[-11:])
                    
            return this_id
        except Exception as error:
            message = {"status":501,
                       "description": f"Error generating mpesa disbursement request id. Error description" + format(error)}
            ErrorLogger().logError(message)            
            return message
   
    