from flask import  Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file28 = Blueprint('app_file28',__name__)
from root.auth.check import token_auth
import ast

@app_file28.route("/customerCreditleft", methods=["POST"])
@cross_origin()
def CustomerCreditLeft():
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
        if not "outlet" in json or json["outlet"]=="" or not "type" in json or json["type"]=="":
            data= {"error":"Missing parameters."}
            return data,400
        if json["type"]=='All':
            
            guestIDsql=f"""SELECT DISTINCT guestID,GuestName from tblorderhistory where PaymentMode='Credit' and guestID!=''  and Outlet_Name=%s"""
            cursor.execute(guestIDsql,(json["outlet"],),)
            result = cursor.fetchall()
            if result == []:
                data = {"error":"No data available."}
                return data,400
            row_headers=[x[0] for x in cursor.description] 
            GuestIDjson=[]
            for res in result:
                GuestIDjson.append(dict(zip(row_headers,res)))
            json_data=[]
            for x in GuestIDjson:
                guestID=x["guestID"]
                creditSummaryDetailsSql=f"""Select (SELECT sum(Amount)  FROM CreditHistory where creditState='Payment'  and outetName=%s and guestID=%s) as AmountPaid,(SELECT sum(Total)   FROM tblorderhistory where PaymentMode='Credit'   and Outlet_Name=%s and guestID=%s) as  TotalCredit, (Select TotalCredit- AmountPaid  ) as amountleft"""
                cursor.execute(creditSummaryDetailsSql,(json["outlet"],guestID,json["outlet"],guestID,),)
                result = cursor.fetchall()
                row_headers=[x[0] for x in cursor.description] 
                creditSummaryjson=[]
                for res in result:
                    creditSummaryjson.append(dict(zip(row_headers,res)))
                try:
                    if float(creditSummaryjson[0]["amountleft"]) >0:
                        creditSummaryPersonalDetailsSql=f"""Select(SELECT guestAddress from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1 ) as guestAddress,(SELECT guestPhone from tblorderhistory where  Outlet_Name=%s and guestID=%s limit 1) as guestPhone,(SELECT guestEmail from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guestEmail,(SELECT guestID from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guestID,(SELECT GuestName from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guest"""
                        cursor.execute(creditSummaryPersonalDetailsSql,(json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,),)
                        privateSummaryDetails = cursor.fetchall()
                        row_headers2=[x[0] for x in cursor.description] 
                        creditSummaryPrivatejson=[]
                        for x in privateSummaryDetails:
                            creditSummaryPrivatejson.append(dict(zip(row_headers2,x)))
                        jsondataObject={"guestPhone":creditSummaryPrivatejson[0]["guestPhone"],"guestID":creditSummaryPrivatejson[0]["guestID"],"guestEmail":creditSummaryPrivatejson[0]["guestEmail"],"guestAddress":creditSummaryPrivatejson[0]["guestAddress"],"guest":creditSummaryPrivatejson[0]["guest"],"AmountPaid":creditSummaryjson[0]["AmountPaid"],"TotalCredit":creditSummaryjson[0]["TotalCredit"],"amountleft":creditSummaryjson[0]["amountleft"]}
                        json_data.append(jsondataObject)
                except Exception as error:
                    if not creditSummaryjson[0]["amountleft"]:
                        creditSummaryjson[0]["amountleft"]=creditSummaryjson[0]["TotalCredit"]
                    creditSummaryPersonalDetailsSql=f"""Select(SELECT guestAddress from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1 ) as guestAddress,(SELECT guestPhone from tblorderhistory where  Outlet_Name=%s and guestID=%s limit 1) as guestPhone,(SELECT guestEmail from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guestEmail,(SELECT guestID from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guestID,(SELECT GuestName from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guest"""
                    cursor.execute(creditSummaryPersonalDetailsSql,(json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,),)
                    privateSummaryDetails = cursor.fetchall()
                    row_headers2=[x[0] for x in cursor.description] 
                    creditSummaryPrivatejson=[]
                    for x in privateSummaryDetails:
                        creditSummaryPrivatejson.append(dict(zip(row_headers2,x)))
                    jsondataObject={"guestPhone":creditSummaryPrivatejson[0]["guestPhone"],"guestID":creditSummaryPrivatejson[0]["guestID"],"guestEmail":creditSummaryPrivatejson[0]["guestEmail"],"guestAddress":creditSummaryPrivatejson[0]["guestAddress"],"guest":creditSummaryPrivatejson[0]["guest"],"AmountPaid":creditSummaryjson[0]["AmountPaid"],"TotalCredit":creditSummaryjson[0]["TotalCredit"],"amountleft":creditSummaryjson[0]["amountleft"]}
                    json_data.append(jsondataObject)

            

            mydb.commit()
            mydb.close()
            return json_data,200
        if json["type"]=='Ranged':
            
            if not "dateStart" in json or json["dateStart"]=="" or  not "dateEnd" in json or json["dateEnd"]=="" :
                data= {"error":"Missing parameters."}
                return data,400
            
            guestIDsql=f"""SELECT DISTINCT guestID,GuestName from tblorderhistory where PaymentMode='Credit' and guestID!=''  and Outlet_Name=%s and Date BETWEEN %s and %s"""
            cursor.execute(guestIDsql,(json["outlet"], json["dateStart"], json["dateEnd"],),)
            result = cursor.fetchall()
            if result == []:
                data = {"error":"No data available."}
                return data,400
            row_headers=[x[0] for x in cursor.description] 
            GuestIDjson=[]
            for res in result:
                GuestIDjson.append(dict(zip(row_headers,res)))
            json_data=[]
            for x in GuestIDjson:
                guestID=x["guestID"]
                creditSummaryDetailsSql=f"""Select (SELECT sum(Amount)  FROM CreditHistory where creditState='Payment'  and outetName=%s and guestID=%s and Date BETWEEN %s and %s) as AmountPaid,(SELECT sum(Total)   FROM tblorderhistory where PaymentMode='Credit'   and Outlet_Name=%s and guestID=%s and Date BETWEEN %s and %s) as  TotalCredit, (Select TotalCredit- AmountPaid  ) as amountleft"""
                cursor.execute(creditSummaryDetailsSql,(json["outlet"],guestID, json["dateStart"], json["dateEnd"],json["outlet"],guestID, json["dateStart"], json["dateEnd"],),)
                result = cursor.fetchall()
                row_headers=[x[0] for x in cursor.description] 
                creditSummaryjson=[]
                for res in result:
                    creditSummaryjson.append(dict(zip(row_headers,res)))
                try:
                    if float(creditSummaryjson[0]["amountleft"]) >0:
                        creditSummaryPersonalDetailsSql=f"""Select(SELECT guestAddress from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1 ) as guestAddress,(SELECT guestPhone from tblorderhistory where  Outlet_Name=%s and guestID=%s limit 1) as guestPhone,(SELECT guestEmail from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guestEmail,(SELECT guestID from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guestID,(SELECT GuestName from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guest"""
                        cursor.execute(creditSummaryPersonalDetailsSql,(json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,),)
                        privateSummaryDetails = cursor.fetchall()
                        row_headers2=[x[0] for x in cursor.description] 
                        creditSummaryPrivatejson=[]
                        for x in privateSummaryDetails:
                            creditSummaryPrivatejson.append(dict(zip(row_headers2,x)))
                        jsondataObject={"guestPhone":creditSummaryPrivatejson[0]["guestPhone"],"guestID":creditSummaryPrivatejson[0]["guestID"],"guestEmail":creditSummaryPrivatejson[0]["guestEmail"],"guestAddress":creditSummaryPrivatejson[0]["guestAddress"],"guest":creditSummaryPrivatejson[0]["guest"],"AmountPaid":creditSummaryjson[0]["AmountPaid"],"TotalCredit":creditSummaryjson[0]["TotalCredit"],"amountleft":creditSummaryjson[0]["amountleft"]}
                        json_data.append(jsondataObject)
                except Exception as error:
                    if not creditSummaryjson[0]["amountleft"]:
                        creditSummaryjson[0]["amountleft"]=creditSummaryjson[0]["TotalCredit"]
                    creditSummaryPersonalDetailsSql=f"""Select(SELECT guestAddress from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1 ) as guestAddress,(SELECT guestPhone from tblorderhistory where  Outlet_Name=%s and guestID=%s limit 1) as guestPhone,(SELECT guestEmail from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guestEmail,(SELECT guestID from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guestID,(SELECT GuestName from tblorderhistory where Outlet_Name=%s and guestID=%s limit 1) as guest"""
                    cursor.execute(creditSummaryPersonalDetailsSql,(json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,json["outlet"],guestID,),)
                    privateSummaryDetails = cursor.fetchall()
                    row_headers2=[x[0] for x in cursor.description] 
                    creditSummaryPrivatejson=[]
                    for x in privateSummaryDetails:
                        creditSummaryPrivatejson.append(dict(zip(row_headers2,x)))
                    jsondataObject={"guestPhone":creditSummaryPrivatejson[0]["guestPhone"],"guestID":creditSummaryPrivatejson[0]["guestID"],"guestEmail":creditSummaryPrivatejson[0]["guestEmail"],"guestAddress":creditSummaryPrivatejson[0]["guestAddress"],"guest":creditSummaryPrivatejson[0]["guest"],"AmountPaid":creditSummaryjson[0]["AmountPaid"],"TotalCredit":creditSummaryjson[0]["TotalCredit"],"amountleft":creditSummaryjson[0]["amountleft"]}
                    json_data.append(jsondataObject)
                    
                    
            mydb.commit()
            mydb.close()
            return json_data,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

