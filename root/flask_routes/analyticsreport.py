from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
import json
load_dotenv()

app_file44 = Blueprint('app_file44', __name__)
from root.auth.check import token_auth

@app_file44.route("/analyticsreport", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password')
        )
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()

        if "token" not in json or not json["token"]:
            return {"error": "No token provided."}, 400
        token = json["token"]
        if not token_auth(token):
            return {"error": "Invalid token."}, 400
        if "dateStart" not in json or "dateEnd" not in json or "timeStart" not in json or "timeEnd" not in json:
            return {"error": "Some fields are missing"}, 400

        # Get inputs
        dateStart = json["dateStart"]
        dateEnd = json["dateEnd"]
        timeStart = json["timeStart"]
        timeEnd = json["timeEnd"]

        # Create start and end datetimes
        startDatetime = f"{dateStart} {timeStart}"  # e.g., "2024-11-20 00:00 AM"
        endDatetime = f"{dateEnd} {timeEnd}"        # e.g., "2024-11-21 11:25 PM"

        # Main sales query
        sales_query = """
        SELECT 
            oh.Outlet_Name AS Outlet,
            COALESCE(SUM(CASE WHEN (oh.PaymentMode = 'Complimentary' or oh.PaymentMode='Non Chargeable') THEN oh.Total END), 0) AS Complimentary_Sales,
            COALESCE(SUM(CASE WHEN oh.Type = 'Banquet' THEN oh.Total END), 0) AS Banquet_Sales,
            COALESCE(SUM(CASE WHEN (oh.bill_no != '') THEN oh.DiscountAmt END), 0) AS Discounts_Sales,
            COALESCE((
                SELECT SUM(od.Total)
                FROM tblorder_detailshistory od
                WHERE od.ItemType = 'Food'
                AND od.order_ID IN (
                    SELECT idtblorderHistory 
                    FROM tblorderhistory 
                    WHERE oh.Outlet_Name = Outlet_Name 
                    AND STR_TO_DATE(CONCAT(Date, ' ', Start_Time), '%Y-%m-%d %h:%i %p') 
                        BETWEEN STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p') 
                        AND STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p') AND bill_no != ''
                )
            ), 0) AS Food_Sales,
            COALESCE((
                SELECT SUM(od.Total)
                FROM tblorder_detailshistory od
                WHERE od.ItemType = 'Beverage'
                AND od.order_ID IN (
                    SELECT idtblorderHistory 
                    FROM tblorderhistory 
                    WHERE oh.Outlet_Name = Outlet_Name 
                    AND STR_TO_DATE(CONCAT(Date, ' ', Start_Time), '%Y-%m-%d %h:%i %p') 
                        BETWEEN STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p') 
                        AND STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p') AND bill_no != ''
                )
            ), 0) AS Beverage_Sales,
            COALESCE(SUM(oh.NoOfGuests), 0) AS NoOfGuests,
            COALESCE(SUM(CASE WHEN oh.Type = 'Dine-In' and oh.bill_no != '' THEN (oh.Total-oh.VAT - oh.serviceCharge) ELSE 0 END)) AS TotalDineInCount,
            COALESCE(SUM(CASE WHEN oh.Type = 'Order' and oh.bill_no != '' THEN (oh.Total-oh.VAT - oh.serviceCharge) ELSE 0 END)) AS TotalDineInCount,
            COALESCE(SUM(CASE WHEN oh.Type = 'Banquet' and oh.bill_no != '' THEN (oh.Total-oh.VAT - oh.serviceCharge) ELSE 0 END)) AS TotalDineInCount,
            COALESCE(Count(oh.idtblorderHistory)) AS TotalOrdersCount
        FROM 
            tblorderhistory oh
        WHERE 
            STR_TO_DATE(CONCAT(oh.Date, ' ', oh.Start_Time), '%Y-%m-%d %h:%i %p') 
                BETWEEN STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p') 
                AND STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p') AND bill_no != ''
        GROUP BY 
            oh.Outlet_Name;
        """

        # # Item details query (join tblorderhistory to include Outlet_Name)
        # item_query = """
        # SELECT 
        #     oh.Outlet_Name, 
        #     od.ItemType, 
        #     od.Description, 
        #     od.ItemName, 
        #     od.itemRate, 
        #     SUM(od.count) AS TotalCount, 
        #     SUM(od.Total) AS Total,
        #     SUM(CASE WHEN oh.Type = 'Dine-In' THEN od.count ELSE 0 END) AS TotalDineInCount,
        #     SUM(CASE WHEN oh.Type = 'Order' THEN od.count ELSE 0 END) AS TotalTakeawayCount
        # FROM 
        #     tblorder_detailshistory od
        # JOIN 
        #     tblorderhistory oh ON od.order_ID = oh.idtblorderHistory
        # WHERE 
        #     STR_TO_DATE(CONCAT(oh.Date, ' ', oh.Start_Time), '%Y-%m-%d %h:%i %p') 
        #         BETWEEN STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p') 
        #         AND STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p')
        # GROUP BY 
        #     oh.Outlet_Name, od.ItemType, od.ItemName
        # ORDER BY 
        #     oh.Outlet_Name, od.ItemType, TotalCount DESC;
        # """
        item_query = """
        SELECT 
            oh.Outlet_Name, 
            od.ItemType, 
            od.Description, 
            od.ItemName, 
            od.itemRate, 
            SUM(od.count) AS TotalCount, 
            SUM(od.Total) AS Total,
            SUM(CASE WHEN oh.Type = 'Dine-In' THEN od.count ELSE 0 END) AS TotalDineInCount,
            SUM(CASE WHEN oh.Type = 'Order' THEN od.count ELSE 0 END) AS TotalTakeawayCount
        FROM 
            tblorder_detailshistory od
        JOIN 
            tblorderhistory oh ON od.order_ID = oh.idtblorderHistory
        WHERE 
            STR_TO_DATE(CONCAT(oh.Date, ' ', oh.Start_Time), '%Y-%m-%d %h:%i %p') 
                BETWEEN STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p') 
                AND STR_TO_DATE(%s, '%Y-%m-%d %h:%i %p') AND bill_no != ''
        GROUP BY 
            oh.Outlet_Name, od.ItemType, od.ItemName
        ORDER BY 
            oh.Outlet_Name, od.ItemType, TotalCount DESC;
        """


        # Execute sales query
        cursor.execute(sales_query, (
            startDatetime, endDatetime, startDatetime, endDatetime, 
            startDatetime, endDatetime
        ))
        sales_result = cursor.fetchall()

        # Execute item query
        cursor.execute(item_query, (startDatetime, endDatetime))
        item_result = cursor.fetchall()



        # Process sales results
        sales_data = []
        for row in sales_result:
            outlet = row[0]
            complimentary_sales = row[1]
            banquet_sales = row[2]
            discounts_sales = row[3]
            food_sales = row[4]
            beverage_sales = row[5]
            noOfGuests = row[6]
            DineInSales = row[7]
            TakeawaySales = row[8]
            BanquetSales = row[9]
            no_of_orders = row[10]
            total_sales = food_sales + beverage_sales + banquet_sales - discounts_sales

            without_complimentary_total_sales = (
                food_sales + beverage_sales + banquet_sales - discounts_sales - complimentary_sales
            )

            DineInSalesPercent = round((float(DineInSales)/float(total_sales)) * 100, 2) if float(total_sales) != 0.0 else 0.0
            TakeawaySalesPercent = round((float(TakeawaySales)/float(total_sales)) * 100, 2) if float(total_sales) != 0.0 else 0.0
            BanquetSalesPercent = round((float(BanquetSales)/float(total_sales)) * 100, 2) if float(total_sales) != 0.0 else 0.0
            avgSales = round(total_sales/no_of_orders, 2)

            sales_data.append({
                "Outlet": outlet,
                "Total_Sales": float(total_sales),
                "Complimentary_Sales": float(complimentary_sales),
                "Banquet_Sales": float(banquet_sales),
                "Discounts_Sales": float(discounts_sales),
                "Food_Sales": float(food_sales),
                "Beverage_Sales": float(beverage_sales),
                "Food_Items": [],
                "Beverage_Items": [],
                "Other_Items": [],
                "noOfGuests": int(noOfGuests),
                "DineInSales": float(DineInSales),
                "TakeawaySales": float(TakeawaySales),
                "BanquetSales": float(BanquetSales),
                "DineInSalesPercent":DineInSalesPercent,
                "TakeawaySalesPercent":TakeawaySalesPercent,
                "BanquetSalesPercent":BanquetSalesPercent,
                "avgSales":float(avgSales),

            })

        # Process item results and append them to the appropriate outlet
        for item in item_result:
            outlet_name, item_type, description, item_name, item_rate, total_count, total, totalDineIN, totalTakeaway = item
            item_data = {
                "Description": description,
                "ItemName": item_name,
                "ItemRate": float(item_rate),
                "TotalCount": int(total_count),
                "Total": float(total),
                "TotalDineIn": float(totalDineIN),
                "TotalTakeaway": float(totalTakeaway)
            }

            # Find the corresponding outlet and append the item
            for sales in sales_data:
                if sales["Outlet"] == outlet_name:
                    if item_type == "Food":
                        sales["Food_Items"].append(item_data)
                    elif item_type == "Beverage":
                        sales["Beverage_Items"].append(item_data)
                    else:
                        sales["Other_Items"].append(item_data)
                    break

        all_menu_query = """select * from tblmenu where state='Active'"""
        cursor.execute(all_menu_query)

        all_menus = cursor.fetchall()
        for outlet_sales in sales_data:
            for item in all_menus:
                item_type = item[3]
                item_name = item[1] 
                description = item[2] 
                rate = item[4] 
                if item_type == 'Food':
                    food_item_list = get_item_list(outlet_sales["Food_Items"])

                    if item_name not in food_item_list:
                        item_data = {
                            "Description": description,
                            "ItemName": item_name,
                            "ItemRate": float(rate),
                            "Total": 0.0,
                            "TotalCount": 0,
                            "TotalDineIn": 0,
                            "TotalTakeaway": 0
                        }
                        outlet_sales["Food_Items"].append(item_data)
                if item_type == 'Beverage':
                    beverage_item_list = get_item_list(outlet_sales["Beverage_Items"])

                    if item_name not in beverage_item_list:
                        item_data = {
                            "Description": description,
                            "ItemName": item_name,
                            "ItemRate": float(rate),
                            "Total": 0.0,
                            "TotalCount": 0,
                            "TotalDineIn": 0,
                            "TotalTakeaway": 0
                        }
                        outlet_sales["Beverage_Items"].append(item_data)
                if item_type == 'Others':
                    other_item_list = get_item_list(outlet_sales["Other_Items"])

                    if item_name not in other_item_list:
                        item_data = {
                            "Description": description,
                            "ItemName": item_name,
                            "ItemRate": float(rate),
                            "Total": 0.0,
                            "TotalCount": 0,
                            "TotalDineIn": 0,
                            "TotalTakeaway": 0
                        }
                        outlet_sales["Other_Items"].append(item_data)
        cursor.close()
        mydb.close()
        return sales_data

    except Exception as e:
        return {"error": str(e)}, 400
    

def get_item_list(items):
    items_list = []
    for item in items:
        items_list.append(item["ItemName"])
    return items_list

