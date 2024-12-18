from flask import  Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file17= Blueprint('app_file17',__name__)


@app_file17.route("/reqitemhistory/", methods=["GET"])
@cross_origin()
def reqfilterfirst():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        item_id =request.args.get("item_id", "")
        outletname = request.args.get("outlet_name", "")
        limit = request.args.get("limit", "")
        outletname.replace('%20',' ')
        if item_id=="" or limit=="" or outletname =="":
            data={"eror":"Some fields are missing."}
            return data,400
        if not limit.isdigit():
            data={"error":"Limit must be an integer"}
            return data,400
        sql = f"""select a.rate, a.UnitsOrdered, b.ReceivedDate from intbl_purchaserequisition_contract a, intbl_purchaserequisition b where a.PurchaseReqID = b.IDIntbl_PurchaseRequisition and a.ItemID =%s and b.Outlet_Name=%s order by a.PurchaseReqID desc limit %s;"""
        cursor.execute(sql,(item_id,outletname,int(limit),),)
        desc = cursor.description
        data = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        data = {"intbl_purchaserequisition_contract":data}
        mydb.close()
        return data,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

