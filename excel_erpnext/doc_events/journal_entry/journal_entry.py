import frappe
from frappe.core.doctype.sms_settings.sms_settings import send_sms  as send_sms_frappe
from excel_erpnext.doc_events.common.common import get_customer_details, get_notified_mobile_no, get_notified_email, get_customer_outstanding_balance, format_in_bangladeshi_currency, get_notification_permission,format_time_to_ampm,format_date_to_custom,format_date_to_custom_cancel,get_attachment_permission
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
        notification_permission = get_notification_permission(account.get('party'))
        settings = frappe.get_doc("ArcApps Alert Settings")
        sms_enabled = bool(settings.excel_sms)
        email_enabled = bool(settings.excel_email)
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
        message = f"{customer_name},Tk.{credit_amount}/= adjusted by {voucher_no} to {user_remarks} on {posting_date},{posting_time}.Balance:Tk.{outstanding_balance}/=[ETL]"
        cancel_message = f"Dear {customer_name}, {voucher_no} amounting Tk.{credit_amount}/= has been canceled. Balance: Tk. {format_in_bangladeshi_currency(outstanding_balance)}/=.[ETL]"
        if method == "on_submit":
            send_sms_frappe(mobile_number, message,success_msg=False)
        if method == "on_cancel":
            send_sms_frappe(mobile_number, cancel_message ,success_msg=False)  
        return 
    # Condition: Ledger Debit
    if account_name == '10203 - Accounts Receivable - ETL' and party_type == 'Customer' and debit_amount != 0:
        message = f"{customer_name},Tk.{debit_amount}/= adjusted by {voucher_no} for {user_remarks} on {posting_date},{posting_time}.Balance:Tk.{outstanding_balance}/=[ETL]"
        cancel_message = f"Dear {customer_name}, {voucher_no} amounting Tk.{debit_amount}/= has been canceled. Balance: Tk. {format_in_bangladeshi_currency(outstanding_balance)}/=.[ETL]"
        if method == "on_submit":
            send_sms_frappe(mobile_number, message ,success_msg=False)
        if method == "on_cancel":
            send_sms_frappe(mobile_number, cancel_message ,success_msg=False)
        return 
    # Condition: Credit Note
    if doc.voucher_type == 'Credit Note':
        message = f"{customer_name},Tk.{credit_amount}/= adjusted by {voucher_no}“{excel_product_team}” on {posting_date},{posting_time}.Balance:Tk.{outstanding_balance}/=[ETL]"
        cancel_message = f"Dear {customer_name}, {voucher_no} amounting Tk.{credit_amount}/= has been canceled. Balance: Tk. {format_in_bangladeshi_currency(outstanding_balance)}/=.[ETL]"
        # send_sms_frappe(mobile_number, message)
        if method == "on_submit":
            send_sms_frappe(mobile_number, message ,success_msg=False)
        if method == "on_cancel":
            send_sms_frappe(mobile_number, cancel_message ,success_msg=False)
        return 
    # Condition: Receive
    if doc.voucher_type == 'Receive Entry':
        message = f"{customer_name},Tk.{credit_amount}/= received by {voucher_no} on {posting_date},{posting_time}.Balance:Tk.{outstanding_balance}/=[ETL]"
        cancel_message = f"Dear {customer_name}, {voucher_no} amounting Tk.{credit_amount}/= has been canceled. Balance: Tk. {format_in_bangladeshi_currency(outstanding_balance)}/=.[ETL]"
        # send_sms_frappe(mobile_number, message)
        if method == "on_submit":
            send_sms_frappe(mobile_number, message,success_msg=False)
        if method == "on_cancel":
            send_sms_frappe(mobile_number, cancel_message,success_msg=False)
        return 
def send_email_notification(doc, method, account):
    attachment_permission = get_attachment_permission(doc.doctype)
    account_name = account.get('account')
    party_type = account.get('party_type')
    customer = account.get('party')
    customer_details = get_customer_details(customer, outstanding_balance=True)
    email_id = customer_details.get('notified_email_list')
    if len(email_id) == 0:
        return
    outstanding_balance = customer_details.get('outstanding_balance')
    customer_name = customer_details.get('customer_name')
    sales_person_email = customer_details.get('sales_person_email')
    sales_person_name = customer_details.get('sales_person_name')
    sales_person_mobile_no = customer_details.get('sales_person_mobile_no')
    voucher_no = doc.name
    credit_amount=account.get('credit_in_account_currency')
    debit_amount=account.get('debit_in_account_currency')
    excel_product_team= account.get('excel_product_team')
    user_remarks= doc.excel_scheme_name
    posting_date = format_date_to_custom(doc.posting_date, need_year=True) if method == "on_submit" else format_date_to_custom_cancel(doc.modified, need_year=True)
    posting_time = format_time_to_ampm(doc.modified ,is_mail=True)
    pdf_data = frappe.attach_print(doc.doctype, doc.name, print_format="Excel Journal Entry", file_name=f"{doc.name}.pdf")




    if account.get('is_rebate')== "Rebate":
        subject = "[ETL] Ledger Transaction Notification"
        message = f"""Dear <b>{customer_name}</b>,<br>
        We have adjusted Taka <b>{credit_amount}/=</b> to your ledger with {voucher_no} against “{user_remarks}” on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b>.
        <br><br>
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
        cancel_subject = "[ETL] Cancellation Alert"
        cancel_message = f"""Dear <b>{customer_name}</b>,<br>
        <p>{voucher_no} amounting Taka <b>{(debit_amount)}/=</b> has been canceled on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
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
        # frappe.sendmail(recipients=[email_id], subject=subject, message=message)
        if method == "on_submit":
            frappe.sendmail(recipients=email_id, subject=subject, message=message ,attachments=[pdf_data] if attachment_permission else [])
        if method == "on_cancel":
            frappe.sendmail(recipients=email_id, subject=cancel_subject, message=cancel_message)
        return  
    if account_name == '10203 - Accounts Receivable - ETL' and party_type == 'Customer' and debit_amount != 0:
        subject = "[ETL] Ledger Transaction Notification"
        message = f"""Dear <b>{customer_name}</b>,<br>
        We have adjusted Taka <b>{debit_amount}/=</b> to your ledger with {voucher_no} due to “{user_remarks}” on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b>.
        <br><br>
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
        cancel_subject = "[ETL] Cancellation Alert"
        cancel_message  = f"""
            <p>Dear <b>{customer_name}</b>,</p>
            <p>{voucher_no} amounting Taka <b>{(debit_amount)}/=</b> has been canceled on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
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
        if method == "on_submit":
            frappe.sendmail(recipients=email_id, subject=subject, message=message ,attachments=[pdf_data] if attachment_permission else [])
        if method == "on_cancel":
            frappe.sendmail(recipients=email_id, subject=cancel_subject, message=cancel_message)
        return 
    # Static Email Content for Each Condition
    if doc.voucher_type == 'Credit Note':
        subject = "[ETL] Ledger Transaction Notification"
        message = f"""Dear <b>{customer_name}</b>,<br>
        We have adjusted Taka <b>{credit_amount}/=</b> to your ledger with credit note {voucher_no} against “{excel_product_team}” on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b>.
        <br><br>
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
        cancel_subject = "[ETL] Cancellation Alert"
        cancel_message  = f"""
            <p>Dear <b>{customer_name}</b>,</p>
            <p>{voucher_no} amounting Taka <b>{(credit_amount)}/=</b> has been canceled on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
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
        if method == "on_submit":
            frappe.sendmail(recipients=email_id, subject=subject, message=message,attachments=[pdf_data] if attachment_permission else [])
        if method == "on_cancel":
            frappe.sendmail(recipients=email_id, subject=cancel_subject, message=cancel_message)
        return 
    if doc.voucher_type == 'Receive Entry':
        # on_submit
        subject = "[ETL] Payment Notification"
        message = f"""Dear <b>{customer_name}</b>,<br>
        We have adjusted Taka <b>{credit_amount}/=</b> to your ledger with {voucher_no} on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b>.
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
        # frappe.sendmail(recipients=[email_id], subject=subject, message=message)
        # on_cancel
        cancel_subject = "[ETL] Cancellation Alert"
        cancel_message = f"""Dear <b>{customer_name}</b>,<br>
        <p>{voucher_no} amounting Taka <b>{(credit_amount)}/=</b> has been canceled on {posting_date} at {posting_time}. Your updated balance is now Taka <b>{format_in_bangladeshi_currency(outstanding_balance)}/=</b></p>
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
        if method == "on_submit":
            frappe.sendmail(recipients=email_id, subject=subject, message=message,attachments=[pdf_data] if attachment_permission else [])
        if method == "on_cancel":
            frappe.sendmail(recipients=email_id, subject=cancel_subject, message=cancel_message)
        return 





