import frappe
import locale
try:
    locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
from frappe.core.doctype.sms_settings.sms_settings import send_sms as send_sms_frappe
def send_notification(doc, method=None):
    settings = frappe.get_doc("ArcApps Alert Settings")
    sms_enabled = bool(settings.excel_sms)
    email_enabled = bool(settings.excel_email)
    customer = frappe.get_doc("Customer", doc.customer)
    notification_type = customer.excel_notification_type
    mobile_number = customer.mobile_no
    email_id = customer.email_id
    if notification_type == "SMS" and sms_enabled and mobile_number:
        send_sms(doc,method,mobile_number)
    elif notification_type == "Email" and email_enabled and email_id:
        send_email(doc,method,email_id)
    elif notification_type == "SMS & Email" and sms_enabled and email_enabled and mobile_number and email_id:
        send_sms(doc,method,mobile_number)
        send_email(doc,method,email_id)
    
def send_sms(doc,method,mobile_number):
    if method == "on_submit":
        total_amount = doc.grand_total
        outstanding_balance= get_customer_outstanding_balance(doc.customer)
        posting_date = doc.posting_date
        message=(f"Dear Valued Partner, bill amount of {format_in_bangladeshi_currency(total_amount)}৳ has been generated to your ledger. Total Outstanding: {format_in_bangladeshi_currency(outstanding_balance)}৳. Posting Date: {posting_date}.")
        send_sms_frappe([mobile_number],message)
def send_email(doc,method,email_id):
    if method == "on_submit":
        frappe.msgprint("Email")
        total_amount = doc.grand_total
        outstanding_balance= get_customer_outstanding_balance(doc.customer)
        posting_date = doc.posting_date
        subject = "Bill Generated Notification"
        message = f"""
            <p>Dear Valued Partner,</p>
            <p>Bill amount of <b>{format_in_bangladeshi_currency(total_amount)}৳</b> has been generated to your ledger.</p>
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