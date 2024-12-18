from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from .utils import post_sales_and_create_journal, post_sales_and_create_journal_for_creditbills
load_dotenv()
app_file57 = Blueprint('app_file57', __name__)

@app_file57.route("/postsales_old", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database')
        )
        cursor = mydb.cursor(buffered=True)
        data = request.get_json()
        initial_data = data

        # Check if the entry already exists based on the date and Outlet_Name
        cursor.execute(
                "SELECT * FROM tblorderhistory WHERE Date = %s AND  Outlet_OrderID = %s",
                (data["date"], data["OrderID"])
        )
        existing_entry = cursor.fetchone()

        # If an existing entry is found, skip the insertion for this record
        if existing_entry:
            # print(f"Skipping date {data['date']} for Outlet {data['Outlet_Name']} (already exists).")
            return({"data": f"Skipping date {data['date']} for Outlet {data['OrderID']} (already exists)."}, 400)

        # Insert data into tblorderhistory
        sql = """INSERT INTO tblorderhistory (Outlet_OrderID, Employee, Table_No, NoOfGuests, Start_Time, End_Time, State, Type, Discounts, Date, bill_no, Total, serviceCharge, VAT, DiscountAmt, PaymentMode, fiscal_year, GuestName, Outlet_Name, billPrintTime, guestID, guestEmail, guestPhone, guestAddress) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        sql2 = f"""INSERT INTO tblorder_detailshistory (order_ID,ItemName,itemRate,Total,ItemType,Description,discountExempt,count)VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"""

        cursor.execute(
            sql,
            (
                data["OrderID"],
                data["Employee"],
                data["TableNo"],
                data["noofGuest"],
                data["start_Time"],
                data["end_Time"],
                data["state"],
                data["type"],
                data["discounts"],
                data["date"],
                data["bill_No"],
                data["Total"],
                data["serviceCharge"],
                data["VAT"],
                data["discountAmt"],
                data["paymentMode"],
                data["fiscal_Year"],
                data["GuestName"],
                data["Outlet_Name"],
                data["billPrintTime"],
                data["guestID"],
                data["guestEmail"],
                data["guestPhone"],
                data["guestAddress"],
            ),
        )
        mydb.commit()

        # Check if the payment mode is 'Credit' and insert into CreditHistory
        if data["paymentMode"] == 'Credit':
            credit_sql = """INSERT INTO CreditHistory (`outetName`, `Date`, `customerName`, `guestID`, `creditState`, `Outlet_OrderID`) VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(
                credit_sql,
                (data["Outlet_Name"], data["date"], data["GuestName"], data["guestID"], 'InitialEntry', data["OrderID"]),
            )
            mydb.commit()

        # Get the last inserted order ID from tblorderhistory
        cursor.execute(
            f"SELECT idtblorderhistory FROM tblorderhistory ORDER BY idtblorderhistory DESC LIMIT 1;"
        )
        order_history_id = cursor.fetchone()[0]

        # Insert payment data into payment_history for each payment
        for payment_data in data.get("SplitPaymentDetailsList", []):
            payment_sql = """INSERT INTO payment_history (bill_No, paymentMode, paymentAmount, orderHistoryid, FiscalYear) VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(
                payment_sql,
                (
                    data["bill_No"],
                    payment_data["paymentMode"],
                    payment_data["paymentAmount"],
                    order_history_id,
                    data["fiscal_Year"],
                ),
            )
            mydb.commit()

        cursor.execute(
        f"SELECT idtblorderhistory FROM tblorderhistory order by idtblorderhistory desc limit 1;"
        )
        id = cursor.fetchall()
        for data in data["ItemDetailsList"]:
            data["orderID"] = id[0][0]
            listdata = (
            data["orderID"],
            data["itemName"],
            data["ItemRate"],
            data["total"],
            data["ItemType"],
            data["Description"],
            data["disExempt"],
            data["count"],
            )
            try:
                cursor.execute(sql2, listdata)
                mydb.commit()
            except Exception as e:
                data={"error":str(e)}
                return data,400
        print("FUnction to be called")

        if initial_data["paymentMode"] != "Credit":
            post_sales_and_create_journal(initial_data)

        else:
            post_sales_and_create_journal_for_creditbills(initial_data)
        print("FUnction called")
        mydb.close()
        data = {"success": "Data posted successfully"}
        return data
    except Exception as error:
        data = {'error': str(error)}
        return data, 400