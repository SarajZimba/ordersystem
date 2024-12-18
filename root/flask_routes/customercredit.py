from flask import Flask, Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file24 = Blueprint('app_file24',__name__)
from root.auth.check import token_auth



@app_file24.route("/customerCredit", methods=["POST"])
@cross_origin()
def customerCredit():
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
        if not "outlet" in json:
            data= {"error":"Outlet Name not supplied."}
            return data,400
        get_customer_creditSql =f"""select distinct GuestName from tblorderhistory where GuestName!='' and PaymentMode='Credit' and Outlet_Name=%s"""
        cursor.execute(get_customer_creditSql,(json["outlet"],),)
        result = cursor.fetchall()
        if result == []:
            data = {"error":"Temporarily unavailable."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        json_data=[]
        for res in result:
            json_data.append(dict(zip(row_headers,res)))
        response_json = []
        for i in json_data:
            customer_Credit_json ={"name":i["GuestName"],"value":i["GuestName"]}
            response_json.append(customer_Credit_json)
        mydb.close()
        return response_json,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

