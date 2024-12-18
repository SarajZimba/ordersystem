from flask import  Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file53 = Blueprint('app_file53',__name__)
from root.auth.check import token_auth
import pytz
from datetime import datetime
import re

def valid_date(datestring):
        try:
                regex = re.compile("^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
                match = re.match(regex, datestring)
                if match is not None:
                    return True
        except ValueError:
            return False
        return False

@app_file53.route("/customers-lists-accumulation", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "token" not in json  or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400

        query = """select distinct(Customer_Name) from tbldallePointsAccumulation t where t.Customer_Name != ''"""
        cursor.execute(query)
        results = cursor.fetchall()

        # Convert results into a list of dictionaries
        items_data = []
        for row in results:
            items_data.append(
                 row[0]
                )            
        return items_data, 200
    except Exception as error:
        data ={'error':str(error)}
        return data,400