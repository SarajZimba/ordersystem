from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()
app_file47 = Blueprint('app_file47', __name__)

@app_file47.route("/postredeemeditemsfromcustomer", methods=["POST"])
@cross_origin()
    
def stats():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(buffered=True)
        data = request.get_json()
        print(data)
        # Insert data into tbldalleRedeemption
        sql_redeemption = """INSERT INTO tbldalleRedeemption 
            (Redeemption_Date, Outlet_Name, Customer_Name, Customer_ID, Email, Phone, Points_Total, Points_Redeemed, Points_Remaining)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(
            sql_redeemption,
            (
                datetime.strptime(data['Redeemption_Date'], '%Y-%m-%d %H:%M:%S'),
                data["Outlet_Name"],
                data["Customer_Name"],
                data["Customer_ID"],
                data["Email"],
                data["Phone"],
                data["Points_Total"],
                data["Points_Redeemed"],
                data["Points_Remaining"],
            ),
        )
        mydb.commit()

        # Get the last inserted ID for Redeemption
        redeemption_id = cursor.lastrowid

        # Insert data into tbldalleRedeemption_details
        sql_redeemption_details = """INSERT INTO tbldalleRedeemption_details 
            (Redeemption_ID, Points_Redemed, Quantity, Item_Name, Restaurant_Redeemable)
            VALUES (%s, %s, %s, %s, %s)"""
        for item in data['details']:
            cursor.execute(
                sql_redeemption_details,
                (
                    redeemption_id,
                    item["Points_Redemed"],
                    item["Quantity"],
                    item["Item_Name"],
                    item["Restaurant_Redeemable"],
                ),
            )
        mydb.commit()

        accumulationtracker_check_sql = """SELECT idtbldallePointsAccumulationTracker FROM tbldallePointsAccumulationTracker WHERE Customer_Name = %s AND Email = %s """


        cursor.execute(accumulationtracker_check_sql, (data["Customer_Name"], data["Email"],))
        existing_data_count = cursor.fetchone()

        if existing_data_count:
            update_tracker_sql = """UPDATE tbldallePointsAccumulationTracker 
                                     SET Points_Balanced = %s, LastUpdatedDate = %s 
                                     WHERE idtbldallePointsAccumulationTracker = %s"""
            
            cursor.execute(update_tracker_sql,
                           (data["Points_Remaining"],
                    datetime.strptime(data["Redeemption_Date"], "%Y-%m-%d %H:%M:%S"),
                    existing_data_count[0],) )
            mydb.commit()
        else:
            insert_tracker_sql = """ INSERT INTO tbldallePointsAccumulationTracker (LastUpdatedDate, Customer_Name, Customer_ID, Email, Phone, Points_Balanced) VALUES (%s, %s, %s, %s, %s, %s)"""

            cursor.execute(insert_tracker_sql, 
                           
                           (
                            datetime.strptime(data["Redeemption_Date"], "%Y-%m-%d %H:%M:%S"),
                            data["Customer_Name"],
                            data["Customer_ID"],
                            data["Email"],
                            data["Phone"],  
                            data["Points_Remaining"],
                           )
                           )
        mydb.commit()

        mydb.close()
        return {"success": "Redeemption data saved successfully"}, 201

    except Exception as e:
        return {"error": str(e)}, 500
