from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
app_file54 = Blueprint('app_file54', __name__)
from root.auth.check import token_auth

@app_file54.route("/getcustomeraccumulationpoints", methods=["POST"])
@cross_origin()
    
def postcustomerPointsAccumulation():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')

        )
        cursor = mydb.cursor(buffered=True)
        json = request.get_json()
        if "token" not in json  or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400
        # SQL query to insert into the table
        sql = """SELECT * FROM tbldallePointsAccumulationTracker order by Points_Balanced DESC"""

        # Execute the query
        cursor.execute(
            sql
        )
        # Fetch all results
        results = cursor.fetchall()
        # Get column names
        column_names = [desc[0] for desc in cursor.description]
        # Convert results to a list of dictionaries and cast Points_Balanced to float
        data = []
        for row in results:
            row_dict = dict(zip(column_names, row))
            row_dict["Points_Balanced"] = float(row_dict["Points_Balanced"])  # Convert to float
            row_dict["LastUpdatedDate"] = row_dict["LastUpdatedDate"].strftime('%Y %m %d %I:%M %p')
            data.append(row_dict)

        # Close the database connection
        mydb.close()

        return {"data": data}, 200

    except Exception as e:
        return {"error": str(e)}, 500