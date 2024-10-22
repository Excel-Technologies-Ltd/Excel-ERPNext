import frappe
from frappe.core.doctype.sms_settings.sms_settings import send_sms

def send_notification(doc, method=None):
    try:
        settings = frappe.get_doc("ArcApps Alert Settings")
        sms_enabled = bool(settings.sms)
        email_enabled = bool(settings.email)

        frappe.msgprint(f"Notification Type: {doc.notification_type}")

        if doc.notification_type == "SMS" and sms_enabled:
            frappe.msgprint("Sending SMS...")
            send_sms_notification(doc)
        elif doc.notification_type == "Email" and email_enabled:
            frappe.msgprint("Sending Email...")
            send_email_notification(doc)
        elif doc.notification_type == "Both" and sms_enabled and email_enabled:
            frappe.msgprint("Sending Both SMS and Email...")
            send_sms_notification(doc)
            send_email_notification(doc)
        else:
            frappe.msgprint("Notification type or settings not properly configured.")

    except frappe.DoesNotExistError:
        frappe.msgprint("ArcApps Alert Settings not found.")
    except Exception as e:
        frappe.log_error(message=f"Error in send_notification: {str(e)}", title="Notification Error")

def send_sms_notification(doc):
    # Simulate sending SMS here
    frappe.msgprint(f"Sending SMS to {doc.recipient}: {doc.message}")
    # Uncomment when ready to send actual SMS:
    # send_sms([doc.recipient], doc.message, success_msg=False)

def send_email_notification(doc):
    # Simulate sending Email here
    frappe.msgprint(f"Sending Email to {doc.recipient}: {doc.message}")
    # Implement actual email sending logic here
