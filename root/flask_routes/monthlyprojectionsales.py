# from flask import  Blueprint,request
# import mysql.connector
# from flask_cors import cross_origin
# import os
# from dotenv import load_dotenv
# load_dotenv()
# app_file58= Blueprint('app_file58',__name__)
# from root.auth.check import token_auth
# import re

# @app_file58.route("/monthlyprojection", methods=["POST"])
# @cross_origin()
# def statsummary():
#     try:
#         mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
#         cursor = mydb.cursor(buffered=True)
#         database_sql = "USE {};".format(os.getenv('database'))
#         cursor.execute(database_sql)
#         json = request.get_json()
#         if "token" not in json  or not any([json["token"]])  or json["token"]=="":
#             data = {"error":"No token provided."}
#             return data,400
#         token = json["token"]
#         if not token_auth(token):
#             data = {"error":"Invalid token."}
#             return data,400



#     except Exception as error:
#         data ={'error':str(error)}
#         return data,400


from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from datetime import datetime
import calendar

load_dotenv()

app_file58 = Blueprint('app_file58', __name__)
from root.auth.check import token_auth

@app_file58.route("/monthlyprojection", methods=["POST"])
@cross_origin()
def statsummary():
    try:
        # Connect to the database
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(buffered=True)

        # Parse JSON input
        json = request.get_json()
        if "token" not in json or not any([json["token"]]) or json["token"] == "":
            return {"error": "No token provided."}, 400
        token = json["token"]
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        # # Get the input date or default to the current date
        # input_date = json.get("date", datetime.now().strftime("%Y-%m-%d"))
        # input_date = datetime.strptime(input_date, "%Y-%m-%d")

        #Use the current date 
        input_date = datetime.now()

        # Extract year and month
        year = input_date.year
        month = input_date.month
        month_name = calendar.month_name[month]
        # Calculate first and last dates of the month
        first_date = f"{year}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        last_date = f"{year}-{month:02d}-{last_day:02d}"

        # Query for outlets
        cursor.execute("SELECT Outlet FROM outetNames")
        outlets = [row[0] for row in cursor.fetchall()]

        # Prepare response data
        response = []
        for outlet in outlets:
            # Calculate sales for the current month up to the input date
            query = """
                SELECT SUM(Total - IFNULL(VAT, 0) - IFNULL(serviceCharge, 0))
                FROM tblorderhistory
                WHERE Outlet_Name = %s
                AND Date >= %s
                AND Date <= %s
            """
            cursor.execute(query, (outlet, first_date, input_date.strftime("%Y-%m-%d")))
            sales_upto_date = cursor.fetchone()[0] or 0

            # Calculate total days up to the input date in the current month
            total_days = input_date.day

            # Calculate average daily sales
            average_daily_sales = sales_upto_date / total_days if total_days > 0 else 0

            # Calculate projected sales for the full month
            projected_sales = average_daily_sales * last_day

            # Calculate last year's sales for the same month
            last_year_first_date = f"{year - 1}-{month:02d}-01"
            last_year_last_date = f"{year - 1}-{month:02d}-{calendar.monthrange(year - 1, month)[1]:02d}"
            query_last_year = """
                SELECT SUM(Total - IFNULL(VAT, 0) - IFNULL(serviceCharge, 0))
                FROM tblorderhistory
                WHERE Outlet_Name = %s
                AND Date >= %s
                AND Date <= %s
            """
            cursor.execute(query_last_year, (outlet, last_year_first_date, last_year_last_date))
            last_year_sales = cursor.fetchone()[0] or 0

            today_sales_query = """
                SELECT SUM(Total - IFNULL(VAT, 0) - IFNULL(serviceCharge, 0))
                FROM tblorderhistory
                WHERE Outlet_Name = %s
                AND Date = %s

            """
            cursor.execute(today_sales_query, (outlet, input_date.strftime("%Y-%m-%d")))
            todays_sales = cursor.fetchone()[0] or 0
            # Append results for the current outlet
            response.append({
                "outlet": outlet,
                "sales_upto_date": round(float(sales_upto_date), 2),
                "total_days": total_days,
                "average_daily_sales": round(float(average_daily_sales), 2),
                "projected_sales": round(float(projected_sales), 2),
                "last_year_sales": round(float(last_year_sales), 2),
                "todays_sales" : todays_sales
            })

        # Close the connection
        cursor.close()
        mydb.close()

        return {"month": month_name,
            "data": response}, 200

    except Exception as error:
        return {"error": str(error)}, 400
