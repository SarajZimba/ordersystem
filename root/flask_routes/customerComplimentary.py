from flask import Flask, Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file20= Blueprint('app_file20',__name__)
from root.auth.check import token_auth




@app_file20.route("/complimentary", methods=["POST"])
@cross_origin()
def complimentary():
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
        if  "Outlet_Name" not in json or "uname" not in json or "start_date" not in json or "end_date" not in json:
            data = {"error":"Some fields are missing"}
            return data,400
        customer = json["uname"]
        startDate = json["start_date"]
        Outlet_Name = json["Outlet_Name"]
        endDate = json["end_date"]
        
        
        if customer =="":
            orderHistory =f"""SELECT Outlet_Name as Outlet,Date,GuestName as Customer,Total,PaymentMode as Mode FROM tblorderhistory WHERE  Date between %s and %s  and Outlet_Name=%s and (PaymentMode='Complimentary' or PaymentMode='Non Chargeable')  ORDER BY Date"""
            cursor.execute(orderHistory,(startDate,endDate,Outlet_Name,),)
            result = cursor.fetchall()
            if result == []:
                data = {"error":"No data available."}
                return data,400
            row_headers=[x[0] for x in cursor.description] 
            json_data=[]
            for res in result:
                json_data.append(dict(zip(row_headers,res)))
            sumSql = f"""SELECT SUM(Total) as Total FROM tblorderhistory WHERE  Date between %s and %s  and Outlet_Name=%s and (PaymentMode='Complimentary' or PaymentMode='Non Chargeable')"""
            cursor.execute(sumSql,(startDate,endDate,Outlet_Name),)
            sumresult = cursor.fetchall()
            if sumresult == []:
                data = {"error":"No data available."}
                return data,400
            row_headers=[x[0] for x in cursor.description] 
            sum_json_data=[]
            for res in sumresult:
                sum_json_data.append(dict(zip(row_headers,res)))
            data={}  
            data["Total"] = sum_json_data[0]["Total"]
            data["details"]=json_data
            mydb.close()
            return data,200
        

        orderHistory =f"""SELECT Outlet_Name as Outlet,Date,GuestName as Customer,Total,PaymentMode as Mode FROM tblorderhistory WHERE  Date between %s and %s and GuestName =%s and Outlet_Name=%s and (PaymentMode='Complimentary' or PaymentMode='Non Chargeable')  ORDER BY Date ASC"""
        cursor.execute(orderHistory,(startDate,endDate,customer,Outlet_Name,),)
        result = cursor.fetchall()
        if result == []:
            data = {"error":"No data available."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        json_data=[]
        for res in result:
            json_data.append(dict(zip(row_headers,res)))
        sumSql = f"""SELECT SUM(Total) as Total FROM tblorderhistory WHERE  Date between %s and %s and GuestName =%s and Outlet_Name=%s and (PaymentMode='Complimentary' or PaymentMode='Non Chargeable')"""
        cursor.execute(sumSql,(startDate,endDate,customer,Outlet_Name),)
        sumresult = cursor.fetchall()
        if sumresult == []:
            data = {"error":"No data available."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        sum_json_data=[]
        for res in sumresult:
            sum_json_data.append(dict(zip(row_headers,res)))
        data={}  
        data["Total"] = sum_json_data[0]["Total"]
        data["details"]=json_data
        
        
        
        mydb.close()
        return data,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400