import frappe
# import locale
from frappe.utils import get_url

from datetime import datetime
# try:
#     locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')
# except locale.Error:
#     locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def get_customer_details(customer_name_id,outstanding_balance=False):
    customer = frappe.get_doc("Customer", customer_name_id)
    customer_name = customer.customer_name
    is_frozen=customer.is_frozen
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
            'customer_name':customer_name,
            'is_frozen':True if is_frozen else False
            }


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


def format_in_bangladeshi_currency(amount, sms=False):
    # Determine if the amount is negative
    is_negative = amount < 0
    if is_negative:
        amount = abs(amount)  # Work with the positive version of the amount for formatting

    # Convert to string and round only if sms is True
    if sms:
        amount = round(amount, 2)
    amount_str = str(amount)
    
    # Handle decimal part if present (for cases with or without sms)
    if '.' in amount_str:
        whole_part, decimal_part = amount_str.split('.')
        if sms:
            decimal_part = decimal_part.ljust(2, '0')[:2]  # Ensure two decimal places
    else:
        whole_part = amount_str
        decimal_part = None

    length = len(whole_part)

    # If the number is less than or equal to 3 digits, return as is
    if length <= 3:
        formatted_amount = amount_str if not sms or not decimal_part else f"{whole_part}.{decimal_part}"
    else:
        # Format last three digits, then add commas in the Bangladeshi style
        formatted_amount = whole_part[-3:]  # Last three digits
        remaining_digits = whole_part[:-3]  # Digits before the last three

        # Group by 2 digits from the end of remaining_digits
        while len(remaining_digits) > 2:
            formatted_amount = remaining_digits[-2:] + ',' + formatted_amount
            remaining_digits = remaining_digits[:-2]

        # Add the remaining part, which is 1 or 2 digits
        if remaining_digits:
            formatted_amount = remaining_digits + ',' + formatted_amount

    # Append decimal part if present
    if decimal_part:
        formatted_amount = f"{formatted_amount}.{decimal_part}"

    # Add negative sign back if needed
    if is_negative:
        formatted_amount = '-' + formatted_amount

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
def get_attachment_permission(doc_name):
    if doc_name == "Journal Entry": 
        settings = frappe.get_doc("ArcApps Alert Settings")
        return bool(settings.journal_att)
    elif doc_name == "Payment Entry":
        settings = frappe.get_doc("ArcApps Alert Settings")
        return bool(settings.payment_att)
    elif doc_name == "Sales Invoice":
        settings = frappe.get_doc("ArcApps Alert Settings")
        return bool(settings.invoice_att)
    elif doc_name == "Journal Attachment (Corporate)":
        settings = frappe.get_doc("ArcApps Alert Settings")
        return bool(settings.corp_journal_att)
    else:
        return False

def get_cm_mail():
    try:
        # Fetch the settings document
        settings = frappe.get_doc("ArcApps Alert Settings")
        mail_list = settings.get("mail_list", [])
        if not mail_list:
            frappe.log_error("Mail list is empty or missing in ArcApps Alert Settings", "Missing Mail List")
            return []
        user_ids = [mail.get("user_email") for mail in mail_list if mail.get("user_email")]      
        return user_ids

    except Exception as e:
        # Log the error for debugging
        frappe.log_error(frappe.get_traceback(), "Error in get_cm_mail")
        print(f"Error: {str(e)}")
        return []
    
def send_cm_mail_from_payment_entry(doc):
    settings = frappe.get_doc("ArcApps Alert Settings")
    if not bool(settings.payment_entry_cm):
        return
    customer = doc.party
    paid_amount = doc.paid_amount
    customer_details = get_customer_details(customer,outstanding_balance=True)
    is_frozen = customer_details.get('is_frozen')
    if not is_frozen:
        return
    customer_name= customer_details.get('customer_name')
    outstanding_balance= customer_details.get('outstanding_balance')
    send_email_to_cm(customer,customer_name,paid_amount,outstanding_balance)
    
def send_cm_mail_from_journal_entry(customer):
    settings = frappe.get_doc("ArcApps Alert Settings")
    if not bool(settings.journal_entry_cm):
        return    
    account = customer.get('account')
    party_type = customer.get('party_type')
    party_name = customer.get('party')
    
    customer_details = get_customer_details(party_name, outstanding_balance=True)
    is_frozen = customer_details.get('is_frozen')
    if not is_frozen:
        return
    customer_name= customer_details.get('customer_name')
    outstanding_balance= customer_details.get('outstanding_balance')
    credit_amount = customer.get('credit_in_account_currency')
    debit_amount = customer.get('debit_in_account_currency')
    if credit_amount > 0:
        paid_amount = credit_amount
    else:
        paid_amount = debit_amount
    send_email_to_cm(party_name,customer_name,paid_amount,outstanding_balance,enrty_type='journal entry')



def send_email_to_cm(customer_code, customer_name, paid_amount, outstanding_balance,enrty_type='payment entry'):
    subject = 'Customer Unfreeze Alert'
    base_url = get_url()
    mail_list = get_cm_mail()
    if len(mail_list) == 0:
        return
    # Generate the customer URL
    customer_url = f"{base_url}/app/customer/{customer_code}"
    message = f"""
    <p>Dear Concern,</p>
    
    <p>A {enrty_type} has been received from <strong>{customer_name}</strong>. Kindly review and take the necessary action to unfreeze.</p>
    
    <p><strong>Details:</strong></p>
    <ul>
        <li>Customer: <a href="{customer_url}" target="_blank">{customer_code}</a></li>
        <li>Customer Name: <strong>{customer_name}</strong></li>
        <li>Paid Amount: <strong>{paid_amount} Taka</strong></li>
        <li>Current Outstanding: <strong>{outstanding_balance} Taka</strong></li>
    </ul>
    
    <p>Best Regards,<br>Team ETL</p>
    """
    
    # Displaying the message for debug purposes (optional)
    frappe.sendmail(
        recipients=mail_list,
        subject=subject,
        message=message
    )
