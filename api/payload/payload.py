from flask import request, Response
import json
import os, time
import string, random, socket
from main import mysql, app
from datetime import datetime, timedelta


class Localtime:
    def gettime(self):

        try:
            os.environ["TZ"] = "Africa/Nairobi"  # set new timezone

            d2 = time.strftime("%Y-%m-%d %H:%M:%S")

            return d2

        except TypeError:
            return Response({"Error generating local time"}, status=501)

    def getdate(self):

        try:
            d2 = datetime.now()
            return d2

        except TypeError:
            return Response({"Error generating local time"}, status=501)


class DataEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)
