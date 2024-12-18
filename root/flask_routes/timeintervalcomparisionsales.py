from flask import  Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file56= Blueprint('app_file56',__name__)
from root.auth.check import token_auth
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
@app_file56.route("/timeintervalwisesalescomparision", methods=["POST"])
@cross_origin()
def statsummary():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        post_data = request.get_json()
        timeintervaljson_list = post_data['intervalList']
        token = post_data['token']
        if "token" not in post_data  or not any([post_data["token"]])  or post_data["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        # token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400

        timeintervalwisesalesResponseList = []
        for json in timeintervaljson_list:
            if "dateStart" not in json or "dateEnd" not in json:
                data = {"error":"Some fields are missing"}
                return data,400
            start_Date = json["dateStart"]
            end_Date = json["dateEnd"]


            if not valid_date(start_Date) or not valid_date(end_Date):
                data={"error":"Invalid date supplied."}
                return data,400
            totalNoOfDays = calculate_no_of_days(start_Date, end_Date)
            query = """
            SELECT 
                oh.Outlet_Name AS Outlet,
                -- Calculate Complimentary Sales
                COALESCE(SUM(CASE WHEN oh.PaymentMode = 'Complimentary' THEN oh.Total END), 0) AS Complimentary_Sales,
                -- Calculate Banquet Sales
                COALESCE(SUM(CASE WHEN oh.Type = 'Banquet' THEN oh.Total END), 0) AS Banquet_Sales,
                -- Calculate Discount Sales
                COALESCE(SUM(oh.DiscountAmt), 0) AS Discounts_Sales,
                -- Calculate Food Sales from tblorder_detailshistory
                COALESCE((
                    SELECT SUM(od.Total)
                    FROM tblorder_detailshistory od
                    WHERE od.ItemType = 'Food'
                    AND od.order_ID IN (
                        SELECT idtblorderHistory 
                        FROM tblorderhistory 
                        WHERE oh.Outlet_Name = Outlet_Name AND Date BETWEEN %s AND %s AND bill_no != ''
                    )
                ), 0) AS Food_Sales,
                -- Calculate Beverage Sales from tblorder_detailshistory
                COALESCE((
                    SELECT SUM(od.Total)
                    FROM tblorder_detailshistory od
                    WHERE od.ItemType = 'Beverage'
                    AND od.order_ID IN (
                        SELECT idtblorderHistory 
                        FROM tblorderhistory 
                        WHERE oh.Outlet_Name = Outlet_Name AND Date BETWEEN %s AND %s AND bill_no != ''
                    )
                ), 0) AS Beverage_Sales
            FROM 
                tblorderhistory oh
            WHERE 
                oh.Date BETWEEN %s AND %s
            GROUP BY 
                oh.Outlet_Name;
            """

            cursor.execute(query, (start_Date, end_Date, start_Date, end_Date, start_Date, end_Date))
            result = cursor.fetchall()


            sales_data = []
            outlet_sales_set = set()  # To track outlets with data
            for row in result:
                outlet = row[0]
                complimentary_sales = row[1]
                banquet_sales = row[2]
                discounts_sales = row[3]
                food_sales = row[4]
                beverage_sales = row[5]

                total_sales = food_sales + beverage_sales + banquet_sales - discounts_sales

                without_complimentary_total_sales = food_sales + beverage_sales + banquet_sales - discounts_sales - complimentary_sales 


                sales_data.append({
                    "Outlet": outlet,
                    "TotalSales": float(total_sales),
                    "ComplimentarySales": float(complimentary_sales),
                    "BanquetSales": float(banquet_sales),
                    "discount": float(discounts_sales),
                    "foodSale": float(food_sales),
                    "beverageSale": float(beverage_sales),
                    "avg_foodSales": float(food_sales/totalNoOfDays),
                    "avg_beverageSales": float(beverage_sales/totalNoOfDays),
                    "avg_banquetSales": float(banquet_sales/totalNoOfDays),
                    "avg_totalSales": float(total_sales/totalNoOfDays),

                })
                outlet_sales_set.add(row[0])

            all_outlet_query = '''SELECT Outlet FROM outetNames'''  # Correct table name assumed to be 'outetNames'
            cursor.execute(all_outlet_query)
            all_outlet_result = cursor.fetchall()
            # Extract outlet names into a set for easier comparison
            all_outlets = {row[0] for row in all_outlet_result}
            # Find outlets without sales and append null data for them
            for outlet in all_outlets - outlet_sales_set:
                sales_data.append({
                    "Outlet": outlet,
                    "TotalSales": float(0),
                    "ComplimentarySales": float(0),
                    "BanquetSales": float(0),
                    "discount": float(0),
                    "foodSale": float(0),
                    "beverageSale": float(0),
                    "avg_foodSales": float(0),
                    "avg_beverageSales": float(0),
                    "avg_banquetSales": float(0),
                    "avg_totalSales": float(0)
                })

            timeintervalsalesdata = {
                 "startDate": start_Date,
                 "endDate": end_Date,
                 "interval" : str(start_Date) + " to " + str(end_Date),
                 "sales_data": sales_data
            }
            timeintervalwisesalesResponseList.append(timeintervalsalesdata)
        cursor.close()
        mydb.close()
        return timeintervalwisesalesResponseList
    except Exception as error:
        data ={'error':str(error)}
        return data,400
    
from datetime import datetime
def calculate_no_of_days(start_date_str, end_date_str):
    # Convert string to datetime objects
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # Calculate the number of days between start_date and end_date
    delta = (end_date - start_date).days


    days_inclusive = delta + 1  # Add 1 to include both start and end dates

    return days_inclusive