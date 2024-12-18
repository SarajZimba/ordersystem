from flask import  Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file22 = Blueprint('app_file22',__name__)
from root.auth.check import token_auth



@app_file22.route("/years", methods=["POST"])
@cross_origin()
def outlets():
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
        if "outlet" not in json:
            data={"error":"Outlet Name not supplied."}
            return data,400
        outletName =json["outlet"]
        get_year_sql =f"""SELECT DISTINCT YEAR(Date) as YearStr FROM `tblorderhistory` WHERE Outlet_Name=%s GROUP BY Date"""
        cursor.execute(get_year_sql,(outletName,),)
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
            outlet_json ={"name":i["YearStr"],"value":i["YearStr"]}
            response_json.append(outlet_json)

        mydb.close()
        return response_json,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

