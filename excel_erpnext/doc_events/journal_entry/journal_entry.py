import frappe
import locale
try:
    locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

from frappe.core.doctype.sms_settings.sms_settings import send_sms as send_sms_frappe

def send_notification(doc, method=None):
    frappe.msgprint(method)
    accounts = doc.accounts
    customer_accounts = [account for account in accounts if account.party_type == "Customer" and account.party]
    if len(customer_accounts) == 0:
        return
    settings = frappe.get_doc("ArcApps Alert Settings")
    sms_enabled = bool(settings.excel_sms)
    email_enabled = bool(settings.excel_email)
    for account in customer_accounts:
        customer = frappe.get_doc("Customer", account.party)
        notification_type = customer.excel_notification_type
        mobile_number = customer.mobile_no
        if notification_type == "SMS" and sms_enabled and mobile_number:
            send_sms(doc, account,method,mobile_number)
        elif notification_type == "Email" and email_enabled and customer.email_id:
            send_email(doc, account,method,customer.email_id)
        elif notification_type == "SMS & Email" and sms_enabled and email_enabled and mobile_number and customer.email_id:
            send_sms(doc, account,method,mobile_number)
            send_email(doc, account,method,customer.email_id)
    
def send_sms(doc, account,method,mobile_number):
    
    credit_amount= account.credit
    total_outstanding_balance = get_customer_outstanding_balance(account.party)
    brand_name= account.excel_product_team
    posting_date = doc.posting_date
    if method == "on_submit":
        frappe.msgprint(frappe.as_json(account))
        if doc.voucher_type == "Credit Note":
            message = f"Dear Valued Partner, taka {format_in_bangladeshi_currency(credit_amount)} adjusted against {brand_name} . Total Outstanding: {format_in_bangladeshi_currency(total_outstanding_balance)}৳. Date: {posting_date}"
            send_sms_frappe([mobile_number],message)
def send_email(doc, account, method, email_id):
    credit_amount = account.credit
    total_outstanding_balance = get_customer_outstanding_balance(account.party)
    brand_name = account.excel_product_team
    posting_date = doc.posting_date
    if method == "on_submit":
        frappe.msgprint(frappe.as_json(account))
        if doc.voucher_type == "Credit Note":
            subject = f"Adjustment Notification for {brand_name}"
            message = f"""
                <p>Dear Valued Partner,</p>
                <p>Taka <b>{format_in_bangladeshi_currency(credit_amount)}</b> has been adjusted against {brand_name}.</p>
                <p>Total Outstanding: <b>{format_in_bangladeshi_currency(total_outstanding_balance)}৳</b></p>
                <p>Date: {posting_date}</p>
                <p>Sincerely!!</p>
                <p>Excel Technologies Ltd.</p>
            """
            # Send the email
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