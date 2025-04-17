import frappe
from frappe.core.doctype.sms_settings.sms_settings import send_sms  as send_sms_frappe
from excel_erpnext.doc_events.common.common import get_customer_details,  check_allow_on_doctype, format_in_bangladeshi_currency, get_notification_permission,format_time_to_ampm,format_date_to_custom,format_date_to_custom_cancel,get_attachment_permission,generate_transaction_table,generate_email_footer,generate_contact_info
def send_notification(doc, method=None):
    
    if not doc.name.startswith(('sinv', 'SINV','rinv','RINV')):
        return
    settings = frappe.get_doc("ArcApps Alert Settings")
    sms_enabled = bool(settings.excel_sms)
    email_enabled = bool(settings.excel_email)
   
    allow_on_doctype= check_allow_on_doctype()
    if method == "on_submit" and doc.name.startswith(('sinv', 'SINV')) and not allow_on_doctype['sales_invoice']:
        return
    if method == "on_submit" and doc.name.startswith(('rinv', 'RINV')) and not allow_on_doctype['sales_return']:
        return
    if method == "on_cancel" and not allow_on_doctype['cancellation_all']:
        return
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
    
    bill_amount = doc.grand_total
    
    posting_date =format_date_to_custom(doc.posting_date) if method == "on_submit" and doc.posting_date else format_date_to_custom_cancel(doc.modified)
    
    posting_time = format_time_to_ampm(doc.modified)
    if method == "on_submit":
        if doc.name.startswith(('sinv', 'SINV')):
            message = f"{customer}, invoice amount Tk.{format_in_bangladeshi_currency(bill_amount,sms=True)} generated to your ledger on {posting_date},{posting_time}. Outstanding:Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True,is_abs=False)}-ETL"
            send_sms_frappe(mobile_number,message,success_msg=False)
        if doc.name.startswith(('rinv', 'RINV')):
            message = f"{customer}, return invoice amount Tk.{format_in_bangladeshi_currency(bill_amount,sms=True)} generated to your ledger on {posting_date},{posting_time}. Outstanding:Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True,is_abs=False)}-ETL"
            send_sms_frappe(mobile_number,message,success_msg=False)
    if method == "on_cancel":
        if doc.name.startswith(('sinv', 'SINV')):
            message = f"Dear {customer}, rectified the previous transaction amount Tk.{format_in_bangladeshi_currency(bill_amount,sms=True)}. Outstanding:Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True,is_abs=False)}.-ETL"
            send_sms_frappe(mobile_number,message ,success_msg=False)
        if doc.name.startswith(('rinv', 'RINV')):
            message = f"Dear {customer}, rectified the previous transaction amount Tk.{format_in_bangladeshi_currency(bill_amount,sms=True)}. Outstanding:Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True,is_abs=False)}.-ETL"
            send_sms_frappe(mobile_number,message ,success_msg=False)

        
def send_email_notification(doc,method):
    attachment_permission = get_attachment_permission(doc.doctype)
    customer_details = get_customer_details(doc.customer,outstanding_balance=True)
    customer=doc.customer_name
    email_id = customer_details.get('notified_email_list')
    if len(email_id) == 0:
        return
    outstanding_balance = customer_details.get('outstanding_balance')
    outstanding_balance=format_in_bangladeshi_currency(outstanding_balance,is_abs=False)
    voucher_no = doc.name
    bill_amount = doc.grand_total
    bill_amount=format_in_bangladeshi_currency(bill_amount)
    return_voucher = doc.return_against
    pdf_data = frappe.attach_print(doc.doctype, doc.name, print_format="Excel Sales Invoice", file_name=f"{doc.name}.pdf")
    posting_date = format_date_to_custom(doc.posting_date ,need_year=True) if method == "on_submit" else format_date_to_custom_cancel(doc.modified ,need_year=True)
    sales_person_email = customer_details.get('sales_person_email')
    sales_person_name = customer_details.get('sales_person_name')
    sales_person_mobile_no = customer_details.get('sales_person_mobile_no')
    posting_time = format_time_to_ampm(doc.modified,is_mail=True)
    support_content = generate_contact_info(sales_person_name, sales_person_mobile_no, sales_person_email)
    if method == "on_submit":
        if doc.name.startswith(('sinv', 'SINV')):
            transaction_data = {
                "Customer Name": customer,
                "Transaction Date": f"{posting_date}, {posting_time}" ,
                "Transaction Amount": bill_amount,
                "Transaction Type": "Sales Invoice",
                "Outstanding Amount": outstanding_balance
            }

            table_content = generate_transaction_table(transaction_data)
            subject = "ETL - Sales Invoice Notification"
            message = f"""
            {table_content}
            {support_content}
            {generate_email_footer()}
            """
            frappe.sendmail(recipients=email_id, subject=subject, message=message ,attachments=[pdf_data] if attachment_permission else [])
           
        if doc.name.startswith(('rinv', 'RINV')):
            
            transaction_data = {
                "Customer Name": customer,
                "Transaction Date": f"{posting_date}, {posting_time}" ,
                "Transaction Amount": bill_amount,
                "Transaction Type": "Sales Return",
                "Outstanding Amount": outstanding_balance
            }
            table_content = generate_transaction_table(transaction_data)
            subject = "ETL - Sales Return Notification"
            message = f"""
            {table_content}
            {support_content}
            {generate_email_footer()}
            """
            frappe.sendmail(recipients=email_id, subject=subject, message=message,attachments=[pdf_data] if attachment_permission else [])
        # frappe.sendmail(
        #     recipients=[email_id],
        #     subject=subject,
        #     message=message
        # )
    if method == "on_cancel":
        if doc.name.startswith(('sinv', 'SINV')):
            transaction_data = {
                "Customer Name": customer,
                "Transaction Date": f"{posting_date}, {posting_time}",
                "Transaction Amount": bill_amount,
                "Transaction Type": "Sales Invoice",
                "Outstanding Amount": outstanding_balance
            }
            table_content = generate_transaction_table(transaction_data)
            subject = "ETL - Cancellation Notification"
            message = f"""
            {table_content}
            {support_content}
            {generate_email_footer()}
            """
            frappe.sendmail(recipients=email_id, subject=subject, message=message)

        if doc.name.startswith(('rinv', 'RINV')):
            
            transaction_data = {
                "Customer Name": customer,
                "Transaction Date": f"{posting_date}, {posting_time}",
                "Transaction Amount": bill_amount,
                "Transaction Type": "Sales Return",
                "Outstanding Amount": outstanding_balance
            }
            table_content = generate_transaction_table(transaction_data)
            subject = "ETL - Cancellation Notification"
            message = f"""
            {table_content}
            {support_content}
            {generate_email_footer()}
            """
            frappe.sendmail(recipients=email_id, subject=subject, message=message)