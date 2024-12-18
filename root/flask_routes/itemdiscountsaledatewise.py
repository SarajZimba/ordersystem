from flask import  Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file33 = Blueprint('app_file33',__name__)
from root.auth.check import token_auth
import pytz
from datetime import datetime
import re

def valid_date(datestring):
        try:
                regex = re.compile("^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$")
                match = re.match(regex, datestring)
                if match is not None:
                    return True
        except ValueError:
            return False
        return False

@app_file33.route("/itemdatewisediscountedsales", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "token" not in json  or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400
        if "dateStart" not in json or "dateEnd" not in json or "type" not in json or "itemName" not in json or "day_of_week" not in json:
            data = {"error":"Some fields are missing"}
            return data,400
        start_Date = json["dateStart"]
        end_Date = json["dateEnd"]
        order_type = json["type"]
        itemName = json["itemName"]
        day_of_week = json["day_of_week"]
        if not valid_date(start_Date) or not valid_date(end_Date):
            data={"error":"Invalid date supplied."}
            return data,400
        

        query = '''select b.date, sum(a.count) , b.Outlet_Name, b.`Type`, b.Discounts , b.DiscountAmt  from tblorder_detailshistory a, tblorderhistory b where a.order_ID = b.idtblorderHistory and b.date between %s and %s and a.ItemName = %s and b.Discounts != "None" group by b.date,  b.Outlet_Name order by b.Outlet_Name, b.date'''
        cursor.execute(query, (start_Date, end_Date, itemName))
        results = cursor.fetchall()

        # Convert results into a list of dictionaries
        sales_data = []
        outlet_sales_set = set()  # To track outlets with data
        if order_type == "All":
            for row in results:
            #     sales_data.append({
            #         "date": row[0],
            #         "count": int(row[1]),
            #         "outlet_name": row[2],
            #     })
            #     outlet_sales_set.add(row[2])
                date_object = row[0]  # "2024-11-14"
                # Get the day of the week
                dates_day = date_object.strftime("%A")  # This will return the full name of the day, e.g., "Thursday"

                if dates_day in day_of_week:
                    sales_data.append({
                        "date": row[0],
                        "count": int(row[1]),
                        "outlet_name": row[2],
                        "discounts": row[3],
                        "discountAmt": row[4]
                    })
                    outlet_sales_set.add(row[2])
        if order_type == "Dine-In":
            for row in results:
                date_object = row[0]  # "2024-11-14"
                # Get the day of the week
                dates_day = date_object.strftime("%A")  # This will return the full name of the day, e.g., "Thursday"

                if dates_day in day_of_week:                
                    if row[3] == "Dine-In":
                        sales_data.append({
                            "date": row[0],
                            "count": int(row[1]),
                            "outlet_name": row[2],
                            "discounts": row[3],
                            "discountAmt": row[4]
                        })
                        outlet_sales_set.add(row[2])
        if order_type == "Takeaway":
            for row in results:
                date_object = row[0]  # "2024-11-14"
                # Get the day of the week
                dates_day = date_object.strftime("%A")  # This will return the full name of the day, e.g., "Thursday"

                if dates_day in day_of_week:  
                    if row[3] == "Order":
                        sales_data.append({
                            "date": row[0],
                            "count": int(row[1]),
                            "outlet_name": row[2],
                            "discounts": row[3],
                            "discountAmt": row[4]
                        }) 
                        outlet_sales_set.add(row[2])  

        all_outlet_query = '''SELECT Outlet FROM outetNames'''  # Correct table name assumed to be 'outetNames'
        cursor.execute(all_outlet_query)
        all_outlet_result = cursor.fetchall()
        # Extract outlet names into a set for easier comparison
        all_outlets = {row[0] for row in all_outlet_result}

        # Assuming sales_data is already generated
        grouped_sales_data = {}

        # Group data by outlet name
        for entry in sales_data:
            outlet_name = entry["outlet_name"]
            data_entry = {
                "count": entry["count"],
                "date": entry["date"],
                "discounts": entry["discounts"],
                "discountAmt": entry["discountAmt"]
            }
            if outlet_name not in grouped_sales_data:
                grouped_sales_data[outlet_name] = {"outlet_name": outlet_name, "data": []}
            grouped_sales_data[outlet_name]["data"].append(data_entry)

        # Convert the grouped dictionary into a list
        transformed_sales_data = [{"outlet_name": key, "data": value["data"]} for key, value in grouped_sales_data.items()]  
        # for outlet in all_outlets - outlet_sales_set:
        #     transformed_sales_data.append({
        #         "data": [],
        #         "outlet_name": outlet,
        #     })          
        return transformed_sales_data, 200
    except Exception as error:
        data ={'error':str(error)}
        return data,400