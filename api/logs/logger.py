from flask import request, Response, json
import os, time
from main import mysql, app
from datetime import datetime, timedelta
from api.payload.payload import Localtime


class ErrorLogger:
    def logError(self, x):
        x["datecreated"] = Localtime().gettime()
        x = str(x)
        file = os.path.join(
            app.config["UPLOAD_FOLDER"] + "/logs/Application_Errors.json"
        )
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as fo:
            fo.write(x)

        return Response({"Error logged successfully"}, status=200)


class UssdLogger:
    def log(self, x):
        x["datecreated"] = Localtime().gettime()
        x = str(x)
        file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/USSD_Requests.json")
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as fo:
            fo.write(x)

        return Response({"Request logged successfully"}, status=200)

class MpesaLogger:
    def log(self, x):
        x["datecreated"] = Localtime().gettime()
        x = str(x)
        file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Mpesa_Logs.json")
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as fo:
            fo.write(x)

        return Response({"Transaction logged successfully"}, status=200)
    

class TelegramLogger:
    def log(self, x):
        x["datecreated"] = Localtime().gettime()
        x = str(x)
        file = os.path.join(app.config["UPLOAD_FOLDER"] + "/logs/Telegram_Logs.json")
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as fo:
            fo.write(x)

        return Response({"Request logged successfully"}, status=200)
