from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
import re
from root.auth.check import token_auth

load_dotenv()

app_file50 = Blueprint('app_file50', __name__)

# Helper function to validate date format (YYYY-MM-DD)
def valid_date(datestring):
    try:
        regex = re.compile(r"^(\d{4})-(0[1-9]|1[0-2]|[1-9])-(0[1-9]|[1-2]\d|3[0-1])$")
        match = re.match(regex, datestring)
        return match is not None
    except ValueError:
        return False


@app_file50.route("/getredeemeditemsfromcustomer", methods=["POST"])
@cross_origin()
def filter_points():
    try:
        # Parse JSON body
        json = request.get_json()
        if not json:
            return jsonify({"error": "No data provided."}), 400
        if "day_of_week" not in json or "startDate" not in json or "endDate" not in json or not json["day_of_week"] or not json["startDate"] or not json["endDate"]:
            return jsonify({"error": "Some fields are missing"}), 400

        # Extract required fields
        start_date = json.get("startDate")
        end_date = json.get("endDate")
        customer_name = json.get("customer_name", "").strip()
        day_of_week = json["day_of_week"]
        item_name = json.get("item_name", None)

        if "token" not in json or not json["token"]:
            return jsonify({"error": "No token provided."}), 400
        token = json["token"]
        if not token_auth(token):
            return jsonify({"error": "Invalid token."}), 400

        # Validate dates
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

        # Base SQL query
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
            WHERE DATE(r.Redeemption_Date) BETWEEN %s AND %s
        """

        accumulation_params = [start_date, end_date]
        if customer_name:
            redeemption_base_query += " AND r.Customer_Name = %s"
            accumulation_params.append(customer_name)

        # Execute query
        cursor.execute(redeemption_base_query, accumulation_params)
        redeemption_results = cursor.fetchall()

        # Close database connection
        cursor.close()
        mydb.close()

        outlet_data = {}
        for row in redeemption_results:
            outlet_name = row['Outlet_Name']
            redemption_id = row['idtbldalleReedemption']
            day_name = row['Redeemption_Date'].strftime('%A')
            if day_name in day_of_week:
                if outlet_name not in outlet_data:
                    outlet_data[outlet_name] = []

                existing_redemption = next((r for r in outlet_data[outlet_name] if r["idtbldalleReedemption"] == redemption_id), None)

                if not existing_redemption:
                    redemption_entry = {
                        "idtbldalleReedemption": row["idtbldalleReedemption"],
                        "Redeemption_Date": row["Redeemption_Date"].strftime('%Y %m %d %I:%M %p'),
                        "Outlet_Name": row["Outlet_Name"],
                        "Customer_Name": row["Customer_Name"],
                        "Customer_ID": row["Customer_ID"],
                        "Email": row["Email"],
                        "Phone": row["Phone"],
                        "Points_Total": row["Points_Total"],
                        "Points_Redeemed": row["Points_Redeemed"],
                        "Points_Remaining": row["Points_Remaining"],
                        "details": []
                    }
                    outlet_data[outlet_name].append(redemption_entry)
                else:
                    redemption_entry = existing_redemption

                # Add details if present
                if row["Detail_Points_Redeemed"] is not None:
                    if item_name != "":
                        if row["Item_Name"] == item_name:
                            detail_entry = {
                                "Points_Redemed": row["Detail_Points_Redeemed"],
                                "Quantity": row["Quantity"],
                                "Item_Name": row["Item_Name"],
                                "Restaurant_Redeemable": row["Restaurant_Redeemable"]
                            }
                            redemption_entry["details"].append(detail_entry)
                    else:
                        detail_entry = {
                                "Points_Redemed": row["Detail_Points_Redeemed"],
                                "Quantity": row["Quantity"],
                                "Item_Name": row["Item_Name"],
                                "Restaurant_Redeemable": row["Restaurant_Redeemable"]
                            }
                        redemption_entry["details"].append(detail_entry)                        

        formatted_redeemption_data = []
        for outlet_name, redemptions in outlet_data.items():
            outlet_data_list = []
            for redemption in redemptions:
                if redemption["details"]:
                    for detail in redemption["details"]:
                        outlet_data_list.append({
                            "Redeemption_Date": redemption["Redeemption_Date"],
                            "Outlet_Name": redemption["Outlet_Name"],
                            "Customer_Name": redemption["Customer_Name"],
                            "Customer_ID": redemption["Customer_ID"],
                            "Email": redemption["Email"],
                            "Phone": redemption["Phone"],
                            "Points_Total": float(redemption["Points_Total"]),
                            "Points_Redeemed": float(redemption["Points_Redeemed"]),
                            "Points_Remaining": float(redemption["Points_Remaining"]),
                            "Item_Name": detail["Item_Name"],
                            "Points_Redemed": float(detail["Points_Redemed"]),
                            "Quantity": detail["Quantity"],
                            "Restaurant_Redeemable": detail["Restaurant_Redeemable"]
                        })
            if outlet_data_list:
                formatted_redeemption_data.append({
                    "Outlet_Name": outlet_name,
                    "data": outlet_data_list
                })

        graph_data = []
        for outlet in formatted_redeemption_data:
            outlet_name = outlet["Outlet_Name"]
            total_points_redeemed = 0
            item_summary = {}

            for redemption in outlet["data"]:
                total_points_redeemed += redemption["Points_Redemed"]
                item_name = redemption["Item_Name"]
                quantity = redemption["Quantity"]
                if item_name and quantity is not None:
                    item_summary[item_name] = item_summary.get(item_name, 0) + quantity

            graph_data.append({
                "Outlet_Name": outlet_name,
                "total_points_redeemed": total_points_redeemed,
                "data": [{"Item_Name": item, "Quantity": qty} for item, qty in item_summary.items()]
            })

        return jsonify({"accumulation": [], "redeemption": formatted_redeemption_data, "graph_data": graph_data}), 200

    except mysql.connector.Error as db_err:
        return jsonify({"error": f"Database error: {str(db_err)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
