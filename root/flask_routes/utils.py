import requests
from decimal import Decimal
from datetime import datetime
import os
def post_sales_and_create_journal(data):
    print("inside function")
    try:
        print("inside try")
        print(data)
        # Extract relevant data from request
        total = round(Decimal(data["Total"]), 2)
        vat = round(Decimal(data["VAT"]), 2)
        discount_amt = round(Decimal(data["discountAmt"]), 2)
        payment_mode = data["paymentMode"]
        bill_no = data["OrderID"]
        date_str = data["date"]
        employee = data["Employee"]
        outlet = data["Outlet_Name"]
        # Convert date to required format
        formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 GMT")
        backend_url = os.getenv("backend_url")
        # Get ledger details from API
        ledger_api_url = backend_url + "api/get-ledgers"
        ledger_response = requests.get(ledger_api_url)
        ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}
        # Calculate ledger-specific values
        sale_amount = total - vat 

        # Debit Side
        debit_ledgers = []
        debit_particulars = []
        debit_amounts = []


        if payment_mode != "Complimentary" or payment_mode != "Non Chargeable":
            if payment_mode == "Split":
                for split_payment in data.get("SplitPaymentDetailsList", []):
                    if split_payment["paymentMode"] == "Cash":
                        payment_ledger_id = ledgers.get("Cash-In-Hand")
                        payment_ledger_name = "Cash-In-Hand"
                    if split_payment["paymentMode"] == "Credit Card":
                        payment_ledger_id = ledgers.get("Card Transactions")
                        payment_ledger_name = "Card Transactions"

                    if split_payment["paymentMode"] == "Mobile Payment":
                        payment_ledger_id = ledgers.get("Mobile Payments")
                        payment_ledger_name = "Mobile Payments"

                    # payment_ledger_name = split_payment["paymentMode"] 
                    # payment_ledger_id = ledgers.get(payment_ledger_name)
                    if not payment_ledger_id:
                        raise ValueError(f"Invalid payment ledger name: {payment_ledger_name}")

                    debit_ledgers.append(payment_ledger_id)
                    debit_particulars.append(f"Split payment from bill no: {bill_no}")
                    debit_amounts.append(Decimal(split_payment["paymentAmount"]))
            else:
                if payment_mode == "Cash":
                    debit_ledger_name = "Cash-In-Hand"  
                if payment_mode == "Credit Card":
                    debit_ledger_name = "Card Transactions"  
                if payment_mode == "Mobile Payment":
                    debit_ledger_name = "Mobile Payments"  
                debit_ledger_id = ledgers.get(debit_ledger_name)
                print(debit_ledger_id)
                if not debit_ledger_id:
                    raise ValueError(f"Invalid debit ledger name: {debit_ledger_name}")

                debit_ledgers.append(debit_ledger_id)
                debit_particulars.append(f"Sale from bill no: {bill_no}")
                debit_amounts.append(total)

            # Credit Side
            credit_ledgers = []
            credit_particulars = []
            credit_amounts = []

            if sale_amount > 0:
                credit_ledgers.append(ledgers["Sales"])
                credit_particulars.append("Sales")
                credit_amounts.append(sale_amount)

            if vat > 0:
                credit_ledgers.append(ledgers["VAT Payable"])
                credit_particulars.append("VAT Payable")
                credit_amounts.append(vat)

            if discount_amt > 0:
                credit_ledgers.append(ledgers["Discount Sales"])
                credit_particulars.append("Discount Sales")
                credit_amounts.append(discount_amt)
                # Discount Expenses
                debit_ledgers.append(ledgers["Discount Expenses"])
                debit_particulars.append("Discount Expenses")
                debit_amounts.append(discount_amt)
            # Prepare data for the journal entry API
        else:
            credit_ledgers.append(ledgers["Complimentary Sales"])
            credit_particulars.append("Complimentary Sales")
            credit_amounts.append(sale_amount)
                # Discount Expenses
            debit_ledgers.append(ledgers["Complimentary Expenses"])
            debit_particulars.append("Complimentary Expenses")
            debit_amounts.append(sale_amount)            
        journal_entry_data = {
            "outlet_name": outlet,
            "bill_id": bill_no,
            "datetime": formatted_date,
            "user": employee,
            "debit_ledgers": debit_ledgers,
            "debit_particulars": debit_particulars,
            "debit_amounts": [str(amount) for amount in debit_amounts],
            "credit_ledgers": credit_ledgers,
            "credit_particulars": credit_particulars,
            "credit_amounts": [str(amount) for amount in credit_amounts]
        }

        token = os.getenv("token")

        # Post to the Journal Entry API
        backend_url = os.getenv("backend_url")
        journal_entry_api_url = backend_url + "api/create_journal_entry/"

        # Set the headers to include the bearer token
        headers = {
            "Authorization": f"Bearer {token}",  # Pass the token as a Bearer token
            "Content-Type": "application/json"   # Optional, ensures JSON content
        }
        print(journal_entry_data)
        response = requests.post(journal_entry_api_url, json=[journal_entry_data], headers=headers)

        if response.status_code == 201:
            print({"message": "Journal entry created successfully"})
        else:
            # print(response.json())
            print({"error": str(response.json())})

    except Exception as error:
        print({"error": str(error)})


import requests
from decimal import Decimal
from datetime import datetime
import os
def post_sales_and_create_journal_for_creditbills(data):
    print("inside function")
    try:
        print("inside try")
        print(data)
        # Extract relevant data from request
        total = round(Decimal(data["Total"]), 2)
        vat = round(Decimal(data["VAT"]), 2)
        discount_amt = round(Decimal(data["discountAmt"]), 2)
        payment_mode = data["paymentMode"]
        bill_no = data["OrderID"]
        date_str = data["date"]
        employee = data["Employee"]
        outlet = data["Outlet_Name"]

        # Convert date to required format
        formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 GMT")
        backend_url = os.getenv("backend_url")

        # Get ledger details from API
        # ledger_api_url = "https://9thamel.silverlinepos.com/api/get-ledgers"
        # ledger_api_url = "https://9thamel.silverlinepos.com/api/get-ledgers"
        ledger_api_url = backend_url + "api/get-ledgers"

        ledger_response = requests.get(ledger_api_url)
        ledgers = {ledger["ledger_name"]: ledger["id"] for ledger in ledger_response.json()}
        # Calculate ledger-specific values
        sale_amount = total - vat 

        # Debit Side
        debit_ledgers = []
        debit_ledger_names = []
        debit_particulars = []
        debit_amounts = []


        if payment_mode != "Complimentary" or payment_mode != "Non Chargeable":
            if payment_mode == "Split":
                for split_payment in data.get("SplitPaymentDetailsList", []):
                    if split_payment["paymentMode"] == "Cash":
                        payment_ledger_id = ledgers.get("Cash-In-Hand")
                        payment_ledger_name = "Cash-In-Hand"
                    if split_payment["paymentMode"] == "Credit Card":
                        payment_ledger_id = ledgers.get("Card Transactions")
                        payment_ledger_name = "Card Transactions"

                    if split_payment["paymentMode"] == "Mobile Payment":
                        payment_ledger_id = ledgers.get("Mobile Payments")
                        payment_ledger_name = "Mobile Payments"

                    # payment_ledger_name = split_payment["paymentMode"] 
                    # payment_ledger_id = ledgers.get(payment_ledger_name)
                    if not payment_ledger_id:
                        raise ValueError(f"Invalid payment ledger name: {payment_ledger_name}")

                    debit_ledgers.append(payment_ledger_id)
                    debit_particulars.append(f"Split payment from bill no: {bill_no}")
                    debit_amounts.append(Decimal(split_payment["paymentAmount"]))
            else:
                # if payment_mode == "Cash":
                #     debit_ledger_name = "Cash-In-Hand"  
                # if payment_mode == "Credit Card":
                #     debit_ledger_name = "Card Transactions"  
                # if payment_mode == "Mobile Payment":
                #     debit_ledger_name = "Mobile Payments"  
                # debit_ledger_id = ledgers.get(debit_ledger_name)
                debit_ledger_id = data["guestID"]
                print(debit_ledger_id)
                # if not debit_ledger_id:
                #     raise ValueError(f"Invalid debit ledger name: {debit_ledger_name}")
                debit_ledger_name = data["GuestName"]
                debit_ledgers.append(debit_ledger_id)
                debit_ledger_names.append(debit_ledger_name)
                debit_particulars.append(f"Sale from bill no: {bill_no}")
                debit_amounts.append(total)

            # Credit Side
            credit_ledgers = []
            credit_particulars = []
            credit_amounts = []

            if sale_amount > 0:
                credit_ledgers.append(ledgers["Sales"])
                credit_particulars.append("Sales")
                credit_amounts.append(sale_amount)

            if vat > 0:
                credit_ledgers.append(ledgers["VAT Payable"])
                credit_particulars.append("VAT Payable")
                credit_amounts.append(vat)

            if discount_amt > 0:
                credit_ledgers.append(ledgers["Discount Sales"])
                credit_particulars.append("Discount Sales")
                credit_amounts.append(discount_amt)
                # Discount Expenses
                debit_ledgers.append(ledgers["Discount Expenses"])
                debit_particulars.append("Discount Expenses")
                debit_amounts.append(discount_amt)
            # Prepare data for the journal entry API
        else:
            credit_ledgers.append(ledgers["Complimentary Sales"])
            credit_particulars.append("Complimentary Sales")
            credit_amounts.append(sale_amount)
                # Discount Expenses
            debit_ledgers.append(ledgers["Complimentary Expenses"])
            debit_particulars.append("Complimentary Expenses")
            debit_amounts.append(sale_amount)            
        journal_entry_data = {
            "outlet_name": outlet,
            "bill_id": bill_no,
            "datetime": formatted_date,
            "user": employee,
            "debit_ledgers": debit_ledgers,
            "debit_particulars": debit_particulars,
            "debit_amounts": [str(amount) for amount in debit_amounts],
            "credit_ledgers": credit_ledgers,
            "credit_particulars": credit_particulars,
            "credit_amounts": [str(amount) for amount in credit_amounts],
            "debit_ledger_names": debit_ledger_names
        }

        token = os.getenv("token")
        # Post to the Journal Entry API
        # journal_entry_api_url = "https://9thamel.silverlinepos.com/api/create_credit_journal_entry/"
        journal_entry_api_url = backend_url + "api/create_credit_journal_entry/"

        # Set the headers to include the bearer token
        headers = {
            "Authorization": f"Bearer {token}",  # Pass the token as a Bearer token
            "Content-Type": "application/json"   # Optional, ensures JSON content
        }
        print(journal_entry_data)
        response = requests.post(journal_entry_api_url, json=[journal_entry_data], headers=headers)

        if response.status_code == 201:
            print({"message": "Journal entry created successfully"})
        else:
            print({"error": str(response.json())})

    except Exception as error:
        print({"error": str(error)})