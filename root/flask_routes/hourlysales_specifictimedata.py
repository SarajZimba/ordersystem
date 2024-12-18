from flask import  Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file37 = Blueprint('app_file37',__name__)
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

@app_file37.route("/hourlysales-specifictimegroupdata", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "token" not in json or "time" not in json or "outlet" not in json or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400
        if "date" not in json:
            data = {"error":"Some fields are missing"}
            return data,400
        date = json["date"]
        time = json["time"]
        outlet_name = json["outlet"]

        if not valid_date(date):
            data={"error":"Invalid date supplied."}
            return data,400
        

        query = """select count(td.idtblorderHistory), td.Start_Time, td.Outlet_Name  from tblorderhistory td where date=%s group by td.Outlet_Name, td.Start_Time """
        cursor.execute(query, (date,))
        results = cursor.fetchall()
        grouped_data = group_sales_data(results)
        print(grouped_data)

        # for row in results:

        for outlet_data in grouped_data:
            if outlet_data["outlet_name"] == outlet_name:
                for time_data in outlet_data["data"]:
                    if time_data["time"] == time:
                        return time_data, 200

        return "Something went wrong", 200
             


    except Exception as error:
        data ={'error':str(error)}
        return data,400

from datetime import datetime

# Define the time blocks as tuples of start and end times in 24-hour format
time_blocks = [
    ("10:00 AM", "11:00 AM"),
    ("11:00 AM", "12:00 PM"),
    ("1:00 PM", "2:00 PM"),
    ("2:00 PM", "3:00 PM"),
    ("3:00 PM", "4:00 PM"),
    ("4:00 PM", "5:00 PM"),
    ("5:00 PM", "6:00 PM"),
    ("6:00 PM", "7:00 PM"),
    ("7:00 PM", "8:00 PM"),
    ("8:00 PM", "9:00 PM"),
    ("9:00 PM", "10:00 PM"),
    ("10:00 PM", "11:00 PM")
]

# Convert time string to 24-hour format for comparison
def convert_to_24hr(time_str):
    return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")

def group_sales_data(results):
    # Initialize an empty list to hold the final output
    output_data = []

    # Iterate through the results and group by outlet name
    outlets_data = {}

    for count, start_time, outlet in results:
        # Initialize the dictionary for each outlet if it doesn't exist
        if outlet not in outlets_data:
            outlets_data[outlet] = {}

        # Ensure all time blocks exist for the outlet, even if no orders fall into them
        for block_start, block_end in time_blocks:
            block_key = f"{block_start} - {block_end}"
            if block_key not in outlets_data[outlet]:
                outlets_data[outlet][block_key] = []

        # Convert the Start_Time to 24-hour format
        start_time_24hr = convert_to_24hr(start_time)

        # Process each time block to determine where the start_time fits
        for block_start, block_end in time_blocks:
            block_start_24hr = convert_to_24hr(block_start)
            block_end_24hr = convert_to_24hr(block_end)

            # If the start_time falls within the block range, append to that block
            if block_start_24hr <= start_time_24hr < block_end_24hr:
                block_key = f"{block_start} - {block_end}"
                outlets_data[outlet][block_key].append({'Start_Time': start_time})

    # Transform the data into the desired output format
    for outlet, time_blocks_data in outlets_data.items():
        outlet_data = {
            "outlet_name": outlet,
            "data": []
        }

        # Add each time block as a dictionary with 'time' and 'orders'
        for block_key, orders in time_blocks_data.items():
            outlet_data["data"].append({
                "time": block_key,
                "orders": orders
            })

        output_data.append(outlet_data)

    return output_data
