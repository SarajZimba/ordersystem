from flask import  Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file12= Blueprint('app_file12',__name__)




@app_file12.route("/req", methods=["POST"])
@cross_origin()
def purchasereqPost():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        data = request.get_json()
        sql = f"""                                    
        INSERT INTO `intbl_purchaserequisition`
        (IDIntbl_PurchaseRequisition,RequisitionType,Date,TotalAmount,TaxAmount,Company_Name,State,ReceivedDate,purchaseBillNumber,DiscountAmount,Outlet_Name)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        sql2 = f"""
        INSERT INTO `intbl_purchaserequisition_contract`
        (ItemID,UnitsOrdered,PurchaseReqID,Rate,Name,BrandName,Code,UOM,StockType,Department,GroupName,ExpDate,Status,Taxable)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(
            sql,
            (
                data["PurchaseRequistionID"],
                data["RequisitionType"],
                data["Date"],
                data["TotalAmount"],
                data["TaxAmount"],
                data["Company_Name"],
                data["State"],
                data["ReceivedDate"],
                data["purchaseBillNumber"],
                data["DiscountAmount"],
                data["Outlet_Name"],
            ),
        )
        for data in data["RequisitionDetailsList"]:
            listdata = (
                data["ItemID"],
                data["UnitsOrdered"],
                data["PurchaseReqID"],
                data["Rate"],
                data["Name"],
                data["BrandName"],
                data["Code"],
                data["UOM"],
                data["StockType"],
                data["Department"],
                data["GroupName"],
                data["ExpDate"],
                data["Status"],
                data["Taxable"],
            )
            try:
                cursor.execute(sql2, listdata)
            except Exception as e:
                print(e)
        mydb.commit()
        mydb.close()
        data ={"success":"Data posted successfully."}
        return data,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400

