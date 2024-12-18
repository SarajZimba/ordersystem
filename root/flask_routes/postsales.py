from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv

load_dotenv()
app_file8 = Blueprint('app_file8', __name__)

@app_file8.route("/postsales", methods=["POST"])
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
        data_list = request.get_json()

        for date_data in data_list:
            # Check if the entry already exists based on the date and Outlet_Name
            cursor.execute(
                "SELECT * FROM tblorderhistory WHERE Date = %s AND Outlet_Name = %s",
                (date_data["date"], date_data["Outlet_Name"])
            )
            existing_entry = cursor.fetchone()

            # If an existing entry is found, skip the insertion for this record
            if existing_entry:
                print(f"Skipping date {date_data['date']} for Outlet {date_data['Outlet_Name']} (already exists).")
                continue

            # Process data if no existing entry
            for data in date_data["data"]:
                sql = """INSERT INTO tblorderhistory (Outlet_OrderID, Employee, Table_No, NoOfGuests, Start_Time, End_Time, State, Type, Discounts, Date, bill_no, Total, serviceCharge, VAT, DiscountAmt, PaymentMode, fiscal_year, GuestName, Outlet_Name, billPrintTime, guestID, guestEmail, guestPhone, guestAddress) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                sql2 = """INSERT INTO tblorder_detailshistory (order_ID, ItemName, itemRate, Total, ItemType, Description, discountExempt, count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

                # Insert data into tblorderhistory
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
                    "SELECT idtblorderhistory FROM tblorderhistory ORDER BY idtblorderhistory DESC LIMIT 1;"
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

                # Insert items into tblorder_detailshistory
                for item_data in data["ItemDetailsList"]:
                    item_sql_data = (
                        order_history_id,
                        item_data["itemName"],
                        item_data["ItemRate"],
                        item_data["total"],
                        item_data["ItemType"],
                        item_data["Description"],
                        item_data["disExempt"],
                        item_data["count"],
                    )
                    try:
                        cursor.execute(sql2, item_sql_data)
                        mydb.commit()
                    except Exception as e:
                        print(f"Error inserting item details: {str(e)}")
                        continue

        mydb.close()
        return {"success": "Data processed successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 500
