from flask import  Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file25 = Blueprint('app_file25',__name__)
from root.auth.check import token_auth
from pytz import timezone
from datetime import datetime,date


@app_file25.route("/customerCreditInsert", methods=["POST"])
@cross_origin()
def CustomerCreditInsert():
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
        if  not "guestID" in json or json["guestID"]=="" or not "outlet" in json or json["outlet"]=="" or "Amount" not in json or json["Amount"]=="" or "PaymentMode" not in json or json["PaymentMode"]=="" or "CustomerName" not in json or json["CustomerName"]=="":
            data= {"error":"Missing parameters."}
            return data,400
        dateToday=date.fromtimestamp(datetime.now(timezone('Asia/Kathmandu')).timestamp())
        paymentAt=datetime.now(timezone('Asia/Kathmandu')).strftime('%I:%M:%S')
        get_customer_creditSql =f"""INSERT INTO  CreditHistory(`outetName`,`Date`, `Amount`, `PaymentMode`, `PaymentAt`, `customerName`,`guestID`,`creditState`) VALUES (%s,%s,%s,%s,%s,%s,%s,'Payment')"""
        cursor.execute(get_customer_creditSql,(json["outlet"],dateToday,json["Amount"],json["PaymentMode"],paymentAt,json["CustomerName"],json["guestID"],),)
        mydb.commit()
        mydb.close()
        data={"success":"Data posted successfully"}
        return data,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

