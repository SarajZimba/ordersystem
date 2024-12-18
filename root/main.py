# changes
from flask import Flask, request, Blueprint
import mysql.connector
from flask_cors import CORS, cross_origin
import os
from dotenv import load_dotenv
import datetime

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
load_dotenv()

# Import your other blueprints here
from root.flask_routes.report import app_file1
from root.flask_routes.outletnames import app_file2
from root.flask_routes.login import app_file4
from root.flask_routes.orderhistory import app_file6
from root.flask_routes.salesreport import app_file7
from root.flask_routes.postsales import app_file8
from root.flask_routes.deletesales import app_file9
from root.flask_routes.statsummary import app_file10
from root.flask_routes.chartsummary import app_file11
from root.flask_routes.customersaleshistory import app_file18
from root.flask_routes.billinfo import app_file19
from root.flask_routes.customerComplimentary import app_file20
from root.flask_routes.graphstats import app_file21
from root.flask_routes.years import app_file22
from root.flask_routes.billsearch import app_file23
from root.flask_routes.customercredit import app_file24
from root.flask_routes.CustomerCreditInsert import app_file25
from root.flask_routes.customerCreditdetails import app_file26
from root.flask_routes.purchasereq import app_file12
from root.flask_routes.reqget import app_file13
from root.flask_routes.reqdetails import app_file14
from root.flask_routes.reqfilter import app_file15
from root.flask_routes.reqfilterfirst import app_file16
from root.flask_routes.reqitemhistory import app_file17
from root.flask_routes.customerCreditcheck import app_file27
from root.flask_routes.customerCreditleft import app_file28
from root.flask_routes.itemsaledatewise import app_file29
from root.flask_routes.item_lists import app_file30
from root.flask_routes.groupsaledatewise import app_file31
from root.flask_routes.group_lists import app_file32
from root.flask_routes.itemdiscountsaledatewise import app_file33
from root.flask_routes.discountsitemsalesdatewise import app_file34
from root.flask_routes.discountslists import app_file35
from root.flask_routes.hourlysales import app_file36
from root.flask_routes.hourlysales_specifictimedata import app_file37
from root.flask_routes.register import app_file38 
from root.flask_routes.agentlogin import app_file39 
from root.flask_routes.userlists import app_file40
from root.flask_routes.deleteuser import app_file41
from root.flask_routes.postmenu import app_file42
from root.flask_routes.updateuser import app_file43
from root.flask_routes.customer import app_file77
from root.flask_routes.analyticsreport import app_file44
from root.flask_routes.salesofcustomeroutletwise import app_file45
from root.flask_routes.customerlists import app_file46
from root.flask_routes.postredeemeditemsfromcustomer import app_file47
from root.flask_routes.postcustomerPointAccumulation import app_file48
from root.flask_routes.redeemptionAccumulation import app_file49
from root.flask_routes.getredeemeditemsfromcustomer import app_file50
from root.flask_routes.customeraccumulation import app_file51
from root.flask_routes.customerlistRedeemption import app_file52
from root.flask_routes.customerlistAccumulation import app_file53
from root.flask_routes.getcustomeraccumulationpoints import app_file54
from root.flask_routes.getredeemptionaccumulationhistory import app_file55
from root.flask_routes.timeintervalcomparisionsales import app_file56
from root.flask_routes.postsales_old import app_file57
from root.flask_routes.monthlyprojectionsales import app_file58








# Register your other blueprints here
app.register_blueprint(app_file1)
app.register_blueprint(app_file2)
app.register_blueprint(app_file4)
app.register_blueprint(app_file6)
app.register_blueprint(app_file7)
app.register_blueprint(app_file8)
app.register_blueprint(app_file9)
app.register_blueprint(app_file10)
app.register_blueprint(app_file11)
app.register_blueprint(app_file12)
app.register_blueprint(app_file13)
app.register_blueprint(app_file14)
app.register_blueprint(app_file15)
app.register_blueprint(app_file16)
app.register_blueprint(app_file17)
app.register_blueprint(app_file18)
app.register_blueprint(app_file19)
app.register_blueprint(app_file20)
app.register_blueprint(app_file21)
app.register_blueprint(app_file22)
app.register_blueprint(app_file23)
app.register_blueprint(app_file24)
app.register_blueprint(app_file25)
app.register_blueprint(app_file26)
app.register_blueprint(app_file27)
app.register_blueprint(app_file28)
app.register_blueprint(app_file29)
app.register_blueprint(app_file30)
app.register_blueprint(app_file31)
app.register_blueprint(app_file32)
app.register_blueprint(app_file33)
app.register_blueprint(app_file34)
app.register_blueprint(app_file35)
app.register_blueprint(app_file36)
app.register_blueprint(app_file37)
app.register_blueprint(app_file38)
app.register_blueprint(app_file39)
app.register_blueprint(app_file40)
app.register_blueprint(app_file41)
app.register_blueprint(app_file42)
app.register_blueprint(app_file43)
app.register_blueprint(app_file44)
app.register_blueprint(app_file45)
app.register_blueprint(app_file46)
app.register_blueprint(app_file47)
app.register_blueprint(app_file48)
app.register_blueprint(app_file49)
app.register_blueprint(app_file50)
app.register_blueprint(app_file51)
app.register_blueprint(app_file52)
app.register_blueprint(app_file53)
app.register_blueprint(app_file54)
app.register_blueprint(app_file55)
app.register_blueprint(app_file56)
app.register_blueprint(app_file57)
app.register_blueprint(app_file58)

app.register_blueprint(app_file77)


@app.route("/entry1", methods=["POST"])
@cross_origin()
def entry1():
    mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
    cursor = mydb.cursor(buffered=True)
    database_sql = "USE {};".format(os.getenv('database'))
    cursor.execute(database_sql)
    json_data_list = request.get_json()

    if not isinstance(json_data_list, list):
        return {"error": "Expected a list of orders."}, 400

    try:
        for json_data in json_data_list:
            perm_outlet_orderID = json_data["outlet_orderID"]
            perm_orderTime = json_data["orderTime"]
            perm_completedAt = json_data["completedAt"]
            perm_totalTime = json_data["TotalTime"]
            perm_tableNum = json_data["tableNum"]
            perm_employee = json_data["employee"]
            perm_orderType = json_data["orderType"]
            perm_currentState = json_data["currentState"]
            perm_outlet_Name = json_data["outlet_Name"]
            perm_guests = json_data["Guest_count"]
            perm_OrderItemDetailsList = json_data["OrderItemDetailsList"]
            perm_kotid = json_data["KOTID"]
            date = datetime.date.today().strftime('%Y-%m-%d')

            try:
                # Insert main order details into tblorderTracker
                sql_order_tracker = """INSERT INTO tblorderTracker (outlet_orderID, Date, tableNum, orderedAt, completedAt, TotalTime, orderType, currentState, Quantity, outlet_Name, Employee, Guest_count, KOTID)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql_order_tracker, (perm_outlet_orderID, date, perm_tableNum, perm_orderTime, perm_completedAt, perm_totalTime, perm_orderType, perm_currentState, perm_guests, perm_outlet_Name, perm_employee, perm_guests, perm_kotid))
                mydb.commit()

                # Get the ID of the inserted order
                order_id = cursor.lastrowid

                # Insert each item detail into tblorderTracker_Details
                for item_details in perm_OrderItemDetailsList:
                    item_name = item_details["ItemName"]
                    item_quantity = item_details["Quantity"]
                    item_modifications = item_details.get("Modifications", "")
                    item_prep_time = item_details.get("AveragePrepTime", "")
                    item_price = item_details["item_price"]
                    item_category = item_details["category"]
                    item_completedAt = item_details["completedAt"]
                    item_totalTime = item_details["TotalTime"]
                    item_prepTime = item_details["prepTimeDifference"]
                    # item_voidAt = item_details["voidAt"]
                    # item_voidTotalTime = item_details["voidTotalTime"]

                    if "voidAt" in item_details and "voidTotalTime" in item_details:
                        item_voidAt = item_details["voidAt"]
                        item_voidTotalTime = item_details["voidTotalTime"]
                    else:
                        item_voidAt = None  # If not present, set to None
                        item_voidTotalTime = None

                    sql_item_details = """INSERT INTO tblorderTracker_Details (orderedAt, completedAt, TotalTime, ItemName, Quantity, Modification, AvgPrepTime, item_price, category, orderTrackerID, prepTimeDifference, voidAt, voidTotalTime)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    cursor.execute(sql_item_details, (perm_orderTime, item_completedAt, item_totalTime, item_name, item_quantity, item_modifications, item_prep_time, item_price, item_category, order_id, item_prepTime, item_voidAt, item_voidTotalTime))
                    mydb.commit()
            except Exception as e:
                return {"error": str(error)}, 400

        cursor.close()
        mydb.close()

        return json_data_list, 200  # Return a success response

    except Exception as error:
        data = {'error': str(error)}
        return data, 400  # Return an error response


@app.route("/entry", methods=["POST"])
@cross_origin()
def entry():
    mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
    cursor = mydb.cursor(buffered=True)
    database_sql = "USE {};".format(os.getenv('database'))
    cursor.execute(database_sql)
    json_data = request.get_json()
    
    perm_outlet_orderID = json_data["outlet_orderID"]
    perm_orderTime = json_data["orderTime"]
    perm_completedAt = json_data["completedAt"]
    perm_totalTime = json_data["TotalTime"]
    perm_tableNum = json_data["tableNum"]
    perm_employee = json_data["employee"]
    perm_orderType = json_data["orderType"]
    perm_currentState = json_data["currentState"]
    perm_outlet_Name = json_data["outlet_Name"]
    perm_guests = json_data["Guest_count"]
    perm_OrderItemDetailsList = json_data["OrderItemDetailsList"]
    perm_kotid = json_data["KOTID"]
    date = datetime.date.today().strftime('%Y-%m-%d')

    try:
        # Insert main order details into tblorderTracker
        sql_order_tracker = """INSERT INTO tblorderTracker (outlet_orderID, Date, tableNum, orderedAt, completedAt, TotalTime, orderType, currentState, Quantity, outlet_Name, Employee, Guest_count, KOTID)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql_order_tracker, (perm_outlet_orderID, date, perm_tableNum, perm_orderTime, perm_completedAt, perm_totalTime, perm_orderType, perm_currentState, perm_guests, perm_outlet_Name, perm_employee, perm_guests, perm_kotid))
        mydb.commit()

        # Get the ID of the inserted order
        order_id = cursor.lastrowid

        # Insert each item detail into tblorderTracker_Details
        for item_details in perm_OrderItemDetailsList:
            item_name = item_details["ItemName"]
            item_quantity = item_details["Quantity"]
            item_modifications = item_details.get("Modifications", "")
            item_prep_time = item_details.get("AveragePrepTime", "")
            item_price = item_details["item_price"]
            item_category = item_details["category"]
            item_completedAt = item_details["completedAt"]
            item_totalTime = item_details["TotalTime"]
            item_prepTime = item_details["prepTimeDifference"]

            sql_item_details = """INSERT INTO tblorderTracker_Details (orderedAt, completedAt, TotalTime, ItemName, Quantity, Modification, AvgPrepTime, item_price, category, orderTrackerID, prepTimeDifference)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql_item_details, (perm_orderTime, item_completedAt, item_totalTime, item_name, item_quantity, item_modifications, item_prep_time, item_price, item_category, order_id, item_prepTime))
            mydb.commit()

        cursor.close()
        mydb.close()

        return json_data, 200  # Return a success response

    except Exception as error:
        data = {'error': str(error)}
        return data, 400  # Return an error response

@app.route("/")
def index():
    return " it is working"

if __name__ == "__main__":
    app.run(debug=True)



