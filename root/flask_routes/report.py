from flask import request, Blueprint
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
app_file1 = Blueprint('app_file1',__name__)
import re
import time
import math
from root.auth.check import token_auth




@app_file1.route("/report", methods=["POST"])
@cross_origin()
def report():
    mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
    cursor = mydb.cursor(buffered=True)
    database_sql = "USE {};".format(os.getenv('database'))
    cursor.execute(database_sql)
    json = request.get_json()
    if "token" not in json or "end_date" not in json or "start_date" not in json or "outlet_name" not in json or "page_no" not in json or not any([json["token"],json["end_date"],json["start_date"],json["outlet_name"],json["page_no"]]) or json["token"]=="" or json["start_date"] =="" or json["end_date"] =="" or json["outlet_name"]=="" or json["page_no"]=="":
        data = {"error":"Some fields missing."}
        return data,400
    else:
        if json["page_no"] <1:
            data = {"error":"Page must start with one."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400
        try:
            start_date = json["start_date"]
            end_date = json["end_date"]
            outlet = json["outlet_name"]
            page_no = json["page_no"]
            sql =f"""select currentState,DATE_FORMAT(Date,'%Y/%m/%d')as Date,orderedAt,Guest_count,outlet_orderID,tableNum,TotalTime,Employee,idtblorderTracker,orderType,KOTID from tblorderTracker where outlet_Name=%s and Date >= %s and Date <=%s and (currentState='Completed' or currentState='void') order by idtblorderTracker desc"""
            cursor.execute(sql,(outlet,start_date,end_date,),)
            result = cursor.fetchall()
            if result == []:
                data = {"error":"No such entry with outletname and date."}
                return data,400
            row_headers=[x[0] for x in cursor.description] 
            json_data=[]
            response_json = {}
            for res in result:
                json_data.append(dict(zip(row_headers,res)))
            dinein=0
            takeaway=0
            voids=0
            cooked=0
            total_guests = 0
            takeaway_total =0.00
            dinein_total=0.00
            for index,key in enumerate(json_data):
                order_number = json_data[index]["idtblorderTracker"]
                orderType = json_data[index]["orderType"]
                Employee= json_data[index]["Employee"]
                TotalTime= json_data[index]["TotalTime"]
                tableNum= json_data[index]["tableNum"]
                Guests= json_data[index]["Guest_count"]
                orderedAt= json_data[index]["orderedAt"]
                Date=json_data[index]["Date"]
                kotid = json_data[index]["KOTID"]
                currentState = json_data[index]["currentState"]
                if Guests:
                    total_guests +=Guests
                outlet_orderID= json_data[index]["outlet_orderID"]
                item_sql =f"""select Quantity,ItemName,orderedAt,completedAt,TotalTime,AvgPrepTime,prepTimeDifference,item_price,voidAt,voidTotalTime from tblorderTracker_Details where orderTrackerID=%s and not completedAt=''"""
                cursor.execute(item_sql,(order_number,),)
                item_result = cursor.fetchall()
                if currentState !="void" and orderType =="Dine-In":
                    dinein +=1
                elif currentState !="void" and orderType =="Take-Away":
                    takeaway +=1
                if item_result == []:
                    data= {"error":"There is an error with your item entry."}
                    return data,400
                row_headers=[x[0] for x in cursor.description] 
                item_json_data=[]
                for res in item_result:
                    item_json_data.append(dict(zip(row_headers,res)))
                if currentState =="void":
                    temp_item_json = {"Date":Date,"OrderedAt":orderedAt,"Outlet_orderID":outlet_orderID,"items":item_json_data,"TableNum":str(tableNum),"TotalTime":"Canceled","OrderType":orderType,"Employee":Employee,"KOTID":kotid}
                elif currentState !="void":   
                    temp_item_json = {"Date":Date,"OrderedAt":orderedAt,"Outlet_orderID":outlet_orderID,"items":item_json_data,"TableNum":str(tableNum),"TotalTime":TotalTime,"OrderType":orderType,"Employee":Employee,"KOTID":kotid}
                for z in range(len(item_json_data)):
                    if TotalTime !="void" and orderType =="Dine-In" and not item_json_data[z]["completedAt"] =="void":
                        if item_json_data[z]["item_price"] is not None and item_json_data[z]["item_price"] !="":
                            dinein_total += float(item_json_data[z]["item_price"])
                    elif TotalTime !="void" and orderType =="Take-Away"  and not item_json_data[z]["completedAt"] =="void":
                        if item_json_data[z]["item_price"] is not None and item_json_data[z]["item_price"] !="":
                            takeaway_total += float(item_json_data[z]["item_price"])
                    if item_json_data[z]["completedAt"] =="void":
                        item_json_data[z]["completedAt"]=item_json_data[z]["voidAt"]
                    if item_json_data[z]["TotalTime"]=="void":
                        item_json_data[z]["TotalTime"]=item_json_data[z]["voidTotalTime"]
                response_json.setdefault("orders",[]).append(temp_item_json)
            n = page_no
            first_index= (5 * n) -5
            second_index = 5 * n
            orders_per_page = 5
            max_page_length = math.ceil(len(response_json["orders"])/orders_per_page)
            if page_no>max_page_length:
                data={"error":"Max page number exceeded. Page number cannot be more than {}.".format(max_page_length)}
                return data,400
            takeaway_total= round(takeaway_total,2)
            dinein_total = round(dinein_total,2)
            response_json["DineIn"]=dinein
            response_json["TakeAway"]=takeaway
            response_json["Guest_count"]=total_guests
            response_json["TakeAway_totalSales"]=takeaway_total
            response_json["DineIn_totalSales"]=dinein_total
            first_orderAt = response_json["orders"][0]["OrderedAt"]
            first_orderDate=str(response_json["orders"][0]["Date"])
            last_orderAt= response_json["orders"][len(response_json["orders"])-1]["OrderedAt"]
            last_orderDate= str(response_json["orders"][len(response_json["orders"])-1]["Date"])
            first_orderDate = re.sub("/","-",first_orderDate)
            last_orderDate = re.sub("/","-",last_orderDate)
            first_date_time_str = '{} {}'.format(first_orderDate,first_orderAt)
            op_start = datetime.strptime(first_date_time_str,'%Y-%m-%d %H:%M:%S')
            last_date_time_str = '{} {}'.format(last_orderDate,last_orderAt)
            op_end = datetime.strptime(last_date_time_str,'%Y-%m-%d %H:%M:%S')
            operating_time = op_start-op_end
            operating_seconds = operating_time.total_seconds()
            operating_time = time.strftime('%H:%M:%S', time.gmtime(operating_seconds))
            op_hours = re.sub("-","",str(round(operating_seconds/3600,2)))
            op_hours_elapsed= "{}".format(op_hours)
            response_json["first_orderAt"]=first_orderAt
            response_json["last_orderAt"]=last_orderAt
            response_json["Operating_hours"]=op_hours_elapsed
            response_json["maxPage_Length"]=max_page_length
            response_json["orders"]=response_json["orders"][first_index:second_index]
            cooking_sql =f"""select count(idtblorderTracker) as cooking_no from tblorderTracker where outlet_Name=%s and Date >=%s and Date <=%s and currentState='Cooking'"""
            cursor.execute(cooking_sql,(outlet,start_date,end_date,),)
            result = cursor.fetchall()
            row_headers=[x[0] for x in cursor.description] 
            cooking_json_data=[]
            for res in result:
                cooking_json_data.append(dict(zip(row_headers,res)))
            cooking_count=0
            if result !=[]:
                cooking_count = cooking_json_data[0]["cooking_no"]
            response_json["cooking"]=cooking_count
            voids=0
            cooked=0
            totalsum=0
            cookedvoidsSql = f"""SELECT (SELECT sum(b.Quantity) FROM tblorderTracker a, tblorderTracker_Details b where a.idtblorderTracker = b.orderTrackerID and a.outlet_Name=%s and a.Date >=%s and a.Date <=%s and not b.completedAt='' and not b.completedAt='void') as cooked, (SELECT sum(b.Quantity) FROM tblorderTracker a, tblorderTracker_Details b where a.idtblorderTracker = b.orderTrackerID and a.outlet_Name=%s and a.Date >=%s and a.Date <=%s and b.completedAt='void') as voids"""
            cursor.execute(cookedvoidsSql,(outlet,start_date,end_date,outlet,start_date,end_date,),)
            cookvoidresult = cursor.fetchall()
            row_headers=[x[0] for x in cursor.description] 
            cookedvoid_json_data=[]
            for res in cookvoidresult:
                cookedvoid_json_data.append(dict(zip(row_headers,res)))
            if cookvoidresult ==[]:
                cooked = 0
                voids=0
                totalsum=0
            else:
                cooked = cookedvoid_json_data[0]["cooked"]
                voids=cookedvoid_json_data[0]["voids"]
                totalsum=cookedvoid_json_data[0]["cooked"]
            response_json["Voids"]=voids
            response_json["Cooked"]=cooked
            response_json["item_count"]=totalsum
            A = response_json["orders"]
            B = []
            def find(uid, id_):
                for i, d in enumerate(B):
                    if d['Outlet_orderID'] == uid and d['Date'] == id_:
                        return i
                return -1
            for d in A:
                if (i := find(d['Outlet_orderID'], d['Date'])) < 0:
                    B.append(d)
                else:
                    for x in d["items"]:
                        B[i]['items'].append(x)
            response_json["orders"] = B
            mydb.close()
            return response_json
        except Exception as error:
            data ={'error':str(error)}
            return data,400

