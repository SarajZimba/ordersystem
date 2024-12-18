from flask import Blueprint,request
import mysql.connector
from flask_cors import  cross_origin
import os
from dotenv import load_dotenv
load_dotenv()
app_file13= Blueprint('app_file13',__name__)


@app_file13.route("/reqget/", methods=["GET"])
@cross_origin()
def reqget():
    try:
        mydb = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('password'))
        cursor = mydb.cursor(buffered=True)
        database_sql = "USE {};".format(os.getenv('database'))
        cursor.execute(database_sql)
        sql = "SELECT * FROM intbl_purchaserequisition "
        cursor.execute(sql)
        try:
            desc = cursor.description
        except Exception as e:
            pass
        r= [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]
        mydb.commit()
        mydb.close()
        return r,200
    except Exception as error:
        data ={'error':str(error)}
        return data,400