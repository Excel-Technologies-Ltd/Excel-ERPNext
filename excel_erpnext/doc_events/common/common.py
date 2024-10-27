import frappe
import locale
from datetime import datetime
try:
    locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def get_customer_details(customer_name_id,outstanding_balance=False):
    customer = frappe.get_doc("Customer", customer_name_id)
    customer_name = customer.customer_name
    # Check sales team presence
    sales_team_name = (
        customer.sales_team[0].sales_person
        if hasattr(customer, 'sales_team') and customer.sales_team and len(customer.sales_team) > 0
        else "Unknown Sales Person"
    )
    
    # Fetch sales person details
    get_sales_person_details = frappe.db.sql("""
        SELECT name, excel_sales_person_email, excel_sales_person_mobile_no 
        FROM `tabSales Person` 
        WHERE name = %s
    """, sales_team_name, as_dict=True)
    
    if get_sales_person_details:
        excel_sales_person_name = get_sales_person_details[0].get('name', '')
        excel_sales_person_mobile_no = get_sales_person_details[0].get('excel_sales_person_mobile_no', '')
        excel_sales_person_email = get_sales_person_details[0].get('excel_sales_person_email', '')
    else:
        excel_sales_person_name = ""
        excel_sales_person_mobile_no = ""
        excel_sales_person_email = ""
    excel_sales_person_name = get_sales_person_details[0]['name']
    excel_sales_person_mobile_no = get_sales_person_details[0]['excel_sales_person_mobile_no']
    excel_sales_person_email = get_sales_person_details[0]['excel_sales_person_email']
    customer_primary_contact = customer.customer_primary_contact
    customer_primary_contact_phone_no = get_notified_mobile_no(customer_primary_contact)
    customer_primary_contact_email = get_notified_email(customer_primary_contact)
    customer_outstanding_balance = get_customer_outstanding_balance(customer_name_id) if outstanding_balance else 0
    return {'sales_person_name':excel_sales_person_name,
            'sales_person_mobile_no':excel_sales_person_mobile_no,
            'sales_person_email':excel_sales_person_email,
            'notified_phone_no_list':customer_primary_contact_phone_no,
            'notified_email_list':customer_primary_contact_email,
            'outstanding_balance':customer_outstanding_balance,
            'customer_name':customer_name}


def get_notified_mobile_no(primary_contact):
    # Raw SQL query to fetch the contact phone
    query = """
        SELECT cp.phone 
        FROM `tabContact Phone` AS cp
        WHERE cp.parenttype = 'Contact'
        AND cp.parentfield = 'phone_nos'
        AND cp.excel_notification=1
        AND cp.parent = %s
    """
    result = frappe.db.sql(query, primary_contact, as_dict=True)
    phone_nos = [row['phone'] for row in result]
    return phone_nos
def get_notified_email(primary_contact):
    query = """
        SELECT cp.email_id 
        FROM `tabContact Email` AS cp
        WHERE cp.parenttype = 'Contact'
        AND cp.parentfield = 'email_ids'
        AND cp.excel_notification=1
        AND cp.parent = %s
    """
    result = frappe.db.sql(query, primary_contact, as_dict=True)
    emails = [row['email_id'] for row in result]
    return emails


def get_customer_outstanding_balance(customer_name):
    frappe.msgprint(customer_name)
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


def get_notification_permission(customer):
    sms=False
    email=False
    both=False
    try:
        settings = frappe.get_doc("ArcApps Alert Settings")
        customer_details = frappe.get_doc("Customer",customer)
        sms_enabled = bool(settings.excel_sms)
        email_enabled = bool(settings.excel_email)
        if customer_details.excel_notification_type == "SMS" and sms_enabled:
            sms = True
        elif customer_details.excel_notification_type == "Email" and email_enabled:
            email = True
        elif customer_details.excel_notification_type == "SMS & Email":
            both = True
        return {'sms':sms,'email':email,'both':both}
    except frappe.DoesNotExistError:
        return {'sms':False,'email':False,'both':False}
    
    
def format_time_to_ampm(time_string,is_mail=False):
    try:
        # Convert to datetime object
        time_obj = datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S.%f')
        
        # Format the time as 05:23PM without space
        formatted_time = time_obj.strftime('%I:%M%p') if not is_mail else time_obj.strftime('%I:%M %p')
        
        return formatted_time

    except ValueError:
        return "Invalid time format"
def format_date_to_custom(date_input, need_year=False):
    # frappe.msgprint(date_input)
    try:
        # Check if the input is already a date object
      
            # Convert string to datetime object
        date_obj = datetime.strptime(date_input, '%Y-%m-%d')
        
        # Format the date as '24-Oct-24' or '24-Oct-2024'
        formatted_date = date_obj.strftime('%d-%b-%y') if not need_year else date_obj.strftime('%d-%b-%Y')
        # frappe.msgprint(formatted_date)
        
        return formatted_date
    except Exception as e:
        # Handle exceptions (e.g., invalid date format)
        print(f"Error formatting date: {e}")
        return None
    
def format_date_to_custom_cancel(date_input, need_year=False):
    # frappe.msgprint(date_input)
    try:
        # Check if the input is already a date object
      
            # Convert string to datetime object
        date_obj = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S.%f')
        
        # Format the date as '24-Oct-24' or '24-Oct-2024'
        formatted_date = date_obj.strftime('%d-%b-%y') if not need_year else date_obj.strftime('%d-%b-%Y')
        # frappe.msgprint(formatted_date)
        
        return formatted_date
    except Exception as e:
        # Handle exceptions (e.g., invalid date format)
        print(f"Error formatting date: {e}")
        return None