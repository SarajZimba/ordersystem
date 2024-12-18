from flask import  Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file16= Blueprint('app_file16',__name__)


@app_file16.route("/reqfilterfirst/", methods=["GET"])
@cross_origin()
def reqfilterfirst():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        time = request.args.get("firsttime", "")
        time2 = request.args.get("secondtime", "")
        outletname = request.args.get("outlet_name", "")
        outletname.replace('%20',' ')
        if time=="" or time2=="" or outletname =="":
            data={"eror":"Some fields are missing."}
            return data,400
        sql = f"""SELECT * FROM intbl_purchaserequisition WHERE ReceivedDate BETWEEN %s AND %s and Outlet_Name=%s ORDER BY IDIntbl_PurchaseRequisition DESC ;"""
        cursor.execute(sql,(time,time2,outletname),)
        desc = cursor.description
        data = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        data = {"purchaserequisition":data}
        mydb.close()
        return data,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

