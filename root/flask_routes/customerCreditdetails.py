from flask import Flask, Blueprint,request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file26 = Blueprint('app_file26',__name__)
from root.auth.check import token_auth



@app_file26.route("/customerCreditDetails", methods=["POST"])
@cross_origin()
def customerCreditdetails():
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
        if "guestID" not in json or  "outlet" not in json or "CustomerName" not in json or json["CustomerName"]=="" or json["outlet"]=="":
            data= {"error":"Missing parameters."}
            return data,400
        get_customer_credit_DetailsSql =f"""select a.idtblorderHistory, a.bill_no, a.Date, a.DiscountAmt, a.Total from tblorderhistory a, CreditHistory b where a.GuestName=%s and a.PaymentMode='Credit' and a.Outlet_Name=%s and a.guestID=%s and a.guestID=b.guestID GROUP by  a.idtblorderHistory"""
        cursor.execute(get_customer_credit_DetailsSql,(json["CustomerName"],json["outlet"],json["guestID"],),)
        creditWiseBillResult = cursor.fetchall()
        if creditWiseBillResult == []:
            creditWiseBillJson = {"error":"Temporarily unavailable."}
        else:
            row_headers=[x[0] for x in cursor.description] 
            creditWiseBillJson=[]
            for res in creditWiseBillResult:
                creditWiseBillJson.append(dict(zip(row_headers,res)))
        get_customer_credit_Payment_DetailsSql =f"""select a.Date, a.PaymentAt as Time, a.Amount,a.PaymentMode from CreditHistory a,tblorderhistory b where a.customerName=%s and a.outetName=%s and  a.guestID=%s and a.creditState='Payment' and a.guestID=b.guestID GROUP BY idCreditTable DESC"""
        cursor.execute(get_customer_credit_Payment_DetailsSql,(json["CustomerName"],json["outlet"],json["guestID"],),)
        creditPaymentResult = cursor.fetchall()
        if creditPaymentResult == []:
            creditWisePaymentJson = {"error":"Temporarily unavailable."}
        else:
            row_headers=[x[0] for x in cursor.description] 
            creditWisePaymentJson=[]
            for res in creditPaymentResult:
                creditWisePaymentJson.append(dict(zip(row_headers,res)))
        
        CreditDetails_Total_Sql =f"""select  sum(b.Total) as Total, b.GuestName  FROM CreditHistory a, tblorderhistory b where b.GuestName=%s and b.Outlet_Name=%s and  a.guestID=%s and b.PaymentMode='Credit' and a.guestID=b.guestID"""
        cursor.execute(CreditDetails_Total_Sql,(json["CustomerName"],json["outlet"],json["guestID"],),)
        CreditDetails_Total_result = cursor.fetchall()
        if CreditDetails_Total_result == []:
            CreditDetail_Total = {"error":"Temporarily unavailable."}
        else:
            row_headers=[x[0] for x in cursor.description] 
            CreditDetail_Total=[]
            for res in CreditDetails_Total_result:
                CreditDetail_Total.append(dict(zip(row_headers,res)))
            CreditDetail_Total= CreditDetail_Total[0]["Total"]
        CreditDetails_Paid_Sql =f"""Select (SELECT sum(Amount)  FROM CreditHistory where 	creditState='Payment' and   guestID=%s and outetName=%s) as TotalPaid,(SELECT sum(Total)   FROM tblorderhistory where PaymentMode='Credit'  and guestID=%s and Outlet_Name=%s) as  TotalCreditSale, (Select TotalCreditSale- TotalPaid ) as RemainingAmount"""
        cursor.execute(CreditDetails_Paid_Sql,(json["guestID"],json["outlet"],json["guestID"],json["outlet"],),)
        creditDetailsSummary = cursor.fetchall()
        if creditDetailsSummary == []:
            CreditDetails = {"error":"Temporarily unavailable."}
        
        else:
            CreditDetails=[]
            row_headers=[x[0] for x in cursor.description] 
            for res in creditDetailsSummary:
                CreditDetails.append(dict(zip(row_headers,res)))
        response_json = {"CreditDetails":CreditDetails[0],"CreditWiseBillList":creditWiseBillJson,"CreditWisePaymentList":creditWisePaymentJson}
        mydb.close()
        return response_json,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

