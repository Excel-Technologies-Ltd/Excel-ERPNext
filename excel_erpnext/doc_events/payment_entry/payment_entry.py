import frappe
import locale
try:
    locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
from frappe.core.doctype.sms_settings.sms_settings import send_sms as send_sms_frappe
def send_notification(doc, method=None):
    if doc.party_type != "Customer":
        return
    frappe.msgprint(frappe.as_json(doc))
    settings = frappe.get_doc("ArcApps Alert Settings")
    sms_enabled = bool(settings.excel_sms)
    email_enabled = bool(settings.excel_email)
    customer = frappe.get_doc("Customer", doc.party)
    notification_type = customer.excel_notification_type
    mobile_number = customer.mobile_no
    email_id = customer.email_id
    if notification_type == "SMS" and sms_enabled:
        send_sms(doc,method,mobile_number)
    elif notification_type == "Email" and email_enabled:
        send_email(doc,method,email_id)
    elif notification_type == "Both" and sms_enabled and email_enabled:
        send_sms(doc,method,mobile_number)
        send_email(doc,method,email_id)
def send_sms(doc,method,mobile_number):
    if doc.party_type == "Customer":
        total_amount = doc.paid_amount
        outstanding_balance = get_customer_outstanding_balance(doc.party)
        posting_date = doc.posting_date
        if method == "on_update":
            message = f"Dear Valued Partner,taka {total_amount} has been deposited from {doc.party}. Total Outstanding: {outstanding_balance}. Date: {posting_date}."
        send_sms_frappe([mobile_number],message,)
        
def send_email(doc,method,email_id):
    if doc.party_type == "Customer":
        total_amount = doc.paid_amount
        outstanding_balance = get_customer_outstanding_balance(doc.party)
        posting_date = doc.posting_date
        if method == "on_update":
            subject = "Payment Received Notification"
            message = f"""
                <p>Dear Valued Partner,</p>
                <p>taka<b>{format_in_bangladeshi_currency(total_amount)}৳</b> has been deposited from {doc.party}</p>
                <p>Total Outstanding: <b>{format_in_bangladeshi_currency(outstanding_balance)}৳</b></p>
                <p>Date: {posting_date}</p>
                <p>Sincerely!!</p>
                <p>Excel Technologies Ltd.</p>
            """
            frappe.sendmail(
                recipients=[email_id],
                subject=subject,
                message=message
            )



def get_customer_outstanding_balance(customer_name):
    total_debit_credit = frappe.db.sql(
        """
        SELECT 
            SUM(debit_in_account_currency) AS total_debit,
            SUM(credit_in_account_currency) AS total_credit
        FROM 
            `tabGL Entry`
        WHERE 
            party_type = 'Customer' AND party = %s
        """, 
        (customer_name,),
        as_dict=True
    )
    
    # Calculate the total outstanding balance
    total_debit = total_debit_credit[0].get('total_debit') or 0
    total_credit = total_debit_credit[0].get('total_credit') or 0
    outstanding_balance = total_debit - total_credit
    
    return outstanding_balance
def format_in_bangladeshi_currency(amount):
    # Set the locale for Indian numbering system
    # Format the number using locale
    formatted_amount = locale.format_string("%d", amount, grouping=True)
    
    return formatted_amount