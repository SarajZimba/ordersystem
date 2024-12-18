from flask import Flask, Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file11= Blueprint('app_file11',__name__)
from root.auth.check import token_auth



@app_file11.route("/chartsummary", methods=["POST"])
@cross_origin()
def chartsummary():
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
        if "outlet" not in json or "type" not in json :
            data = {"error":"Some fields are missing"}
            return data,400
        outletName = json["outlet"]
        typeSummary = json["type"]
        if typeSummary and typeSummary=="yearly":
            if "date" not in json:
                data = {"error":"Some fields are missing"}
                return data,400
            year = json["date"]
            dailySql = f"""SELECT SUM(Total) as Total,DAYNAME(Date) as dayName from tblorderhistory where Outlet_Name=%s and YEAR(Date)=%s GROUP BY WEEKDAY(Date)"""
            cursor.execute(dailySql,(outletName,year,),)
            dailystatsResult = cursor.fetchall()
            dailyStats_json_data=[]
            monthTotal=[]
            dailyTotal=[]
            dailylabel=[]    
            monthlylabel=[]
            if dailystatsResult == []:
                daily={"error":"No data available."}
                return daily,400
            else:
                row_headers=[x[0] for x in cursor.description] 
                for res in dailystatsResult:
                    dailyStats_json_data.append(dict(zip(row_headers,res)))
                    dailyTotal.append(str(dict(zip(row_headers,res))["Total"]))
                    dailylabel.append(str(dict(zip(row_headers,res))["dayName"]))
                daily=dailyStats_json_data
                dailytotal=dailyTotal
            monthlysql=f"""SELECT SUM(Total) as Total,MONTHNAME(Date) as monthName from tblorderhistory where Outlet_Name=%s and YEAR(Date)=%s GROUP BY MONTH(Date)"""
            cursor.execute(monthlysql,(outletName,year,),)
            monthlystatsResult = cursor.fetchall()
            monthlyStats_json_data=[]
            if monthlystatsResult == []:
                monthly={"error":"No data available."}
                return monthly,400
            else:
                row_headers=[x[0] for x in cursor.description] 
                for res in monthlystatsResult:
                    monthlyStats_json_data.append(dict(zip(row_headers,res)))
                    monthTotal.append(str(dict(zip(row_headers,res))["Total"]))
                    monthlylabel.append(str(dict(zip(row_headers,res))["monthName"]))
                monthly=monthlyStats_json_data 
                monthlytotal=monthTotal
            responseJson={"daily":daily,"dailytotal":dailytotal,"dailylabel":dailylabel,"monthly":monthly,"monthlytotal":monthlytotal,"monthlylabel":monthlylabel}
            mydb.close()
            return responseJson,200
        
        if typeSummary and typeSummary=="weekly":
            if "start_date" not in json or "end_date" not in json:
                data = {"error":"Some fields are missing"}
                return data,400
            startdate = json["start_date"]
            enddate = json["end_date"]
            weeklySql = f"""SELECT SUM(Total) as Total, WEEK(Date) as WeekName from tblorderhistory where Date BETWEEN %s and %s and Outlet_Name=%s GROUP BY WEEK(Date)"""
            cursor.execute(weeklySql,(startdate,enddate,outletName,),)
            weeklystatsResult = cursor.fetchall()
            weeklyStats_json_data=[]
            weekTotal=[]
            weeklabel=[]    
            if weeklystatsResult == []:
                weekly={"error":"No data available."}
                return weekly,400
            else:
                row_headers=[x[0] for x in cursor.description] 
                for res in weeklystatsResult:
                    weeklyStats_json_data.append(dict(zip(row_headers,res)))
                    weekTotal.append(str(dict(zip(row_headers,res))["Total"]))
                    weekname="Week {}".format(str(dict(zip(row_headers,res))["WeekName"]))
                    weeklabel.append(weekname)
                weekly=weeklyStats_json_data
            responseJson={"weekly":weekly,"weeklyTotal":weekTotal,"weeklabel":weeklabel}
            mydb.close()
            return responseJson,200
        
        
        if typeSummary and typeSummary=="monthly":
            if "start_date" not in json or "end_date" not in json:
                data = {"error":"Some fields are missing"}
                return data,400
            startdate = json["start_date"]
            enddate = json["end_date"]
            monthlySql = f"""SELECT SUM(Total) as Total,MONTHNAME(Date) as MonthName from tblorderhistory where Date BETWEEN %s and %s and Outlet_Name=%s GROUP BY MONTH(Date)"""
            cursor.execute(monthlySql,(startdate,enddate,outletName,),)
            monthlystatsResult = cursor.fetchall()
            monthlyStats_json_data=[]
            monthlyTotal=[]
            monthlylabel=[]    
            if monthlystatsResult == []:
                monthly={"error":"No data available."}
                return monthly,400
            else:
                row_headers=[x[0] for x in cursor.description] 
                for res in monthlystatsResult:
                    monthlyStats_json_data.append(dict(zip(row_headers,res)))
                    monthlyTotal.append(str(dict(zip(row_headers,res))["Total"]))
                    monthlylabel.append(str(dict(zip(row_headers,res))["MonthName"]))
                monthly=monthlyStats_json_data
            responseJson={"monthly":monthly,"monthlyTotal":monthlyTotal,"monthlabel":monthlylabel}
            mydb.close()
            return responseJson
        
        
        
        
        
        
        
    except Exception as error:
        data ={'error':str(error)}
        return data,400