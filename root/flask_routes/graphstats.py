from flask import  Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file21= Blueprint('app_file21',__name__)
from root.auth.check import token_auth
import re



@app_file21.route("/datestats", methods=["POST"])
@cross_origin()
def graphstats():
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
        if  "Outlet_Name" not in json or "start_date" not in json or "end_date" not in json:
            data = {"error":"Some fields are missing"}
            return data,400
        startDate = json["start_date"]
        Outlet_Name = json["Outlet_Name"]
        endDate = json["end_date"]
        datestatsSql=f"""SELECT  sum(Total) as data,DAYNAME(Date) as label ,Date as id  from tblorderhistory where Outlet_Name=%s and Date BETWEEN %s and %s  and bill_no!='' group by  Date  """
        cursor.execute(datestatsSql,(Outlet_Name,startDate,endDate),)
        dailystatsResult = cursor.fetchall()
        dailyStats_json_data=[]
        if dailystatsResult == []:
            data = {"error":"No data available."}
            return data,400
        labels=[]
        idlabels=[]
        daylist=[]
        row_headers=[x[0] for x in cursor.description] 
        for res in dailystatsResult:
            totalPrice=str(dict(zip(row_headers,res))["data"])
            labels.append(totalPrice) 
            day=str(dict(zip(row_headers,res))["label"])
            daylist.append(day) 
            
            
            dateString = re.sub(' 00:00:00 GMT',"", str(dict(zip(row_headers,res))["id"]))
            idlabels.append(dateString)
            dailyStats_json_data.append(dict(zip(row_headers,res)))
            
        try:
            #newlabels=  sorted(labels, key = lambda x:float(x))
            statsjson = {"daylist":daylist,"labels":idlabels,"total":labels,"datasets":dailyStats_json_data}
        except Exception as error:
            statsjson = {"daylist":daylist,"labels":idlabels,"total":labels,"datasets":dailyStats_json_data}

            
        
        mydb.close()
        return statsjson,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400