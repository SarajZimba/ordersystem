from flask import Flask, Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file77= Blueprint('app_file77',__name__)
from root.auth.check import token_auth

@app_file77.route("/customer", methods=["POST"])
@cross_origin()
def add_customer():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)

        json_data = request.get_json()
        token = json_data.get("token")

        if not token or not token_auth(token):
            return {"error": "Invalid or missing token."}, 400

        # required_fields = ["name", "address", "dateofbirth", "qr_code"]
        # for field in required_fields:
        #     if field not in json_data or not json_data[field]:
        #         return {"error": f"Missing required field: {field}"}, 400

        name = json_data.get("name", None)
        address = json_data.get("address", None)
        dateofbirth = json_data.get("dateofbirth", None)
        qr_code = json_data.get("qr_code", None)

        # Insert customer record
        insert_query = "INSERT INTO customer (name, address, dateofbirth, qr_code) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (name, address, dateofbirth, qr_code))
        mydb.commit()

        mydb.close()
        return {"message": "Customer added successfully."}, 200

    except mysql.connector.Error as err:
        return {"error": f"MySQL error: {err}"}, 400

    except Exception as error:
        return {"error": str(error)}, 400

