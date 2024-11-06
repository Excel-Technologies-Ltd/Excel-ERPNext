import frappe
from frappe.core.doctype.sms_settings.sms_settings import send_sms  as send_sms_frappe
from excel_erpnext.doc_events.common.common import get_customer_details, get_notified_mobile_no, get_notified_email, get_customer_outstanding_balance, format_in_bangladeshi_currency, get_notification_permission,format_time_to_ampm,format_date_to_custom,format_date_to_custom_cancel,get_attachment_permission
def send_notification(doc, method=None):
    
    if not doc.name.startswith(('sinv', 'SINV','rinv','RINV')):
        return
    settings = frappe.get_doc("ArcApps Alert Settings")
    sms_enabled = bool(settings.excel_sms)
    email_enabled = bool(settings.excel_email)
    notification_permission = get_notification_permission(doc.customer)
    if notification_permission['sms']:
        send_sms_notification(doc, method)
    if notification_permission['email']:
        send_email_notification(doc, method)
    if notification_permission['both']:
        if sms_enabled:
            send_sms_notification(doc, method)
        if email_enabled:
            send_email_notification(doc, method)
def send_sms_notification(doc,method):

    customer_details = get_customer_details(doc.customer,outstanding_balance=True)
    customer=doc.customer_name
    mobile_number = customer_details.get('notified_phone_no_list')
    if len(mobile_number) == 0:
        return
    outstanding_balance = customer_details.get('outstanding_balance')
    voucher_no = doc.name
    return_voucher = doc.return_against
    bill_amount = doc.grand_total
    posting_date =format_date_to_custom(doc.posting_date) if method == "on_submit" and doc.posting_date else format_date_to_custom_cancel(doc.modified)
    
    posting_time = format_time_to_ampm(doc.modified)
    if method == "on_submit":
        if doc.name.startswith(('sinv', 'SINV')):
            message = f"{customer}, {voucher_no} amounting Tk.{bill_amount}/= generated on {posting_date},{posting_time}. Balance:Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True)}/=[ETL]"
            send_sms_frappe(mobile_number,message,success_msg=False)
        if doc.name.startswith(('rinv', 'RINV')):
            message = f"{customer}, Tk.{abs(bill_amount)}/= sales returned for {return_voucher} on {posting_date},{posting_time}. Balance:Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True)}/=[ETL]"
            send_sms_frappe(mobile_number,message,success_msg=False)
    if method == "on_cancel":
        if doc.name.startswith(('sinv', 'SINV')):
            message = f"Dear {customer}, {voucher_no} amounting Tk.{bill_amount}/= has been canceled. Balance:Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True)}/=.[ETL]"
            send_sms_frappe(mobile_number,message ,success_msg=False)
        if doc.name.startswith(('rinv', 'RINV')):
            message = f"Dear {customer}, {voucher_no} amounting Tk.{bill_amount}/= has been canceled. Balance:Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True)}/=.[ETL]"
            send_sms_frappe(mobile_number,message ,success_msg=False)

        
def send_email_notification(doc,method):
    attachment_permission = get_attachment_permission(doc.doctype)
    customer_details = get_customer_details(doc.customer,outstanding_balance=True)
    customer=doc.customer_name
    email_id = customer_details.get('notified_email_list')
    if len(email_id) == 0:
        return
    outstanding_balance = customer_details.get('outstanding_balance')
    voucher_no = doc.name
    bill_amount = doc.grand_total
    return_voucher = doc.return_against
    pdf_data = frappe.attach_print(doc.doctype, doc.name, print_format="Excel Sales Invoice", file_name=f"{doc.name}.pdf")
    posting_date = format_date_to_custom(doc.posting_date ,need_year=True) if method == "on_submit" else format_date_to_custom_cancel(doc.modified ,need_year=True)
    sales_person_email = customer_details.get('sales_person_email')
    sales_person_name = customer_details.get('sales_person_name')
    sales_person_mobile_no = customer_details.get('sales_person_mobile_no')
    posting_time = format_time_to_ampm(doc.modified,is_mail=True)
    if method == "on_submit":
        if doc.name.startswith(('sinv', 'SINV')):
            subject = "ETL - Sales Invoice Notification"
            message = f"""
            <p>Dear <b>{customer}</b>,</p>
            <p>We would like to inform you that a new invoice {voucher_no} for the amount of Taka <b>{bill_amount}/=</b> has been generated on {posting_date} at {posting_time}. Your current outstanding balance is Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
            <p>If you have any requirement or need assistance, please feel free to reach out {'your KAM' if not sales_person_mobile_no and not sales_person_email else 'to'} <b>{sales_person_name}</b> {'.' if not sales_person_mobile_no and not sales_person_email else ''}
            {f'at {sales_person_mobile_no}' if sales_person_mobile_no  else ''}
            {f'or email' if sales_person_email and sales_person_mobile_no else ''}
            {f'at {sales_person_email}' if sales_person_email  else ''} </p>
            <p>For more information on our products and services, please visit our website: 
                <a href="http://www.excelbd.com" target="_blank">www.excelbd.com</a> 
                or on Facebook: 
                <a href="https://www.facebook.com/ExcelTechnologiesLtd" target="_blank">Excel Technologies Ltd</a>
            </p>
            <p>We truly appreciate your continued business and partnership.</p>
            <br>
            <p>Sincerely,</p>
            <p>Excel Technologies Ltd.</p>
            <p style="color: #888; font-size: 12px; font-style: italic;">
                This is a system generated email. Please do not reply, as responses to this email are not monitored.
                </p>
            """
            frappe.sendmail(recipients=email_id, subject=subject, message=message ,attachments=[pdf_data] if attachment_permission else [])
           
        if doc.name.startswith(('rinv', 'RINV')):
            subject = "ETL - Sales Return Notification"
            message = f"""
                <p>Dear <b>{customer}</b>,</p>
                <p>We have adjusted Taka <b>{abs(bill_amount)}/=</b> to your ledger by returning against sales invoice {return_voucher} on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
                <p>If you have any requirement or need assistance, please feel free to reach out {'your KAM' if not sales_person_mobile_no and not sales_person_email else 'to'} <b>{sales_person_name}</b> {'.' if not sales_person_mobile_no and not sales_person_email else ''}
                {f'at {sales_person_mobile_no}' if sales_person_mobile_no  else ''}
                {f'or email' if sales_person_email and sales_person_mobile_no else ''}
                {f'at {sales_person_email}' if sales_person_email  else ''} </p>
                <p>For more information on our products and services, please visit our website: 
                <a href="http://www.excelbd.com" target="_blank">www.excelbd.com</a> 
                or on Facebook: 
                <a href="https://www.facebook.com/ExcelTechnologiesLtd" target="_blank">Excel Technologies Ltd</a>
                </p>
                <p>We truly appreciate your continued business and partnership.</p>
                <br>
                <p>Sincerely,</p>
                <p>Excel Technologies Ltd.</p>
                <p style="color: #888; font-size: 12px; font-style: italic;">
                    This is a system generated email. Please do not reply, as responses to this email are not monitored.
                </p>
                
            """
            frappe.sendmail(recipients=email_id, subject=subject, message=message,attachments=[pdf_data] if attachment_permission else [])
        # frappe.sendmail(
        #     recipients=[email_id],
        #     subject=subject,
        #     message=message
        # )
    if method == "on_cancel":
        if doc.name.startswith(('sinv', 'SINV')):
            subject = "ETL - Cancellation Notification"
            message = f"""
                <p>Dear <b>{customer}</b>,</p>
                <p>{voucher_no} amounting Taka <b>{abs(bill_amount)}/=</b> has been canceled on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
                <p>If you have any requirement or need assistance, please feel free to reach out {'your KAM' if not sales_person_mobile_no and not sales_person_email else 'to'} <b>{sales_person_name}</b> {'.' if not sales_person_mobile_no and not sales_person_email else ''}
                {f'at {sales_person_mobile_no}' if sales_person_mobile_no  else ''}
                {f'or email' if sales_person_email and sales_person_mobile_no else ''}
                {f'at {sales_person_email}' if sales_person_email  else ''} </p>
            <p>For more information on our products and services, please visit our website: 
                <a href="http://www.excelbd.com" target="_blank">www.excelbd.com</a> 
                or on Facebook: 
                <a href="https://www.facebook.com/ExcelTechnologiesLtd" target="_blank">Excel Technologies Ltd</a>
            </p>
            <p>We truly appreciate your continued business and partnership.</p>
            <br>
            <p>Sincerely,</p>
            <p>Excel Technologies Ltd.</p>
            <p style="color: #888; font-size: 12px; font-style: italic;">
                This is a system generated email. Please do not reply, as responses to this email are not monitored.
            </p>
            """
            frappe.sendmail(recipients=email_id, subject=subject, message=message)

        if doc.name.startswith(('rinv', 'RINV')):
            subject = "ETL - Cancellation Notification"
            message = f"""
            <p>Dear <b>{customer}</b>,</p>
            <p>{voucher_no} amounting Taka <b>{abs(bill_amount)}/=</b> has been canceled on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
            <p>If you have any requirement or need assistance, please feel free to reach out {'your KAM' if not sales_person_mobile_no and not sales_person_email else 'to'} <b>{sales_person_name}</b> {'.' if not sales_person_mobile_no and not sales_person_email else ''}
            {f'at {sales_person_mobile_no}' if sales_person_mobile_no  else ''}
            {f'or email' if sales_person_email and sales_person_mobile_no else ''}
            {f'at {sales_person_email}' if sales_person_email  else ''} </p>
            <p>For more information on our products and services, please visit our website: 
                <a href="http://www.excelbd.com" target="_blank">www.excelbd.com</a> 
                or on Facebook: 
                <a href="https://www.facebook.com/ExcelTechnologiesLtd" target="_blank">Excel Technologies Ltd</a>
            </p>
            <p>We truly appreciate your continued business and partnership.</p>
            <br>
            <p>Sincerely,</p>
            <p>Excel Technologies Ltd.</p>
            <p style="color: #888; font-size: 12px; font-style: italic;">
                This is a system generated email. Please do not reply, as responses to this email are not monitored.
            </p>
            """
            frappe.sendmail(recipients=email_id, subject=subject, message=message)

