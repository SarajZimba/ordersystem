from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
import re
from root.auth.check import token_auth

load_dotenv()

app_file55 = Blueprint('app_file55', __name__)

# Helper function to validate date format (YYYY-MM-DD)
def valid_date(datestring):
    try:
        regex = re.compile(r"^(\d{4})-(0[1-9]|1[0-2]|[1-9])-(0[1-9]|[1-2]\d|3[0-1])$")
        match = re.match(regex, datestring)
        return match is not None
    except ValueError:
        return False

from collections import defaultdict

@app_file55.route("/get_accumulation_redeemtionhistory", methods=["POST"])
@cross_origin()
def filter_points():
    try:
        # Parse JSON body
        json = request.get_json()
        if not json:
            return jsonify({"error": "No data provided."}), 400
        if "customer_name" not in json or "email" not in json:
            data = {"error":"Some fields are missing"}
            return data,400

        customer_name = json.get("customer_name", "").strip()  # Default to empty string if not provided
        email = json.get("email", "")
        if "token" not in json  or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400

        # Connect to the database
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(dictionary=True)

        # Base SQL query
        accumulation_base_query = """
            SELECT * 
            FROM tbldallePointsAccumulation
            WHERE Customer_Name = %s and Email = %s
        """

        # # Adjust query if customer_name is provided and not blank
        # if customer_name and customer_name != "":
        #     accumulation_base_query += " AND Customer_Name = %s"
        #     accumulation_params = (start_date, end_date, customer_name)
        # else:
        accumulation_params = (customer_name, email,)

        # Execute query
        cursor.execute(accumulation_base_query, accumulation_params)
        accumulation_results = cursor.fetchall()



        # Base SQL query with optional customer_name filtering
        redeemption_base_query = """
            SELECT 
                r.idtbldalleReedemption,
                r.Redeemption_Date,
                r.Outlet_Name,
                r.Customer_Name,
                r.Customer_ID,
                r.Email,
                r.Phone,
                r.Points_Total,
                r.Points_Redeemed,
                r.Points_Remaining,
                rd.Points_Redemed AS Detail_Points_Redeemed,
                rd.Quantity,
                rd.Item_Name,
                rd.Restaurant_Redeemable
            FROM tbldalleRedeemption r
            LEFT JOIN tbldalleRedeemption_details rd
            ON r.idtbldalleReedemption = rd.Redeemption_ID
            WHERE r.Customer_Name = %s AND r.Email = %s 
        """

        # redeemption_params = [start_date, end_date]

        # Execute query
        cursor.execute(redeemption_base_query, accumulation_params)
        redeemption_results = cursor.fetchall()

        # Close database connection
        cursor.close()
        mydb.close()


        transformed_data = []
        # Group results by Outlet_Name
        grouped_data = defaultdict(list)
        # for row in accumulation_results:
        #     grouped_data[row['Outlet_Name']].append(row)
        for row in accumulation_results:


            row['Date'] = row['Date'].strftime('%Y %m %d %I:%M %p')
            row['Points_Accumulated'] = float(row['Points_Accumulated'])
            row['Points_Balanced'] = float(row['Points_Balanced'])
            row['Points_Total'] = float(row['Points_Total'])
            grouped_data[row['Outlet_Name']].append(row)

        # Convert defaultdict to a regular dictionary for JSON serialization
        grouped_data = dict(grouped_data)

        for outlet_name, data in grouped_data.items():
            transformed_data.append({
                "Outlet_Name": outlet_name,
                "data": data
            })
        # Process results to group by Outlet_Name and consolidate redemption details


        outlet_data = {}
        for row in redeemption_results:
            outlet_name = row['Outlet_Name']
            redemption_id = row['idtbldalleReedemption']
            day_name = row['Redeemption_Date'].strftime('%A')
            # Initialize outlet if not already present
            if outlet_name not in outlet_data:
                outlet_data[outlet_name] = []

            # Check if this redemption already exists in the outlet's list
            existing_redemption = next((r for r in outlet_data[outlet_name] if r["idtbldalleReedemption"] == redemption_id), None)

            if not existing_redemption:
                # Create a new redemption entry
                redemption_entry = {
                        "idtbldalleReedemption": row["idtbldalleReedemption"],
                        "Redeemption_Date": row["Redeemption_Date"].strftime('%Y %m %d %I:%M %p'),
                        "Outlet_Name": row["Outlet_Name"],
                        "Customer_Name": row["Customer_Name"],
                        "Customer_ID": row["Customer_ID"],
                        "Email": row["Email"],
                        "Phone": row["Phone"],
                        "Points_Total": float(row["Points_Total"]),
                        "Points_Redeemed": float(row["Points_Redeemed"]),
                        "Points_Remaining": float(row["Points_Remaining"]),
                        "details": []
                    }
                outlet_data[outlet_name].append(redemption_entry)
            else:
                redemption_entry = existing_redemption

            # Add details if present
            if row["Detail_Points_Redeemed"] is not None:
                detail_entry = {
                        "Points_Redemed": float(row["Detail_Points_Redeemed"]),
                        "Quantity": row["Quantity"],
                        "Item_Name": row["Item_Name"],
                        "Restaurant_Redeemable": row["Restaurant_Redeemable"]
                    }
                redemption_entry["details"].append(detail_entry)

        # Transform the data into the required format
        formatted_redeemption_data = []
        for outlet_name, redemptions in outlet_data.items():
            formatted_redeemption_data.append({
                "Outlet_Name": outlet_name,
                "data": redemptions
            })

        # New format for graph_data just like in getredeemeditemsfromcustomer
        formatted_graph_data = []

        for outlet_name, redemptions in outlet_data.items():
            outlet_data_list = []  # To store flattened data for this outlet
            for redemption in redemptions:
                # Add redemption-level details as individual entries
                if redemption["details"]:
                    for detail in redemption["details"]:
                        outlet_data_list.append({
                                "Redeemption_Date": redemption["Redeemption_Date"],
                                "Outlet_Name": redemption["Outlet_Name"],
                                "Customer_Name": redemption["Customer_Name"],
                                "Customer_ID": redemption["Customer_ID"],
                                "Email": redemption["Email"],
                                "Phone": redemption["Phone"],
                                "Points_Total": redemption["Points_Total"],
                                # "Points_Redeemed": redemption["Points_Redeemed"],
                                "Points_Remaining": redemption["Points_Remaining"],
                                "Item_Name": detail["Item_Name"],
                                "Points_Redemed": detail["Points_Redemed"],
                                "Quantity": detail["Quantity"],
                                "Restaurant_Redeemable": detail["Restaurant_Redeemable"]
                        })
            if outlet_data_list != []:
                formatted_graph_data.append({
                    "Outlet_Name": outlet_name,
                    "data": outlet_data_list
                })

            # Initialize the result structure
        graph_data = []

        # Iterate through the formatted_redeemption_data
        for outlet in formatted_graph_data:
            outlet_name = outlet["Outlet_Name"]
            total_points_redeemed = 0
            item_summary = {}

                # Process the redemption data
            for redemption in outlet["data"]:
                    # Accumulate points redeemed if present
                if redemption["Points_Redemed"] is not None:
                    total_points_redeemed += redemption["Points_Redemed"]

                # Process item details
                item_name = redemption["Item_Name"]
                quantity = redemption["Quantity"]



                if item_name and quantity is not None:
                    # Aggregate quantity for each item
                    if item_name in item_summary:
                        item_summary[item_name] += quantity
                    else:
                        item_summary[item_name] = quantity

                # Build the outlet-level data
            graph_data.append({
                "Outlet_Name": outlet_name,
                "total_points_redeemed": total_points_redeemed,
                "data": [{"Item_Name": item, "Quantity": qty} for item, qty in item_summary.items()]
            })

        # Return the grouped results
        return jsonify({"accumulation": transformed_data, "redeemption":formatted_redeemption_data, "graph_data":graph_data}), 200

    except mysql.connector.Error as db_err:
        return jsonify({"error": f"Database error: {str(db_err)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
