import frappe
from frappe.core.doctype.sms_settings.sms_settings import send_sms 
from excel_erpnext.doc_events.common.common import get_customer_details, get_notified_mobile_no, get_notified_email, get_customer_outstanding_balance, format_in_bangladeshi_currency, get_notification_permission

def send_notification(doc, method=None):
    try:
        settings = frappe.get_doc("ArcApps Alert Settings")
        email_enabled = bool(settings.excel_email)
        sms_enabled = bool(settings.excel_sms)
        notification_permission = get_notification_permission(doc.name)
        if notification_permission['sms'] and sms_enabled:
            send_sms_notification(doc, method)
        if notification_permission['email']:
            send_email_notification(doc, method)
        if notification_permission['both']:
            if sms_enabled:
                send_sms_notification(doc, method)
            if email_enabled:
                send_email_notification(doc, method)

    except frappe.DoesNotExistError:
        print("ArcApps Alert Settings not found.")
    except Exception as e:
        frappe.log_error(message=f"Error in send_notification: {str(e)}", title="Notification Error")


def send_sms_notification(doc, method):
    customer_details = get_customer_details(doc.name)  # Log customer details for debugging
    notified_phone_no_list = customer_details.get('notified_phone_no_list')
    if len(notified_phone_no_list) == 0:
        return
    if isinstance(notified_phone_no_list, list):
        if len(notified_phone_no_list) == 0:
            # frappe.msgprint("The phone number list is empty.")
            return
    else:
        # frappe.msgprint("Notified phone number list is not an array.")
        return

    if method == "after_insert":
        sales_person_name = customer_details.get('sales_person_name')
        sales_person_mobile_no = customer_details.get('sales_person_mobile_no')

        if sales_person_mobile_no:
            message = f"Dear Valued Partner, Welcome aboard! We're proud to be your business partner. For queries, contact {sales_person_name}: {sales_person_mobile_no}. Excel Technologies Ltd."
        else:
            message = f"Dear Valued Partner, Welcome aboard! We're proud to be your business partner. For queries, contact your KAM {sales_person_name}. Excel Technologies Ltd."

        
        for phone_no in notified_phone_no_list:
            send_sms([phone_no], message)

def send_email_notification(doc, method=None):
    customer_details = get_customer_details(doc.name)
    notified_email_list = customer_details.get('notified_email_list')
    if len(notified_email_list) == 0:
        return
    # Check if the email list is valid and not empty
    if isinstance(notified_email_list, list):
        frappe.msgprint(f"Notified Email List: {notified_email_list}")
        if len(notified_email_list) == 0:
            return
    else:
        frappe.msgprint("Notified email list is not an array.")
        return

    if method == "after_insert":
        sales_person_name = customer_details.get('sales_person_name')
        sales_person_mobile_no = customer_details.get('sales_person_mobile_no')
        sales_person_email = customer_details.get('sales_person_email')

        message = f"""
        <p>Dear Valued Partner,</p>
        <p>Welcome aboard! We're proud to have you as our business partner and look forward to a successful journey together.</p>
        <p>If you have any requirement or need assistance, please feel free to reach out {'your KAM' if not sales_person_mobile_no and not sales_person_email else 'to'} <b>{sales_person_name}</b> {'.' if not sales_person_mobile_no and not sales_person_email else ''}
        {f'at <b>{sales_person_mobile_no}</b>' if sales_person_mobile_no  else ''}
        {f'or email' if sales_person_email and sales_person_mobile_no else ''}
        {f'at <b>{sales_person_email}</b>' if sales_person_email  else ''} </p>
        <p>For more information on our products and services, please visit our website: 
            <a href="http://www.excelbd.com" target="_blank">www.excelbd.com</a> 
            or on Facebook: 
            <a href="https://www.facebook.com/ExcelTechnologiesLtd" target="_blank">Excel Technologies Ltd</a>
        </p>
        <p>Thank you for choosing us.</p>
        <br>
        <p>Sincerely,</p>
        <p>Excel Technologies Ltd.</p>
        <p style="color: #888; font-size: 12px; font-style: italic;">
            This is a system generated email. Please do not reply, as responses to this email are not monitored.
        </p>
        """
        
        frappe.sendmail(recipients=notified_email_list, subject="Welcome to Excel Technologies Ltd.", message=message)

