from flask import  Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file15= Blueprint('app_file15',__name__)





@app_file15.route("/reqfilter/", methods=["GET"])
@cross_origin()
def reqfilter():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        time = request.args.get("time") or ""
        time2 = request.args.get("time2") or ""
        company_name = request.args.get("company_name") or ""
        if time=="" or time2=="" or company_name =="":
            data={"eror":"Some fields are missing."}
            return data,400
        sql = f"""SELECT * FROM intbl_purchaserequisition WHERE ReceivedDate BETWEEN %s AND %s and Company_Name like %s ORDER BY IDIntbl_PurchaseRequisition DESC ;"""
        cursor.execute(sql,(time,time2,"%" + company_name + "%"),)
        desc = cursor.description
        data = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        data = {"purchaserequisition":data}
        mydb.close()
        return data,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

