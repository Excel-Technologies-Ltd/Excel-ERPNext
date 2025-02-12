import frappe
from frappe.core.doctype.sms_settings.sms_settings import send_sms  as send_sms_frappe
from excel_erpnext.doc_events.common.common import get_customer_details,  check_allow_on_doctype, format_in_bangladeshi_currency, get_notification_permission,format_time_to_ampm,format_date_to_custom,format_date_to_custom_cancel,get_attachment_permission,send_email_to_cm,send_cm_mail_from_payment_entry,generate_transaction_table,generate_email_footer,generate_contact_info
def send_notification(doc, method=None):
    
    if doc.payment_type != "Receive":
        return
    if doc.party_type != "Customer":
        return
    if method == "on_submit":
        send_cm_mail_from_payment_entry(doc,doc.name)
    settings = frappe.get_doc("ArcApps Alert Settings")
    sms_enabled = bool(settings.excel_sms)
    email_enabled = bool(settings.excel_email)
    
    allow_on_doctype= check_allow_on_doctype()
    if method == "on_submit" and not allow_on_doctype['payment_entry']:
        return
    if method == "on_cancel" and not allow_on_doctype['cancellation_all']:
        return
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
        paid_amount = doc.paid_amount
        paid_amount=format_in_bangladeshi_currency(paid_amount)
        posting_date = format_date_to_custom(doc.posting_date) if method == "on_submit" else format_date_to_custom_cancel(doc.modified)
        posting_time = format_time_to_ampm(doc.modified)
        if method == "on_submit":
            message = f"{party_name},Tk.{paid_amount}/= has been deposited/received on {posting_date},{posting_time}. Outstanding: Tk.{format_in_bangladeshi_currency(outstanding_balance,sms=True)}/=[ETL]"
            send_sms_frappe(mobile_number,message,success_msg=False)
        if method == "on_cancel" :
            message = f"Dear {party_name}, rectified the previous transaction amount Tk.{paid_amount}/=. Balance Tk. {format_in_bangladeshi_currency(outstanding_balance,sms=True)}/=.[ETL]"
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
        # brands = [entry.brand for entry in custom_brand_wise_payments]
        # if len(brands) == 0:
        #     brand_list = ""
        # else:
        #     brand_list = f" against [{', '.join(brands)}]"
        pdf_data = frappe.attach_print(doc.doctype, doc.name, print_format="Excel Payment Notify", file_name=f"{doc.name}.pdf")

        outstanding_balance = customer_details.get('outstanding_balance')
        outstanding_balance=format_in_bangladeshi_currency(outstanding_balance)
        # voucher_no = doc.name
        # mode_of_payment = doc.mode_of_payment
        paid_amount = doc.paid_amount
        paid_amount=format_in_bangladeshi_currency(paid_amount)
        posting_date = format_date_to_custom(doc.posting_date ,need_year=True) if method == "on_submit" and doc.posting_date else format_date_to_custom_cancel(doc.modified,need_year=True)
        
        sales_person_email = customer_details.get('sales_person_email')
        sales_person_name = customer_details.get('sales_person_name')
        sales_person_mobile_no = customer_details.get('sales_person_mobile_no')
        posting_time = format_time_to_ampm(doc.modified,is_mail=True)
        support_content = generate_contact_info(sales_person_name, sales_person_mobile_no, sales_person_email)
        footer_content = generate_email_footer()
        # need to change on_submit here
        if method == "on_submit":
            transaction_data = {
                "Customer Name": party_name,
                "Transaction Date": f"{posting_date} {posting_time}",
                "Transaction Amount": paid_amount,
                "Transaction Type": "Payment Entry",
                "Outstanding Amount": outstanding_balance
            }
            table_content = generate_transaction_table(transaction_data)
            subject = "ETL - Payment Notification"
            message = f"""
            {table_content}
            {support_content}
            {generate_email_footer()}
            
            """
            frappe.sendmail(recipients=email_id, subject=subject, message=message, attachments=[pdf_data] if attachment_permission else [])
                
        if method == "on_cancel":
            transaction_data = {
                "Customer Name": party_name,
                "Transaction Date": f"{posting_date} {posting_time}",
                "Transaction Amount": abs(paid_amount),
                "Transaction Type": "Payment Entry",
                "Outstanding Amount": outstanding_balance
            }
            subject = "ETL - Cancellation Notification"
            message = f"""
            {table_content}
            {support_content}
            {footer_content}
            """

            frappe.sendmail(recipients=email_id, subject=subject, message=message)



