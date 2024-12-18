from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()

app_file41 = Blueprint('app_file41', __name__)
from root.auth.check import token_auth

@app_file41.route('/deleteuser', methods=['POST'])

@cross_origin()
def userslist():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json =request.get_json()
        print(json)
        if "token" not in json or not any([json["token"]]) or json["token"] == "" :
            data = {"error": "No token provided"}
            return data, 400 
        if not any([json["username"]]) or "username" not in json or json["username"] == "":
            data = {"error": "No username provided"}
            return data, 400
        token = json["token"]
        if not token_auth(token):
            data = {"error": "Invalid token"}
            return data, 400
        username = json["username"]

        getUserlist_query = """select * from EmployeeLogin where userName =%s"""
        cursor.execute(getUserlist_query, (username,))
        result = cursor.fetchall()
        if result == []:
            data = {"error":f"No user exists of {username} "}
            return data, 400
        getUserlist_query = """delete from EmployeeLogin where userName = %s"""
        cursor.execute(getUserlist_query, (username,) )
        mydb.commit()
        cursor.close()
        mydb.close()
        return {"data": "User deleted succesfully"}, 200
        
    except Exception as e:
        data = {'error': str(e)}

        return data, 400 