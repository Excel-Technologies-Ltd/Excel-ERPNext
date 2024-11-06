import frappe
from frappe.core.doctype.sms_settings.sms_settings import send_sms  as send_sms_frappe
from excel_erpnext.doc_events.common.common import get_customer_details, get_notified_mobile_no, get_notified_email, get_customer_outstanding_balance, format_in_bangladeshi_currency, get_notification_permission,format_time_to_ampm,format_date_to_custom,format_date_to_custom_cancel,get_attachment_permission
def send_notification(doc, method=None):
    
    if doc.payment_type != "Receive":
        return
    if doc.party_type != "Customer":
        return
    settings = frappe.get_doc("ArcApps Alert Settings")
    sms_enabled = bool(settings.excel_sms)
    email_enabled = bool(settings.excel_email)
    notification_permission = get_notification_permission(doc.party)
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
    if doc.party_type == "Customer":
        customer_details = get_customer_details(doc.party,outstanding_balance=True)
        party_name=doc.party_name
        mobile_number = customer_details.get('notified_phone_no_list')
        if len(mobile_number) == 0:
            return
        outstanding_balance = customer_details.get('outstanding_balance')
        voucher_no = doc.name
        mode_of_payment = doc.mode_of_payment
        
        paid_amount = doc.paid_amount
        posting_date = format_date_to_custom(doc.posting_date) if method == "on_submit" else format_date_to_custom_cancel(doc.modified)
        posting_time = format_time_to_ampm(doc.modified)
        if method == "on_submit":
            message = f"{party_name},Tk.{paid_amount}/=paid by {voucher_no} on {posting_date},{posting_time}[{mode_of_payment}]. Balance: Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True)}/=[ETL]"
            send_sms_frappe(mobile_number,message,success_msg=False)
        if method == "on_cancel":
            message = f"Dear {party_name}, {voucher_no} amounting Tk.{paid_amount}/= has been canceled. Balance Tk. {format_in_bangladeshi_currency(outstanding_balance,sms=True)}/=. [ETL]"
            send_sms_frappe(mobile_number,message,success_msg=False)
        
def send_email_notification(doc,method):
    if doc.party_type == "Customer":
        attachment_permission = get_attachment_permission(doc.doctype)
        customer_details = get_customer_details(doc.party,outstanding_balance=True)
        party_name=doc.party_name
        email_id = customer_details.get('notified_email_list')
        if len(email_id) == 0:
            return
        custom_brand_wise_payments=doc.custom_brand_wise_payments
        brands = [entry.brand for entry in custom_brand_wise_payments]
        if len(brands) == 0:
            brand_list = ""
        else:
            brand_list = f" against [{', '.join(brands)}]"
        pdf_data = frappe.attach_print(doc.doctype, doc.name, print_format="Excel Payment Notify", file_name=f"{doc.name}.pdf")

        outstanding_balance = customer_details.get('outstanding_balance')
        voucher_no = doc.name
        mode_of_payment = doc.mode_of_payment
        paid_amount = doc.paid_amount
        posting_date = format_date_to_custom(doc.posting_date ,need_year=True) if method == "on_submit" and doc.posting_date else format_date_to_custom_cancel(doc.modified,need_year=True)
        
        sales_person_email = customer_details.get('sales_person_email')
        sales_person_name = customer_details.get('sales_person_name')
        sales_person_mobile_no = customer_details.get('sales_person_mobile_no')
        posting_time = format_time_to_ampm(doc.modified,is_mail=True)
        if method == "on_submit":
            subject = "ETL - Payment Notification"
            message = f"""
                <p>Dear <b>{party_name}</b>,</p>
                <p>Thank you for your payment of Taka <b>{paid_amount}/=</b> via {voucher_no} {brand_list} on {posting_date} at {posting_time} by <b>[{mode_of_payment}]</b>. Your current outstanding balance is Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
                <p>If you have any requirement or need assistance, please feel free to reach out {'your KAM' if not sales_person_mobile_no and not sales_person_email else 'to'} <b>{sales_person_name}</b> {'.' if not sales_person_mobile_no and not sales_person_email else ''}
                {f'at <b>{sales_person_mobile_no}</b>' if sales_person_mobile_no  else ''}
                {f'or email' if sales_person_email and sales_person_mobile_no else ''}
                {f'at <b>{sales_person_email}</b>' if sales_person_email  else ''} </p>
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
           
            frappe.sendmail(recipients=email_id, subject=subject, message=message, attachments=[pdf_data] if attachment_permission else [])
        if method == "on_cancel":
            subject = "ETL - Cancellation Notification"
            message = f"""
            <p>Dear <b>{party_name}</b>,</p>
            <p>{voucher_no} amounting Taka <b>{(paid_amount)}/=</b> has been canceled on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
            <p>If you have any requirement or need assistance, please feel free to reach out {'your KAM' if not sales_person_mobile_no and not sales_person_email else 'to'} <b>{sales_person_name}</b> {'.' if not sales_person_mobile_no and not sales_person_email else ''}
            {f'at <b>{sales_person_mobile_no}</b>' if sales_person_mobile_no  else ''}
            {f'or email' if sales_person_email and sales_person_mobile_no else ''}
            {f'at <b>{sales_person_email}</b>' if sales_person_email  else ''} </p>
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



