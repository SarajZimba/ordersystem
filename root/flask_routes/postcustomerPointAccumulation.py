from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
app_file48 = Blueprint('app_file48', __name__)

@app_file48.route("/postcustomerpointaccumulation", methods=["POST"])
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
        # Get the JSON payload
        data = request.get_json()
        print(data)
        # SQL query to insert into the table
        sql = """INSERT INTO tbldallePointsAccumulation 
                (Date, Outlet_Name, Customer_Name, Customer_ID, Email, Phone, Points_Total, Points_Accumulated, Points_Balanced, Bill_Total, Bill_ID, Outlet_Order_ID, Table_No)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        # Execute the query
        cursor.execute(
            sql,
            (
                datetime.strptime(data["Date"], "%Y-%m-%d %H:%M:%S"),
                data["Outlet_Name"],
                data["Customer_Name"],
                data["Customer_ID"],
                data["Email"],
                data["Phone"],
                data["Points_Total"],
                data["Points_Accumulated"],
                data["Points_Balanced"],
                data["Bill_Total"],
                data["Bill_ID"],
                data["Outlet_Order_ID"],
                data["Table_No"],
            ),
        )
        mydb.commit()

        # Retrieve the last inserted ID for reference
        inserted_id = cursor.lastrowid

        accumulationtracker_check_sql = """SELECT idtbldallePointsAccumulationTracker FROM tbldallePointsAccumulationTracker WHERE Customer_Name = %s AND Email = %s """


        cursor.execute(accumulationtracker_check_sql, (data["Customer_Name"], data["Email"],))
        existing_data_count = cursor.fetchone()

        if existing_data_count:
            update_tracker_sql = """UPDATE tbldallePointsAccumulationTracker 
                                     SET Points_Balanced = %s, LastUpdatedDate = %s 
                                     WHERE idtbldallePointsAccumulationTracker = %s"""
            
            cursor.execute(update_tracker_sql,
                           (data["Points_Balanced"],
                    datetime.strptime(data["Date"], "%Y-%m-%d %H:%M:%S"),
                    existing_data_count[0],) )
            mydb.commit()
        else:
            insert_tracker_sql = """ INSERT INTO tbldallePointsAccumulationTracker (LastUpdatedDate, Customer_Name, Customer_ID, Email, Phone, Points_Balanced) VALUES (%s, %s, %s, %s, %s, %s)"""

            cursor.execute(insert_tracker_sql, 
                           
                           (
                            datetime.strptime(data["Date"], "%Y-%m-%d %H:%M:%S"),
                            data["Customer_Name"],
                            data["Customer_ID"],
                            data["Email"],
                            data["Phone"],  
                            data["Points_Balanced"],
                           )
                           )
        mydb.commit()
        mydb.close()
        return {"success": "Points accumulation data saved successfully", "id": inserted_id}, 201

    except Exception as e:
        print({"error": str(e)})
        return {"error": str(e)}, 500