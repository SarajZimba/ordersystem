from flask import Blueprint, request
import mysql.connector
from flask_cors import cross_origin
import os
from dotenv import load_dotenv
from decimal import Decimal

load_dotenv()
app_file42 = Blueprint('app_file42', __name__)

@app_file42.route("/postmenu", methods=["POST"])
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

        # Check if the tblMenu has already existing data
        cursor.execute("SELECT COUNT(*) FROM tblmenu")
        existing_data_count = cursor.fetchone()[0]

        if existing_data_count > 0:
            cursor.execute("DELETE FROM tblmenu")
            mydb.commit()


        data_list = request.get_json()

        for data in data_list:
            sql = """INSERT INTO tblmenu (Name, Description, Type, Price, Restaurant, state, discountExempt) VALUES (%s, %s, %s, %s, %s, %s, %s) """
            cursor.execute(sql, (
                data['name'],
                data['description'],
                data['type'],
                Decimal(data['price']) if data['price'] else "0.0",
                data['restaurant'],
                data['state'],
                data['discountexempt'],
            ),)
            mydb.commit()

        cursor.close()
        mydb.close()
        return {"success": "Data processed successfully"}, 200

    except Exception as e:
        return {"error": str(e)}, 500