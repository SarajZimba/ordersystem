from flask import Flask, Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file19= Blueprint('app_file19',__name__)
from root.auth.check import token_auth





@app_file19.route("/billinfo", methods=["POST"])
@cross_origin()
def billinfo():
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
        if "Outlet_Name" not in json or "bill_no" not in json or "Date" not in json:
            data = {"error":"Some fields are missing"}
            return data,400
        outletName = json["Outlet_Name"]
        BillNo = json["bill_no"]
        Date = json["Date"]
        billdetailsSql =f"""SELECT bill_no, employee, Table_No,Start_Time,End_Time,Type,Date,serviceCharge,vat,total,PaymentMode FROM `tblorderhistory` WHERE Outlet_Name=%s and bill_no=%s and Date =%s"""
        cursor.execute(billdetailsSql,(outletName,BillNo,Date,),)
        result = cursor.fetchall()
        if result == []:
            data = {"error":"No data available."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        json_data=[]
        for res in result:
            json_data.append(dict(zip(row_headers,res)))
        billitemDetailsSql = f"""SELECT a.itemName, sum(a.count) as Quantity, a.itemrate, a.total,a.ItemType FROM tblorder_detailshistory a, tblorderhistory b  WHERE a.order_ID = b.idtblorderHistory and b.Outlet_Name=%s and b.bill_no =%s and b.Date=%s group by a.ItemName"""
        cursor.execute(billitemDetailsSql,(outletName,BillNo,Date,),)
        billitemresult = cursor.fetchall()
        if billitemresult == []:
            data = {"error":"No data available."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        billItemdata ={}
        for res in billitemresult:
            billItemdata.setdefault("Details",[]).append(dict(zip(row_headers,res)))
        json_data[0]["details"]=billItemdata["Details"]   
        
        billTotalQuantitySql =f"""SELECT a.itemName, sum(a.count) as Quantity FROM tblorder_detailshistory a, tblorderhistory b  WHERE a.order_ID = b.idtblorderHistory and b.Outlet_Name=%s and b.bill_no =%s and b.Date=%s"""
        cursor.execute(billTotalQuantitySql,(outletName,BillNo,Date,),)
        billTotalQuantityresult = cursor.fetchall()
        billTotalQuantitdata =[]
        for res in billTotalQuantityresult:
            billTotalQuantitdata.append(dict(zip(row_headers,res)))
        json_data[0]["TotalCount"]=billTotalQuantitdata[0]["Quantity"]
        mydb.close()
        return json_data[0],200
    except Exception as error:
        data ={'error':str(error)}
        return data,400