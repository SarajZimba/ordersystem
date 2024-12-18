from flask import Blueprint, request, jsonify
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
import json
load_dotenv()

app_file45 = Blueprint('app_file45', __name__)
from root.auth.check import token_auth
    

@app_file45.route("/salesofcustomer", methods=["POST"])
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
        print(json)

        if "token" not in json or not json["token"]:
            return {"error": "No token provided."}, 400
        token = json["token"]
        if not token_auth(token):
            return {"error": "Invalid token."}, 400

        if "dateStart" not in json or "dateEnd" not in json or "customer_name" not in json or not any((json["dateStart"], json["dateEnd"], json["customer_name"])):
            return {"error": "Some fields are missing"}, 400

        # Get inputs
        dateStart = json["dateStart"]
        dateEnd = json["dateEnd"]
        customer_name = json["customer_name"]

        # Main sales query
        salesofcustomer_query = """
            SELECT 
                Outlet_Name,
                SUM(Cash) AS Cash,
                SUM(CreditCard) AS CreditCard,
                SUM(MobilePayment) AS MobilePayment,
                SUM(Credit) AS Credit,
                SUM(TotalSales) AS TotalSales,
                SUM(Complimentary_Sales) AS TotalSales

            FROM (
                -- Subquery 1: Aggregating data from tblorderhistory
                SELECT 
                    oh.Outlet_Name,
                    SUM(CASE WHEN oh.PaymentMode = 'Cash' THEN oh.Total ELSE 0 END) AS Cash,
                    SUM(CASE WHEN oh.PaymentMode = 'Credit Card' THEN oh.Total ELSE 0 END) AS CreditCard,
                    SUM(CASE WHEN oh.PaymentMode = 'Mobile Payment' THEN oh.Total ELSE 0 END) AS MobilePayment,
                    SUM(CASE WHEN oh.PaymentMode = 'Credit' THEN oh.Total ELSE 0 END) AS Credit,
                    SUM(oh.Total) AS TotalSales,
            COALESCE(SUM(CASE WHEN (oh.PaymentMode = 'Complimentary' or oh.PaymentMode='Non Chargeable') THEN oh.Total END), 0) AS Complimentary_Sales
                FROM 
                    tblorderhistory oh
                WHERE 
                    oh.Date BETWEEN %s AND %s
                    AND oh.GuestName = %s
                GROUP BY 
                    oh.Outlet_Name

                UNION ALL

                -- Subquery 2: Aggregating data from payment_history
                SELECT 
                    oh.Outlet_Name,
                    SUM(CASE WHEN ph.paymentMode = 'Cash' THEN ph.paymentAmount ELSE 0 END) AS Cash,
                    SUM(CASE WHEN ph.paymentMode = 'Credit Card' THEN ph.paymentAmount ELSE 0 END) AS CreditCard,
                    SUM(CASE WHEN ph.paymentMode = 'Mobile Payment' THEN ph.paymentAmount ELSE 0 END) AS MobilePayment,
                    0 AS Credit,  -- Credit doesn't exist in payment_history
                    0 AS TotalSales -- TotalSales only comes from tblorderhistory,
                    0 as Complimentary_Sales --ComplimentarySales only comes from tblorderhistory
                FROM 
                    payment_history ph
                JOIN 
                    tblorderhistory oh ON ph.orderHistoryid = oh.idtblorderHistory
                WHERE 
                    oh.Date BETWEEN %s AND %s
                    AND oh.GuestName = %s
                GROUP BY 
                    oh.Outlet_Name
            ) AS CombinedResults
            GROUP BY 
                Outlet_Name;
        """

        cursor.execute(salesofcustomer_query, (dateStart, dateEnd, customer_name,
                                               dateStart, dateEnd, customer_name))
        result = cursor.fetchall()

        outlet_set = set()
        salesofcustomer_dict = []
        for item in result:
            outlet_name, cash, creditCard, mobilePayment, credit, totalSales = item
            item_data = {
                "outlet_name": outlet_name,
                "Cash": float(cash),
                "CreditCard": float(creditCard),
                "MobilePayment": int(mobilePayment),
                "Credit": float(credit),
                "TotalSales": float(totalSales),
                "bills": [],
                "all_items": []
            }
            salesofcustomer_dict.append(item_data)
            outlet_set.add(outlet_name)

        # Query to fetch the orders of the customer
        orders_query = """
            SELECT *
            FROM tblorderhistory oh
            WHERE oh.GuestName = %s AND oh.Date BETWEEN %s AND %s;
        """
        cursor.execute(orders_query, (customer_name, dateStart, dateEnd))
        orders = cursor.fetchall()

        # Query to fetch the order details for each order
        order_details_query = """
            SELECT od.order_ID, od.ItemName, od.itemRate, od.Total, od.count
            FROM tblorder_detailshistory od
            WHERE od.order_ID = %s;
        """
        
        # Process orders and append their details to the correct outlet
        for order in orders:
            order_id, outlet_orderID, Employee, Table_no, Noofguests, Start_time, End_time, State, Type, Discounts, Date, bill_no, total, serviceCharge, vat, discountAmt, PaymentMode, fiscalYear, GuestName, Outlet_name, billPrintTime, guestId, guestEmail, guestPhone, guestAddress = order
            # Find the matching outlet in the salesofcustomer_dict
            for outlet in salesofcustomer_dict:
                if outlet["outlet_name"] == Outlet_name:
                    # Fetch order details for this order
                    cursor.execute(order_details_query, (order_id,))
                    order_details = cursor.fetchall()
                    
                    # Create the bill structure
                    bill = {
                        "bill_no": bill_no,
                        "total": float(total),
                        "order_date": Date,
                        "order_id":order_id,
                        "outlet_orderId": outlet_orderID,
                        "employee": Employee,
                        "table_no" : Table_no,
                        "noOfGuest": Noofguests,
                        "startTime":Start_time,
                        "endTime": End_time,
                        "state": State,
                        "type": Type,
                        "Discounts": Discounts,
                        "serviceCharge": float(serviceCharge),
                        "vat": float(vat),
                        "discountAmt": float(discountAmt),
                        "paymentMode": PaymentMode,
                        "fiscalYear": fiscalYear,
                        "GuestName": GuestName,
                        "OutletName": Outlet_name,
                        "billPrintTime": billPrintTime,
                        "guestId": guestId, 
                        "guestEmail": guestEmail,
                        "guestPhone": guestPhone,
                        "guestAddress": guestAddress ,

                        "items": []
                    }
                    
                    # Add items to the bill
                    for item in order_details:
                        order_ID, item_name, item_rate, item_total, item_count = item
                        bill["items"].append({
                            "order_ID": order_ID,
                            "item_name": item_name,
                            "item_rate": float(item_rate),
                            "item_total": float(item_total),
                            "item_count": int(item_count)
                        })

                    # Append the bill to the outlet
                    outlet["bills"].append(bill)

                    break

        # Query all outlet names
        outletnames_query = "SELECT Outlet FROM outetNames;"
        cursor.execute(outletnames_query)
        all_outlets = [row[0] for row in cursor.fetchall()]

        # Add missing outlets with default values
        for outlet_name in all_outlets:
            if outlet_name not in outlet_set:
                salesofcustomer_dict.append({
                    "outlet_name": outlet_name,
                    "Cash": 0.0,
                    "CreditCard": 0.0,
                    "MobilePayment": 0.0,
                    "Credit": 0.0,
                    "TotalSales": 0.0,
                    "bills": [],
                    "all_items": []
                })

        # Query to fetch the total item sales by outlet and item
        item_sales_query = """
            SELECT od.ItemName, od.itemRate, SUM(od.Total) AS Total, SUM(od.count) AS Count, oh.Outlet_Name
            FROM tblorder_detailshistory od, tblorderhistory oh
            WHERE od.order_ID = oh.idtblorderHistory
            AND oh.GuestName = %s
            AND oh.Date BETWEEN %s AND %s
            GROUP BY od.ItemName, oh.Outlet_Name;
        """
        
        # Execute the query
        cursor.execute(item_sales_query, (customer_name, dateStart, dateEnd))
        item_sales_result = cursor.fetchall()

        # Append the item sales data to the respective outlet in salesofcustomer_dict
        for item in item_sales_result:
            item_name, item_rate, total_sales, item_count, outlet_name = item
            for outlet in salesofcustomer_dict:
                if outlet["outlet_name"] == outlet_name:
                    # Append the item details to the 'all_items' of the respective outlet
                    outlet["all_items"].append({
                        "item_name": item_name,
                        "item_rate": float(item_rate),
                        "item_total": float(total_sales),
                        "item_count": int(item_count)
                    })
                    break


        cursor.close()
        mydb.close()

        # Sort the result by TotalSales in descending order
        salesofcustomer_dict = sorted(salesofcustomer_dict, key=lambda x: x["TotalSales"], reverse=True)
        return jsonify(salesofcustomer_dict), 200

    except Exception as e:
        print(str(e))
        return {"error": str(e)}, 400
