# 

from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
import re
from root.auth.check import token_auth

load_dotenv()

app_file51 = Blueprint('app_file51', __name__)

# Helper function to validate date format (YYYY-MM-DD)
def valid_date(datestring):
    try:
        regex = re.compile(r"^(\d{4})-(0[1-9]|1[0-2]|[1-9])-(0[1-9]|[1-2]\d|3[0-1])$")
        match = re.match(regex, datestring)
        return match is not None
    except ValueError:
        return False

from collections import defaultdict

@app_file51.route("/customer_accumulation", methods=["POST"])
@cross_origin()
def filter_points():
    try:
        # Parse JSON body
        json = request.get_json()
        if not json:
            return jsonify({"error": "No data provided."}), 400
        if "startDate" not in json or "endDate" not in json  or json["startDate"]=="" or json["endDate"] == "":
            data = {"error":"Some fields are missing"}
            return data,400
        # Extract required fields
        start_date = json.get("startDate")
        end_date = json.get("endDate")
        customer_name = json.get("customer_name", "").strip()  # Default to empty string if not provided

        if "token" not in json  or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400
        # Validate dates
        if not start_date or not end_date:
            return jsonify({"error": "startDate and endDate are required."}), 400
        if not valid_date(start_date) or not valid_date(end_date):
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Connect to the database
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True)

        # Fetch all distinct outlets
        get_outlet_sql = "SELECT DISTINCT Outlet FROM outetNames"
        cursor.execute(get_outlet_sql)
        all_outlets = [row['Outlet'] for row in cursor.fetchall()]

        # Base SQL query
        accumulation_base_query = """
            SELECT * 
            FROM tbldallePointsAccumulation
            WHERE DATE(Date) BETWEEN %s AND %s
        """



        # Adjust query if customer_name is provided and not blank
        if customer_name and customer_name != "":
            accumulation_base_query += " AND Customer_Name = %s"
            accumulation_params = (start_date, end_date, customer_name)
        else:
            accumulation_params = (start_date, end_date)

        # Execute query
        cursor.execute(accumulation_base_query, accumulation_params)
        accumulation_results = cursor.fetchall()

        redeemptionAccumulation_transformed_data = [] #This data is the accumulation part of the redeemptionAccumulatin api
        # Group results by Outlet_Name
        grouped_data = defaultdict(list)
        # for row in accumulation_results:
        #     grouped_data[row['Outlet_Name']].append(row)
        for row in accumulation_results:
            # day_name = row['Date'].strftime('%A')
            # if day_name in day_of_week:
            # row['Date'] = row['Date'].strftime('%Y %m %d %I:%M %p')
            grouped_data[row['Outlet_Name']].append(row)

        # Convert defaultdict to a regular dictionary for JSON serializa    tion
        grouped_data = dict(grouped_data)

        for outlet_name, data in grouped_data.items():
            redeemptionAccumulation_transformed_data.append({
                "Outlet_Name": outlet_name,
                "data": data
            })
        # Process results to group by Outlet_Name and consolidate redemption details

        # Close database connection
        cursor.close()
        mydb.close()


        transformed_data = transform_data(accumulation_results, start_date, end_date, all_outlets)
        return jsonify({"accumulation": transformed_data, "accumulationData": redeemptionAccumulation_transformed_data}), 200

    except mysql.connector.Error as db_err:
        return jsonify({"error": f"Database error: {str(db_err)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from collections import defaultdict
from datetime import datetime, timedelta

def transform_data(accumulation_results, start_date, end_date, all_outlets):
    grouped_data = defaultdict(list)

    # Group existing data by Outlet_Name
    for row in accumulation_results:
        grouped_data[row['Outlet_Name']].append(row)

    transformed_data = []
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    # Iterate over all outlets (ensuring every outlet is represented)
    for outlet_name in all_outlets:
        outlet_data = defaultdict(list)

        # If the outlet has data, organize it by date
        if outlet_name in grouped_data:
            for row in grouped_data[outlet_name]:
                date_str = row['Date'].strftime('%Y-%m-%d')
                outlet_data[date_str].append(row)

        # Initialize results for this outlet
        outlet_result = {
            "Outlet_Name": outlet_name,
            "total_count": 0,
            "total_points": 0.0,
            "data": []
        }

        # Iterate over the date range
        current_date = start_date_obj
        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y-%m-%d')

            # Fetch data for the current date or use default
            date_entries = outlet_data.get(date_str, [])
            daily_count = len(date_entries)
            daily_points = sum(float(entry["Points_Accumulated"]) for entry in date_entries)

            # Append daily data (default to zero if no entries exist)
            outlet_result["data"].append({
                "date": date_str,
                "count": daily_count,
                "points": daily_points
            })

            # Update outlet totals
            outlet_result["total_count"] += daily_count
            outlet_result["total_points"] += daily_points

            # Move to the next date
            current_date += timedelta(days=1)

        transformed_data.append(outlet_result)

    return transformed_data



