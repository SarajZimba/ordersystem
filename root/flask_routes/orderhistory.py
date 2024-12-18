from flask import Flask, Blueprint,request
app = Flask(__name__)
import mysql.connector
from flask_cors import CORS, cross_origin
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'secret!'
import os
from dotenv import load_dotenv
load_dotenv()
app_file6= Blueprint('app_file6',__name__)
from root.auth.check import token_auth
from datetime import timedelta
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


@app_file6.route("/orderhistory", methods=["POST"])
@cross_origin()
def stats():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        json = request.get_json()
        if "token" not in json  or not any([json["token"]])  or json["token"]=="":
            data = {"error":"No token provided."}
            return data,400
        token = json["token"]
        if not token_auth(token):
            data = {"error":"Invalid token."}
            return data,400
        if "outlet" not in json or "dateStart" not in json or "dateEnd" not in json:
            data = {"error":"Some fields are missing"}
            return data,400
        outlet = json["outlet"]
        startDate = json["dateStart"]
        endDate = json["dateEnd"]
        if not valid_date(startDate) or not valid_date(endDate):
            data={"error":"Invalid date supplied."}
            return data,400
        orderHistory =f"""SELECT CONVERT(TIME(TIMEDIFF(STR_TO_DATE(a.End_Time, '%l:%i %p'),STR_TO_DATE(a.Start_Time, '%l:%i %p'))), CHAR) as duration,a.Outlet_OrderID, DATE_FORMAT(a.Date, "%Y-%m-%d") as Date,a.Table_No,a.NoOfGuests,CONVERT(STR_TO_DATE(a.Start_Time, '%l:%i %p'),CHAR) as Start_Time,a.billPrintTime,CONVERT(STR_TO_DATE(a.End_Time, '%l:%i %p'),CHAR) as End_Time,a.Type,a.Employee as server,a.bill_no,a.Total,a.PaymentMode,a.idtblorderHistory FROM tblorderhistory a,tblorder_detailshistory b where a.idtblorderHistory = b.order_ID and a.Date between %s and %s and a.outlet_Name =%s GROUP BY a.idtblorderHistory order by a.Outlet_OrderID"""
        cursor.execute(orderHistory,(startDate,endDate,outlet,),)
        result = cursor.fetchall()
        if result == []:
            data = {"error":"No data available."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        json_data=[]
        resultJson={}
        for res in result:
            json_data.append(dict(zip(row_headers,res)))
        summaryDetails_Sql=f"""SELECT (SELECT SUM(a.Total-a.serviceCharge-a.VAT)  FROM tblorderhistory a where not a.bill_no='' and a.Date between %s and %s and a.outlet_Name =%s) AS TOTALNETSALES,(SELECT SUM(a.Total) FROM tblorderhistory a where  not a.bill_no='' and a.Date between %s and %s and a.outlet_Name =%s and a.Type='Dine-In') AS TOTALDINEIN,(SELECT SUM(a.Total) FROM tblorderhistory a,tblorder_detailshistory b where a.idtblorderHistory = b.order_ID and a.Date between %s and %s and a.outlet_Name =%s and a.Type='Order') AS TOTALTAB,(SELECT (SUM(a.Total)/ SUM(a.NoOfGuests)) FROM tblorderhistory a,tblorder_detailshistory b where a.idtblorderHistory = b.order_ID and a.Date between %s and %s and a.outlet_Name =%s)AS REVPERGUEST"""
        cursor.execute(summaryDetails_Sql,(startDate,endDate,outlet,startDate,endDate,outlet,startDate,endDate,outlet,startDate,endDate,outlet,),)
        Summaryresult = cursor.fetchall()
        if Summaryresult == []:
            data = {"error":"No data available."}
            return data,400
        row_headers=[x[0] for x in cursor.description] 
        Summaryresult_json=[]
        for res in Summaryresult:
            Summaryresult_json.append(dict(zip(row_headers,res)))
        if not Summaryresult_json[0]["TOTALTAB"]:
            Summaryresult_json[0]["TOTALTAB"]=0
        if not Summaryresult_json[0]["TOTALDINEIN"]:
            Summaryresult_json[0]["TOTALDINEIN"]=0
        guestsSql= f"""SELECT SUM(NoOfGuests) as TOTALGUESTS FROM tblorderhistory  where Date between %s and %s and outlet_Name=%s"""
        cursor.execute(guestsSql,(startDate,endDate,outlet,),)
        GuestSummaryresult = cursor.fetchall()
        row_headers=[x[0] for x in cursor.description] 
        GuestSummaryresult_json=[]
        for res in GuestSummaryresult:
            GuestSummaryresult_json.append(dict(zip(row_headers,res)))
        
        totalsalesjson={"totalNetSales":str(Summaryresult_json[0]["TOTALNETSALES"]),"totalPax":str(GuestSummaryresult_json[0]["TOTALGUESTS"]),"TotalDineIn":str(Summaryresult_json[0]["TOTALDINEIN"]),"PercentDineIn":str(round(100 * float(Summaryresult_json[0]["TOTALDINEIN"])/float(Summaryresult_json[0]["TOTALNETSALES"]),2) ),"PercentTab":str(round(100 * float(Summaryresult_json[0]["TOTALTAB"])/float(Summaryresult_json[0]["TOTALNETSALES"]),2) ),"TotalTab":str(Summaryresult_json[0]["TOTALTAB"]),"RevenuePerGuest":str(Summaryresult_json[0]["TOTALNETSALES"]/GuestSummaryresult_json[0]["TOTALGUESTS"])}
        resultJson["TotalSalesSummary"]=totalsalesjson
        firstorderAt = json_data[0]["Start_Time"]
        lastoderAt = json_data[len(json_data)-1]["Start_Time"]
        lastbillclosedAt = json_data[len(json_data)-1]["End_Time"]
        firstorderDate = json_data[0]["Date"]
        lastoderDate = json_data[len(json_data)-1]["Date"]
        firstTime="{} {}".format(firstorderDate,firstorderAt)
        lastTime="{} {}".format(lastoderDate,lastoderAt)
        operationhourssql = "SELECT TIMESTAMPDIFF(SECOND,'{}','{}') as Operationtime".format(firstTime,lastTime)
        cursor.execute(operationhourssql)
        operationhourresult = cursor.fetchall()
        if operationhourresult == [] or not operationhourresult[0][0]:
            timestatsjson={"firstorderAt":str(firstorderAt),"lastoderAt":str(lastoderAt),"lastbillclosedAt":str(lastbillclosedAt),"firstorderDate":str(firstorderDate),"lastoderDate":str(lastoderDate),"operationTime":"None"}
        else:
            timestatsjson={"firstorderAt":str(firstorderAt),"lastoderAt":str(lastoderAt),"lastbillclosedAt":str(lastbillclosedAt),"firstorderDate":str(firstorderDate),"lastoderDate":str(lastoderDate),"operationTime":str(timedelta(seconds=operationhourresult[0][0]))}
        resultJson["Timestats"]=timestatsjson   
        timesalesstatssql = f"""SELECT (SELECT  count(Total) FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '11:00' AND '15:00') AND Type='Dine-In') AS 1DINEINCOUNT, (SELECT  CONVERT(SUM(Total),CHAR)  FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '11:00' AND '15:00') AND Type='Dine-In') AS 1DINEINTOTAL, (SELECT  count(Total) FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '11:00' AND '15:00') AND Type='Order') AS 1TABCOUNT, (SELECT  CONVERT(SUM(Total),CHAR)  FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '11:00' AND '15:00') AND Type='Order') AS 1TABTOTAL, (SELECT  CONVERT(SUM(Total),CHAR)  FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '11:00' AND '15:00')) AS 1ALLTOTAL,(SELECT  count(Total) FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '11:00' AND '15:00')) AS 1ALLCOUNT, 
                                (SELECT  count(Total) FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '15:01' AND '18:00') AND Type='Dine-In') AS 2DINEINCOUNT, (SELECT CONVERT(SUM(Total),CHAR)  FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '15:01' AND '18:00') AND Type='Dine-In') AS 2DINEINTOTAL, (SELECT  count(Total) FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '15:01' AND '18:00') AND Type='Order') AS 2TABCOUNT, (SELECT  CONVERT(SUM(Total),CHAR)  FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '15:01' AND '18:00') AND Type='Order') AS 2TABTOTAL,  (SELECT  CONVERT(SUM(Total),CHAR)  FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '15:01' AND '18:00') ) AS 2ALLTOTAL,(SELECT  count(Total) FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '15:01' AND '18:00')) AS 2ALLCOUNT,
                                (SELECT  count(Total) FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '18:01' AND '22:00') AND Type='Dine-In') AS 3DINEINCOUNT, (SELECT CONVERT(SUM(Total),CHAR)  FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '18:01' AND '22:00') AND Type='Dine-In') AS 3DINEINTOTAL, (SELECT  count(Total) FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '18:01' AND '22:00') AND Type='Order') AS 3TABCOUNT, (SELECT CONVERT(SUM(Total),CHAR)  FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '18:01' AND '22:00') AND Type='Order') AS 3TABTOTAL ,(SELECT  CONVERT(SUM(Total),CHAR)  FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and (TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '18:01' AND '22:00') ) AS 3ALLTOTAL,(SELECT  count(Total) FROM `tblorderhistory` WHERE Outlet_Name='{outlet}' and Date BETWEEN '{startDate}' and '{endDate}' and(TIME(STR_TO_DATE(Start_Time, '%l:%i %p')) BETWEEN '18:01' AND '22:00')) AS 3ALLCOUNT"""
        cursor.execute(timesalesstatssql)
        timesalesstats = cursor.fetchall()
        row_headers=[x[0] for x in cursor.description] 
        timesalesstats_json=[]
        for res in timesalesstats:
            timesalesstats_json.append(dict(zip(row_headers,res))) 
        timesalesdata = timesalesstats_json[0]
        timesalesjson = {}
        eleven_three_dinein_count = timesalesdata["1DINEINCOUNT"]
        eleven_three_dinein_sales = timesalesdata["1DINEINTOTAL"]
        eleven_three_tab_count = timesalesdata["1TABCOUNT"]
        eleven_three_tab_sales = timesalesdata["1TABTOTAL"]
        eleven_three_total_count = timesalesdata["1ALLCOUNT"]
        eleven_three_total_sales = timesalesdata["1ALLTOTAL"]
        
        
        three_six_dinein_count = timesalesdata["2DINEINCOUNT"]
        three_six_dinein_sales = timesalesdata["2DINEINTOTAL"]
        three_six_tab_count = timesalesdata["2TABCOUNT"]
        three_six_tab_sales = timesalesdata["2TABTOTAL"]
        three_six_total_count = timesalesdata["2ALLCOUNT"]
        three_six_total_sales = timesalesdata["2ALLTOTAL"]
        
        six_ten_dinein_count = timesalesdata["3DINEINCOUNT"]
        six_ten_dinein_sales = timesalesdata["3DINEINTOTAL"]
        six_ten_tab_count = timesalesdata["3TABCOUNT"]
        six_ten_tab_sales = timesalesdata["3TABTOTAL"]
        six_ten_total_count = timesalesdata["3ALLCOUNT"]
        six_ten_total_sales = timesalesdata["3ALLTOTAL"]
        
        
        if eleven_three_total_sales is None:
            eleven_three_total_sales=0
        if three_six_total_sales is None:
            three_six_total_sales=0
        if six_ten_total_sales is None:
            six_ten_total_sales= 0
        totalallsales = float(eleven_three_total_sales) + float(three_six_total_sales) + float(six_ten_total_sales)
        
        if totalallsales ==0:
            eleven_three_pct= 0
            three_six_pct= 0
            six_ten_pct= 0
        if totalallsales !=0:
            eleven_three_pct= str(round(100 * float(eleven_three_total_sales)/float(totalallsales),2) )
            three_six_pct= str(round(100 * float(three_six_total_sales)/float(totalallsales),2) )
            six_ten_pct= str(round(100 * float(six_ten_total_sales)/float(totalallsales),2) )
        
        
        
        timesalesjson["eleven_three"]={"pct":eleven_three_pct,"dinein_count":str(eleven_three_dinein_count),"dinein_sales":str(eleven_three_dinein_sales),"tab_count":str(eleven_three_tab_count),"tab_sales":str(eleven_three_tab_sales),"total_count":str(eleven_three_total_count),"total_sales":str(eleven_three_total_sales)}
        timesalesjson["three_six"]={"pct":three_six_pct,"dinein_count":str(three_six_dinein_count),"dinein_sales":str(three_six_dinein_sales),"tab_count":str(three_six_tab_count),"tab_sales":str(three_six_tab_sales),"total_count":str(three_six_total_count),"total_sales":str(three_six_total_sales)}
        timesalesjson["six_ten"]={"pct":six_ten_pct,"dinein_count":str(six_ten_dinein_count),"dinein_sales":str(six_ten_dinein_sales),"tab_count":str(six_ten_tab_count),"tab_sales":str(six_ten_tab_sales),"total_count":str(six_ten_total_count),"total_sales":str(six_ten_total_sales)}
        
        
        resultJson["Time_sales"]=timesalesjson
        for index,value in enumerate(json_data):
            primaryKey= json_data[index]["idtblorderHistory"]
            getItemSql=f"""SELECT CONCAT(' ',count,' x ',ItemName,',') as item FROM tblorder_detailshistory where order_ID=%s"""
            cursor.execute(getItemSql,(primaryKey,),)
            result = cursor.fetchall()
            if result == []:
                json_data[index]["ItemDetailList"]= {}
            row_headers=[x[0] for x in cursor.description] 
            Itemjson_data=[]
            for res in result:
                Itemjson_data.append(dict(zip(row_headers,res)))  
            itemliststring=""
            for x in Itemjson_data:
                itemliststring = "{}{}".format(itemliststring,x["item"])
            if  len(itemliststring) >0 and  itemliststring[len(itemliststring)-1]=="," and itemliststring!="":
                itemliststring=itemliststring[:len(itemliststring)-1]
            revperguest = json_data[index]["Total"]
            if json_data[index]["Type"] == "Dine-In":
                if int(json_data[index]["NoOfGuests"])==0:
                    revperguest =int(json_data[index]["Total"])
                else:    
                    revperguest = round(int(json_data[index]["Total"])/ int(json_data[index]["NoOfGuests"]),2)
            json_data[index]["revperguest"]= revperguest
            json_data[index]["items"]= itemliststring
        resultJson["table_summary"]= json_data
        mydb.close()
        return resultJson
    except Exception as error:
        data ={'error':str(error)}
        return data,400