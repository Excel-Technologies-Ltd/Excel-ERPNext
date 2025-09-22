# telegram_notification.py
import frappe
import requests
import json
from frappe.utils import get_url

def send_telegram_message(chat_id, bot_token, message, parse_mode="HTML"):
    """
    Send message to Telegram group/chat
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': parse_mode
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        frappe.log_error(f"Failed to send Telegram message: {str(e)}", "Telegram Notification Error")
        return False

def format_error_message(error_log):
    """
    Format error log details for Telegram message
    """
    site_name = frappe.local.site or "Unknown Site"
    base_url = get_url()
    error_link = f"{base_url}/app/error-log/{error_log.name}"
    
    message = f"""
🚨 <b>BazraBD Error Alert</b> 🚨

<b>Site:</b> {site_name}
<b>Error:</b> {error_log.error[:100]}{'...' if len(error_log.error) > 100 else ''}
<b>Method:</b> {error_log.method or 'N/A'}
<b>Time:</b> {error_log.creation}

<b>View Full Error:</b> <a href="{error_link}">Click Here</a>

#ERPNextError #Support
    """
    return message.strip()

@frappe.whitelist()
def site_not_reachable_alert():
    settings = frappe.get_doc("ArcApps Alert Settings")
    site_url = get_url()
    site_name = settings.site_name
    
    if not site_name or not bool(settings.enable):
        return {"success": False, "message": "No sites configured"}
    
    site_list = [site.strip() for site in site_name.split(",")]
    unreachable_sites = []
    
    # Check each site
    for site in site_list:
        try:
            response = requests.get(f"{site}", timeout=10)  # Add timeout
            if response.status_code != 200:
                unreachable_sites.append(site)
        except requests.exceptions.RequestException:
            # Handle connection errors, timeouts, etc.
            unreachable_sites.append(site)
    
    # Send alert only if there are unreachable sites
    if unreachable_sites:
        time = frappe.utils.now()
        unreachable_count = len(unreachable_sites)
        total_sites = len(site_list)
        
        # Create message based on number of unreachable sites
        if unreachable_count == 1:
            alert_message = f"🚨<b>Site Not Reachable Alert</b> 🚨\n<b>Unreachable Site:</b> {unreachable_sites[0]}\n<b>Time:</b> {time}"
        else:
            sites_text = "\n".join([f"• {site}" for site in unreachable_sites])
            alert_message = f"""🚨<b>Multiple Sites Not Reachable Alert</b> 🚨
<b>Unreachable Sites ({unreachable_count} of {total_sites}):</b>
{sites_text}
<b>Time:</b> {time}"""
        
        # Send telegram message
        send_telegram_message(
            chat_id=settings.chat_id,
            bot_token=settings.bot_token,
            message=alert_message,
            parse_mode="HTML",
        )
        
        return {
            "success": True, 
            "message": f"{unreachable_count} site(s) not reachable",
            "unreachable_sites": unreachable_sites
        }
    else:
        return {
            "success": True, 
            "message": "All sites are reachable"
        }


@frappe.whitelist()
def notify_telegram_on_error(error_log_name):
    """
    Send error notification to Telegram when called
    """
    try:
        # Get Telegram settings from System Settings or create a custom doctype
        telegram_settings = get_telegram_settings()
        
        if not telegram_settings.get('enabled'):
            return "not allowed"
            
        error_log = frappe.get_doc('Error Log', error_log_name)
        
        # Format message
        message = format_error_message(error_log)
        
        # Send to Telegram
        success = send_telegram_message(
            chat_id=telegram_settings.get('chat_id'),
            bot_token=telegram_settings.get('bot_token'),
            message=message,
            parse_mode=telegram_settings.get('parse_mode', 'HTML')
        )
        
        if success:
            frappe.logger().info(f"Telegram notification sent for error: {error_log_name}")
        
    except Exception as e:
        frappe.log_error(f"Error in Telegram notification: {str(e)}", "Telegram Notification")

def get_telegram_settings():
    """
    Get Telegram configuration settings from Telegram Settings doctype
    """
    try:
        telegram_settings = frappe.get_doc("ArcApps Alert Settings")
        
        return {
            'enabled': bool(telegram_settings.enable),
            'bot_token': telegram_settings.bot_token,
            'chat_id': telegram_settings.chat_id,
            'site_name': telegram_settings.site_name,
            'parse_mode':  'HTML'
        }
    except Exception as e:
        frappe.log_error(f"Error getting Telegram settings: {str(e)}", "Telegram Settings Error")
        return {
            'enabled': False,
            'bot_token': '',
            'chat_id': '',
            'site_name': '',
            'parse_mode': 'HTML'
        }

# Hook function to be called when Error Log is created
def on_error_log_insert(doc, method):
    """
    Hook function to be called when a new Error Log is created
    Add this to hooks.py
    """
    # Run in background to avoid blocking the error logging process
    frappe.enqueue(
        notify_telegram_on_error,
        error_log_name=doc.name,
        queue='short'
    )
def site_not_reachable_alert_hook():
    """
    Hook function to be called when a new Error Log is created
    Add this to hooks.py
    """
    # Run in background to avoid blocking the error logging process
    frappe.enqueue(
        site_not_reachable_alert,
        queue='long'
    )


#