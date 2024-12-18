from flask import  Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file38 = Blueprint('app_file38',__name__)
import secrets


@app_file38.route("/register", methods=["POST"])
@cross_origin()
def login():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "username" not in json or "password" not in json or not any([json["username"],json["password"], json["type"]]) or json["username"] =="" or json["password"]=="" or json["type"] == "" or "type" not in json or json["type"] == "":
            data = {"error":"Some fields missing."}
            return data,400
        uname = json["username"]
        upass = json["password"]
        type = json["type"]
        # token = secrets.token_hex(16)
        token = "test"

        # Check if the username already exists
        check_user_sql = """SELECT COUNT(*) FROM EmployeeLogin WHERE userName = %s"""
        cursor.execute(check_user_sql, (uname,))
        user_exists = cursor.fetchone()[0]
        
        if user_exists > 0:
            return {"error": "Username already exists."}, 400

        get_outlet_sql =f"""insert into EmployeeLogin (userName, Password, type, token) Values (%s, %s, %s, %s)"""
        cursor.execute(get_outlet_sql,(uname,upass, type, token),)
        mydb.commit()
        mydb.close()
        return {"data":"user registered successfully"},200
            
    except Exception as error:
        data ={'error':str(error)}
        return data,400

