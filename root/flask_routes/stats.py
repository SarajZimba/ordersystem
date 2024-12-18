from flask import  Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file5 = Blueprint('app_file5',__name__)
from root.auth.check import token_auth
import pytz
from datetime import datetime


@app_file5.route("/stats", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "token" not in json or "outlet" not in json  or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        outlet = json["outlet"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400  
        current = datetime.now(tz=pytz.timezone("Asia/Kathmandu")).strftime('%Y-%m-%d')
        cooking_sql =f"""select (select count(idtblorderTracker) from tblorderTracker where outlet_Name=%s  and currentState='Cooking')as cooking,(select count(idtblorderTracker) from tblorderTracker where outlet_Name=%s  and currentState='Started')as started ,(select count(idtblorderTracker) as cooking_no from tblorderTracker where outlet_Name=%s  and currentState='Completed' and Date=%s) as completedToday,(select SUM(a.Quantity) as count FROM `tblorderTracker_Details` a, tblorderTracker b where a.orderTrackerID = b.idtblorderTracker and not a.completedAt='' and not a.completedAt='void' and b.Date=%s and b.outlet_Name=%s) as itemsCompetedToday,(select count(idtblorderTracker_Details) as voidToday FROM `tblorderTracker_Details` a, tblorderTracker b where a.orderTrackerID = b.idtblorderTracker and not a.completedAt='' and a.completedAt='void' and b.Date=%s and b.outlet_Name=%s) as voidTotalToday"""
        cursor.execute(cooking_sql,(outlet,outlet,outlet,current,current,outlet,current,outlet,),)
        result = cursor.fetchall()
        if result == []:
            data = {"error":"No data available."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        json_data=[]
        for res in result:
            json_data.append(dict(zip(row_headers,res)))
        totalOrders = json_data[0]["completedToday"]+  json_data[0]["cooking"]+  json_data[0]["started"]
        json_data[0]["totalOrdersToday"]=totalOrders
        mydb.close()
        return json_data[0],200 
    except Exception as error:
        data ={'error':str(error)}
        return data,400

