from flask import  Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file4 = Blueprint('app_file4',__name__)


@app_file4.route("/login", methods=["POST"])
@cross_origin()
def login():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "username" not in json or "password" not in json or not any([json["username"],json["password"]]) or json["username"] =="" or json["password"]=="":
            data = {"error":"Some fields missing."}
            return data,400
        uname = json["username"]
        upass = json["password"]
        get_outlet_sql =f"""select Token, type, userName from EmployeeLogin where userName=%s and Password=%s"""
        cursor.execute(get_outlet_sql,(uname,upass,),)
        result = cursor.fetchall()
        if result == []:
            data = {"error":"No data available."}
            return data,400
        type = result[0][1]
        print(type)
        if type == "agent":
            data = {"error":"Agent are not able to login to the portal"}
            return data,400
        token = {"token":str(result[0][0]), "userName": str(result[0][2])}
        mydb.close()
        return token,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

