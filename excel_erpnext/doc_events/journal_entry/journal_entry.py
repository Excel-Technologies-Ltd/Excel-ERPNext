import frappe
from frappe.core.doctype.sms_settings.sms_settings import send_sms  as send_sms_frappe
from excel_erpnext.doc_events.common.common import get_customer_details,  check_allow_on_doctype, format_in_bangladeshi_currency, get_notification_permission,format_time_to_ampm,format_date_to_custom,format_date_to_custom_cancel,get_attachment_permission,send_cm_mail_from_journal_entry,generate_transaction_table,generate_email_footer,generate_contact_info
def send_notification(doc, method=None):
    
    accounts=doc.accounts
    account_condition_met = any(entry.get("account") == "3020702 - Provision for Sales Rebate & Benefit - ETL" for entry in accounts)
    customer_condition_met = any(entry.get("party_type") == "Customer" for entry in accounts)

    if account_condition_met and customer_condition_met:
        modified_accounts = [
            {**entry.as_dict(), "is_rebate": "Rebate"} if entry.party_type == "Customer" else entry.as_dict()
            for entry in accounts
        ]
    else:
        modified_accounts = [entry.as_dict() for entry in accounts]
    
    customer_accounts = [account for account in modified_accounts if account.get("party_type") == "Customer" and account.get("party")]
    if len(customer_accounts) == 0:
        return
    for account in customer_accounts:
        if method == 'on_submit' and account.get('party_type') == "Customer" and account.get('account') == "10203 - Accounts Receivable - ETL":
            send_cm_mail_from_journal_entry(account,doc.name)   
        
        settings = frappe.get_doc("ArcApps Alert Settings")
        sms_enabled = bool(settings.excel_sms)
        email_enabled = bool(settings.excel_email)
        allow_on_doctype= check_allow_on_doctype()
        if method == "on_submit" and account.get('is_rebate')== "Rebate" and not allow_on_doctype['benefit_journal']:
            return
        if method == "on_submit" and account.get('account') == '10203 - Accounts Receivable - ETL' and account.get('party_type') == 'Customer' and account.get('debit_in_account_currency') != 0 and not allow_on_doctype['debit_adjustment_journal']:
            return
        if method == "on_submit" and doc.voucher_type == 'Credit Note' and not allow_on_doctype['credit_note_journal']:
            return
        if method == "on_submit" and doc.voucher_type == 'Receive Entry' and not allow_on_doctype['receive_journal']:
            return
        if method == "on_cancel" and not allow_on_doctype['cancellation_all']:
            return
        notification_permission = get_notification_permission(account.get('party'))
        if notification_permission.get('sms'):
            send_sms_notification(doc, method,account)
        if notification_permission.get('email'):
            send_email_notification(doc, method,account)
        if notification_permission.get('both'):
            if sms_enabled:
                send_sms_notification(doc, method,account)
            if email_enabled:
                send_email_notification(doc, method,account)
def send_sms_notification(doc, method, account):

    account_name = account.get('account')
    party_type = account.get('party_type')
    customer = account.get('party')
    customer_details = get_customer_details(customer, outstanding_balance=True)
    mobile_number = customer_details.get('notified_phone_no_list')
    if len(mobile_number) == 0:
        return

    outstanding_balance = customer_details.get('outstanding_balance')
    outstanding_balance=format_in_bangladeshi_currency(outstanding_balance,is_abs=False)
    customer_name = customer_details.get('customer_name')
    voucher_no = doc.name
    credit_amount=account.get('credit_in_account_currency')
    debit_amount=account.get('debit_in_account_currency')
    excel_product_team= account.get('excel_product_team')
    user_remarks= doc.excel_scheme_name 
    posting_date = format_date_to_custom(doc.posting_date) if method == "on_submit" else format_date_to_custom_cancel(doc.modified)
    posting_time = format_time_to_ampm(doc.modified)
    # Condition: Rebate 
    if account.get('is_rebate')== "Rebate":
        message = f"{customer_name},Tk.{format_in_bangladeshi_currency(credit_amount,sms=True)} adjusted to your ledger on {posting_date},{posting_time}. Outstanding:Tk.{outstanding_balance}[ETL]"
        cancel_message = f"Dear {customer_name}, rectified the previous transaction amount Tk.{format_in_bangladeshi_currency(credit_amount,sms=True)}. Outstanding:Tk.{outstanding_balance}.[ETL]"
        if method == "on_submit":
            send_sms_frappe(mobile_number, message,success_msg=False)
        if method == "on_cancel":
            send_sms_frappe(mobile_number, cancel_message ,success_msg=False)  
        return 
    # Condition: Ledger Debit = Ledger Adjustment
    if account_name == '10203 - Accounts Receivable - ETL' and party_type == 'Customer' and debit_amount != 0:
        message = f"{customer_name},Tk.{format_in_bangladeshi_currency(debit_amount,sms=True)} adjusted to your ledger on {posting_date},{posting_time}. Outstanding:Tk.{outstanding_balance}[ETL]"
        cancel_message = f"Dear {customer_name}, rectified the previous transaction amount Tk.{format_in_bangladeshi_currency(debit_amount,sms=True)}. Outstanding:Tk.{outstanding_balance}.[ETL]"
        if method == "on_submit":
            send_sms_frappe(mobile_number, message ,success_msg=False)
        if method == "on_cancel":
            send_sms_frappe(mobile_number, cancel_message ,success_msg=False)
        return 
    # Condition: Credit Note
    if doc.voucher_type == 'Credit Note':
        message = f"{customer_name},Tk.{format_in_bangladeshi_currency(credit_amount) } adjusted to your ledger on {posting_date},{posting_time}. Outstanding:Tk.{outstanding_balance}[ETL]"
        cancel_message = f"Dear {customer_name}, rectified the previous transaction amount Tk.{format_in_bangladeshi_currency(credit_amount,sms=True)}. Outstanding:Tk.{outstanding_balance}.[ETL]"
        # send_sms_frappe(mobile_number, message)
        if method == "on_submit":
            send_sms_frappe(mobile_number, message ,success_msg=False)
        if method == "on_cancel":
            send_sms_frappe(mobile_number, cancel_message ,success_msg=False)
        return 
    # Condition: Receive Entry = Payment Entry
    if doc.voucher_type == 'Receive Entry':
        message = f"{customer_name},Tk.{format_in_bangladeshi_currency(credit_amount,sms=True)} has been deposited/received on {posting_date},{posting_time}. Outstanding:Tk.{outstanding_balance}[ETL]"
        cancel_message = f"Dear {customer_name}, rectified the previous transaction amount Tk.{format_in_bangladeshi_currency(credit_amount,sms=True)}. Outstanding:Tk.{outstanding_balance}.[ETL]"
        # send_sms_frappe(mobile_number, message)
        if method == "on_submit":
            send_sms_frappe(mobile_number, message,success_msg=False)
        if method == "on_cancel":
            send_sms_frappe(mobile_number, cancel_message,success_msg=False)
        return 
def send_email_notification(doc, method, account):
    allow_on_doctype= check_allow_on_doctype()
    territory= doc.excel_territory
    if territory == "CORPORATE" or territory == "TENDER":
        attachment_permission = get_attachment_permission("Journal Attachment (Corporate)")
    else:
        attachment_permission = get_attachment_permission(doc.doctype)
    account_name = account.get('account')
    party_type = account.get('party_type')
    customer = account.get('party')
    customer_details = get_customer_details(customer, outstanding_balance=True)
    email_id = customer_details.get('notified_email_list')
    if len(email_id) == 0:
        return
    outstanding_balance = customer_details.get('outstanding_balance')
    outstanding_balance=format_in_bangladeshi_currency(outstanding_balance,is_abs=False)
    customer_name = customer_details.get('customer_name')
    sales_person_email = customer_details.get('sales_person_email')
    sales_person_name = customer_details.get('sales_person_name')
    sales_person_mobile_no = customer_details.get('sales_person_mobile_no')
    voucher_no = doc.name
    get_credit_amount=account.get('credit_in_account_currency')
    credit_amount=format_in_bangladeshi_currency(get_credit_amount)
    get_debit_amount=account.get('debit_in_account_currency')
    debit_amount=format_in_bangladeshi_currency(get_debit_amount)
    excel_product_team= account.get('excel_product_team')
    user_remarks= doc.excel_scheme_name
    posting_date = format_date_to_custom(doc.posting_date, need_year=True) if method == "on_submit" else format_date_to_custom_cancel(doc.modified, need_year=True)
    posting_time = format_time_to_ampm(doc.modified ,is_mail=True)
    pdf_data = frappe.attach_print(doc.doctype, doc.name, print_format="Excel Journal Entry", file_name=f"{doc.name}.pdf")
  
    support_content = generate_contact_info(sales_person_name, sales_person_mobile_no, sales_person_email)
    footer_content = generate_email_footer()

    if account.get('is_rebate')== "Rebate":
        transaction_data = {
            "Customer Name": customer_name,
            "Transaction Date": f"{posting_date}, {posting_time}",
            "Transaction Amount":  credit_amount,
            "Transaction Type": "Rebate",
            "Outstanding Amount": outstanding_balance,
        }

        table_content = generate_transaction_table(transaction_data)
        subject = "ETL - Ledger Transaction Notification"
        message = f"""
        {table_content}
        {support_content}
        {footer_content}
        """
        cancel_subject = "ETL - Cancellation Notification"
        cancel_message = f"""
        {table_content}
        {support_content}
        {footer_content}
        """
        # frappe.sendmail(recipients=[email_id], subject=subject, message=message)
        if method == "on_submit":
           
            frappe.sendmail(recipients=email_id, subject=subject, message=message ,attachments=[pdf_data] if attachment_permission else [])
        if method == "on_cancel":
            frappe.sendmail(recipients=email_id, subject=cancel_subject, message=cancel_message)
        return  
    if account_name == '10203 - Accounts Receivable - ETL' and party_type == 'Customer' and get_debit_amount != 0:
        subject = "ETL - Ledger Transaction Notification"
        transaction_data = {
            "Customer Name": customer_name,
            "Transaction Date": f"{posting_date}, {posting_time}",
            "Transaction Amount": debit_amount,
            "Transaction Type": "Ledger Adjustment",
            "Outstanding Amount": outstanding_balance,
        }
        table_content = generate_transaction_table(transaction_data)
        message = f"""
        {table_content}
        {support_content}
        {footer_content}
        """
        cancel_subject = "ETL - Cancellation Alert"
        cancel_message  = f"""
        {table_content}
        {support_content}
        {footer_content}
        """
        if method == "on_submit":
            frappe.sendmail(recipients=email_id, subject=subject, message=message ,attachments=[pdf_data] if attachment_permission else [])
        if method == "on_cancel":
            frappe.sendmail(recipients=email_id, subject=cancel_subject, message=cancel_message)
        return 
    # Static Email Content for Each Condition
    if doc.voucher_type == 'Credit Note' :
        subject = "ETL - Ledger Transaction Notification"
        transaction_data = {
            "Customer Name": customer_name,
            "Transaction Date": f"{posting_date}, {posting_time}",
            "Transaction Amount": credit_amount,
            "Transaction Type": "Credit Note",
            "Outstanding Amount": outstanding_balance,
        }
        table_content = generate_transaction_table(transaction_data)
        message = f"""
        {table_content}
        {support_content}
        {footer_content}
        """
        cancel_subject = "ETL - Cancellation Alert"
        cancel_message  = f"""
        {table_content}
        {support_content}
        {footer_content}
        """
        if method == "on_submit":
            frappe.sendmail(recipients=email_id, subject=subject, message=message,attachments=[pdf_data] if attachment_permission else [])
        if method == "on_cancel":
            frappe.sendmail(recipients=email_id, subject=cancel_subject, message=cancel_message )
        return 
    if doc.voucher_type == 'Receive Entry' :
        subject = "ETL - Payment Notification"
        transaction_data = {
            "Customer Name": customer_name,
            "Transaction Date": f"{posting_date}, {posting_time}",
            "Transaction Amount": credit_amount,
            "Transaction Type": "Payment Entry",
            "Outstanding Amount": outstanding_balance,
        }
        table_content = generate_transaction_table(transaction_data)
        message = f"""
        {table_content}
        {support_content}
        {footer_content}
        """
        # frappe.sendmail(recipients=[email_id], subject=subject, message=message)
        # on_cancel
        cancel_subject = "ETL - Cancellation Alert"
        cancel_message = f"""
        {table_content}
        {support_content}
        {footer_content}
        """
        if method == "on_submit":
            frappe.sendmail(recipients=email_id, subject=subject, message=message,attachments=[pdf_data] if attachment_permission else [])
        if method == "on_cancel":
            frappe.sendmail(recipients=email_id, subject=cancel_subject, message=cancel_message)
        return 





