from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file7 = Blueprint('app_file7', __name__)
from root.auth.check import token_auth

@app_file7.route("/saleshistory", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "token" not in json or not any([json["token"]]) or json["token"] == "":
            data = {"error": "No token provided."}
            return data, 400
        token = json["token"]
        if not token_auth(token):
            data = {"error": "Invalid token."}
            return data, 400
        if "outlet" not in json or "dateStart" not in json or "dateEnd" not in json:
            data = {"error": "Some fields are missing"}
            return data, 400
        outlet = json["outlet"]
        startDate = json["dateStart"]
        endDate = json["dateEnd"]

        orderHistory = """
        SELECT
            tblorderhistory.Date, tblorderhistory.bill_no,
            (tblorderhistory.Total - tblorderhistory.serviceCharge - tblorderhistory.VAT) AS 'Subtotal',
            tblorderhistory.Outlet_OrderID AS id, tblorderhistory.serviceCharge, tblorderhistory.VAT, tblorderhistory.Total,
            tblorderhistory.DiscountAmt, tblorderhistory.PaymentMode, tblorderhistory.GuestName, tblorderhistory.idtblorderhistory,
            payment_history.paymentMode AS paymentModeHistory, payment_history.paymentAmount AS paymentAmountHistory, tblorderhistory.guestID
        FROM
            tblorderhistory
        LEFT JOIN
            payment_history ON tblorderhistory.idtblorderhistory = payment_history.orderHistoryid AND tblorderhistory.PaymentMode = 'Split'
        WHERE
            tblorderhistory.Date BETWEEN %s AND %s
            AND tblorderhistory.Outlet_Name = %s;
        """
        cursor.execute(orderHistory, (
            startDate, endDate, outlet,
        ),)
        result = cursor.fetchall()
        if result == []:
            data = {"error": "No data available."}
            return data, 400
        row_headers = [x[0] for x in cursor.description]
        json_data = []
        for res in result:
            json_data.append(dict(zip(row_headers, res)))

        statsSql = """
        SELECT
            SUM(DiscountAmt) AS DiscountAmountSum,
            SUM(Total - serviceCharge - VAT) AS SubtotalAmountSum,
            SUM(Total) AS TotalSum,
            SUM(VAT) AS VatSum,
            SUM(serviceCharge) AS ServiceChargeSum,
            SUM(NoOfGuests) AS TotalGuestsServed,
            COUNT(idtblorderHistory) AS TotalOrders,
            COUNT(DISTINCT Date) AS DaysOperated
        FROM tblorderhistory
        WHERE Date BETWEEN %s AND %s AND Outlet_Name = %s;
        """
        cursor.execute(statsSql, (startDate, endDate, outlet,))
        statsResult = cursor.fetchall()
        Stats_json_data = []
        if statsResult == []:
            Stats_json_data.append({"orderDetails": {"error": "No data available."}})
        else:
            row_headers = [x[0] for x in cursor.description]
            for res in statsResult:
                Stats_json_data.append(dict(zip(row_headers, res)))
            Stats_json_data[0]["orderDetails"] = json_data

        items_food_Sql = """
        SELECT
            a.Description, a.itemName,
            SUM(a.count) AS quantity,
            a.itemRate AS itemrate,
            SUM(a.Total) AS total,
            a.ItemType
        FROM tblorder_detailshistory a, tblorderhistory b
        WHERE
            a.ItemType = 'Food'
            AND a.order_ID = b.idtblorderHistory
            AND b.Outlet_Name = %s
            AND b.Date BETWEEN %s AND %s
        GROUP BY a.ItemName, a.Description
        ORDER BY a.Description;
        """
        cursor.execute(items_food_Sql, (outlet, startDate, endDate,))
        items_foodResult = cursor.fetchall()
        items_food_json_data = []
        if not items_foodResult:
            items_food_json_data.append({"Data": {"error": "No food data available."}})
        else:
            row_headers = [x[0] for x in cursor.description]
            for res in items_foodResult:
                items_food_json_data.append(dict(zip(row_headers, res)))

        items_beverage_Sql = """
        SELECT
            a.Description, a.itemName,
            SUM(a.count) AS quantity,
            a.itemRate AS itemrate,
            SUM(a.Total) AS total,
            a.ItemType
        FROM tblorder_detailshistory a, tblorderhistory b
        WHERE
            a.ItemType = 'Beverage'
            AND a.order_ID = b.idtblorderHistory
            AND b.Outlet_Name = %s
            AND b.Date BETWEEN %s AND %s
        GROUP BY a.ItemName, a.Description
        ORDER BY a.Description;
        """
        cursor.execute(items_beverage_Sql, (outlet, startDate, endDate,))
        items_beverageResult = cursor.fetchall()
        items_beverage_json_data = []
        if not items_beverageResult:
            items_beverage_json_data.append({"Data": {"error": "No beverage data available."}})
        else:
            row_headers = [x[0] for x in cursor.description]
            for res in items_beverageResult:
                items_beverage_json_data.append(dict(zip(row_headers, res)))

        items_sum_Sql = """
        SELECT
            (SELECT SUM(a.total) FROM tblorder_detailshistory a, tblorderhistory b
             WHERE
                a.ItemType = 'Beverage'
                AND a.order_ID = b.idtblorderHistory
                AND b.Outlet_Name = %s
                AND b.Date BETWEEN %s AND %s) AS beveragetotal,
            (SELECT SUM(a.count) FROM tblorder_detailshistory a, tblorderhistory b
             WHERE
                a.ItemType = 'Beverage'
                AND a.order_ID = b.idtblorderHistory
                AND b.Outlet_Name = %s
                AND b.Date BETWEEN %s AND %s) AS beveragequantity,
            (SELECT SUM(a.total) FROM tblorder_detailshistory a, tblorderhistory b
             WHERE
                a.ItemType = 'Food'
                AND a.order_ID = b.idtblorderHistory
                AND b.Outlet_Name = %s
                AND b.Date BETWEEN %s AND %s) AS foodtotal,
            (SELECT SUM(a.count) FROM tblorder_detailshistory a, tblorderhistory b
             WHERE
                a.ItemType = 'Food'
                AND a.order_ID = b.idtblorderHistory
                AND b.Outlet_Name = %s
                AND b.Date BETWEEN %s AND %s) AS foodquantity;
        """
        cursor.execute(items_sum_Sql, (outlet, startDate, endDate, outlet, startDate, endDate, outlet, startDate, endDate, outlet, startDate, endDate,))
        items_sumResult = cursor.fetchall()
        items_sum_json_data = []
        if not items_sumResult:
            items_sum_json_data.append({"error": "No data available."})
        else:
            row_headers = [x[0] for x in cursor.description]
            for res in items_sumResult:
                items_sum_json_data.append(dict(zip(row_headers, res)))

        beverageGrouptotalSql = """
        SELECT
            SUM(a.Total) AS groupTotal,
            a.Description AS groupName
        FROM tblorder_detailshistory a, tblorderhistory b
        WHERE
            b.Outlet_Name = %s
            AND b.Date BETWEEN %s AND %s
            AND a.ItemType = 'Beverage'
            AND a.order_ID = b.idtblorderHistory
        GROUP BY a.Description
        ORDER BY SUM(a.Total) DESC;
        """
        cursor.execute(beverageGrouptotalSql, (outlet, startDate, endDate,))
        beverageGroupResult = cursor.fetchall()
        beverageGroup_json_data = []
        if not beverageGroupResult:
            beverageGroup_json_data.append({"error": "No beverage group data available."})
        else:
            row_headers = [x[0] for x in cursor.description]
            for res in beverageGroupResult:
                beverageGroup_json_data.append(dict(zip(row_headers, res)))

        foodGrouptotalSql = """
        SELECT
            SUM(a.Total) AS groupTotal,
            a.Description AS groupName
        FROM tblorder_detailshistory a, tblorderhistory b
        WHERE
            b.Outlet_Name = %s
            AND b.Date BETWEEN %s AND %s
            AND a.ItemType = 'Food'
            AND a.order_ID = b.idtblorderHistory
        GROUP BY a.Description
        ORDER BY SUM(a.Total) DESC;
        """
        cursor.execute(foodGrouptotalSql, (outlet, startDate, endDate,))
        foodGroupResult = cursor.fetchall()
        foodGroup_json_data = []
        if not foodGroupResult:
            foodGroup_json_data.append({"error": "No food group data available."})
        else:
            row_headers = [x[0] for x in cursor.description]
            for res in foodGroupResult:
                foodGroup_json_data.append(dict(zip(row_headers, res)))

        itemsumDetailsJson = {
            "itemSum": items_sum_json_data,
            "food": items_food_json_data,
            "foodGroup": foodGroup_json_data,
            "beverage": items_beverage_json_data,
            "beverageGroup": beverageGroup_json_data
        }

        split_order_details = {}

        for order_detail in json_data:
            order_id = order_detail["idtblorderhistory"]
            if order_id not in split_order_details:
                split_order_details[order_id] = order_detail
                split_order_details[order_id]["SplitPayments"] = []

        for row in result:
            order_id = row[10]
            payment_mode = row[8] if row[8] is not None else "Unknown"
            if payment_mode == "Split" and order_id in split_order_details:
                payment_amount = float(row[12]) if row[12] is not None else 0.0
                payment_mode = row[11] if row[11] is not None else "Unknown"

                split_order_details[order_id]["SplitPayments"].append({
                    "PaymentMode": payment_mode,
                    "PaymentAmount": payment_amount,
                })

        final_order_details = list(split_order_details.values())

        for order_detail in final_order_details:
            del order_detail["paymentAmountHistory"]
            del order_detail["paymentModeHistory"]

        Stats_json_data[0]["itemDetails"] = itemsumDetailsJson
        Stats_json_data[0]["orderDetails"] = final_order_details
        mydb.close()
        return Stats_json_data[0]
    except Exception as error:
        data = {'error': str(error)}
        return data, 400


