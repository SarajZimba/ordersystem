from flask import  request, Blueprint
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file3 = Blueprint('app_file3',__name__)
from root.auth.check import token_auth


@app_file3.route("/itemstats", methods=["POST"])
@cross_origin()
def completed_items():
    try:
        json = request.get_json()
        if "token" not in json or "end_date" not in json or "start_date" not in json not in json or "outlet_name" not in json or not any([json["token"],json["end_date"],json["start_date"],json["outlet_name"]]) or json["start_date"]=="" or json["token"] =="" or json["end_date"]=="" or json["outlet_name"] =="":
            data = {"error":"Some fields missing."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400
        start_date = json["start_date"]
        end_date = json["end_date"]
        outlet_name = json["outlet_name"]
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        completedItem_category_sql= f"""SELECT sum(a.Quantity) as quantity, a.ItemName,a.category from tblorderTracker_Details a, tblorderTracker b where a.orderTrackerID = b.idtblorderTracker and b.Date BETWEEN %s and %s and b.outlet_Name =%s and not a.completedAt='' and not a.completedAt='void'  group by a.ItemName,a.category"""
        cursor.execute(completedItem_category_sql,(start_date,end_date,outlet_name,),)
        category_result = cursor.fetchall()
        if category_result==[]:
            completed_category_json_data={"error":"No data available for completed items."}
        else:
            row_headers=[x[0] for x in cursor.description] 
            completed_category_json_data={}
            for res in category_result:
                data=dict(zip(row_headers,res))
                category= data["category"]
                ItemName=data["ItemName"]
                quantity=data["quantity"]
                itemjson = {"ItemName":ItemName,"quantity":quantity}
                completed_category_json_data.setdefault(category,[]).append(itemjson)
            
        
        voidItem_category_sql= f"""SELECT sum(a.Quantity) as quantity, a.ItemName,a.category from tblorderTracker_Details a, tblorderTracker b where a.orderTrackerID = b.idtblorderTracker and b.Date BETWEEN %s and %s and b.outlet_Name =%s and not a.completedAt='' and a.completedAt='void'  group by a.ItemName,a.category"""
        cursor.execute(voidItem_category_sql,(start_date,end_date,outlet_name,),)
        voidcategory_result = cursor.fetchall()
        if voidcategory_result==[]:
            void_category_json_data={"error":"No data available for voided items."}
        else:
            row_headers=[x[0] for x in cursor.description] 
            void_category_json_data={}
            for res in voidcategory_result:
                voiddata=dict(zip(row_headers,res))
                voidcategory= voiddata["category"]
                voidItemName=voiddata["ItemName"]
                voidquantity=voiddata["quantity"]
                voiditemjson = {"ItemName":voidItemName,"quantity":voidquantity}
                void_category_json_data.setdefault(voidcategory,[]).append(voiditemjson)
        itemStatsjson={"Completed":completed_category_json_data,"Void":void_category_json_data}
        cursor.close()
        mydb.close() 
        return itemStatsjson,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

