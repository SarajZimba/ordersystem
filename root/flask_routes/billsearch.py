from flask import Flask, Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file23= Blueprint('app_file23',__name__)
from root.auth.check import token_auth



@app_file23.route("/billsearch", methods=["POST"])
@cross_origin()
def billsearch():
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
        if "outlet" not in json or "billno" not in json:
            data = {"error":"Some fields are missing"}
            return data,400
        outlet = json["outlet"]
        billno = json["billno"]
        
        orderHistory =f"""SELECT Date,bill_no,(Total-serviceCharge-VAT) as 'Subtotal', Outlet_OrderID as id,serviceCharge, VAT,  Total, DiscountAmt, PaymentMode, GuestName FROM `tblorderhistory` where Outlet_Name =%s and  bill_no=%s """
        cursor.execute(orderHistory,(
            outlet,billno,
        ),)
        result = cursor.fetchall()
        if result == []:
            data = {"error":"No data available."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        json_data=[]
        for res in result:
            json_data.append(dict(zip(row_headers,res)))
        
        
        
        
        
        mydb.close()
        return json_data
    except Exception as error:
        data ={'error':str(error)}
        return data,400