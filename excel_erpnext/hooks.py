# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "excel_erpnext"
app_title = "Excel ERPNext"
app_publisher = "Castlecraft Ecommerce Pvt. Ltd."
app_description = "Extensions for Excel Technologies"
app_icon = "fa fa-cloud"
app_color = "grey"
app_email = "support@castlecraft.in"
app_license = "AGPLv3"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/excel_erpnext/css/excel_erpnext.css"
app_include_js = "/assets/excel_erpnext/js/excel_erpnext.js"

# include js, css files in header of web template
# web_include_css = "/assets/excel_erpnext/css/excel_erpnext.css"
# web_include_js = "/assets/excel_erpnext/js/excel_erpnext.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Excel Project Pre Costing" : "public/js/excel_project_pre_costing.js", 
    "ArcApps Project Pre Costing" : "public/js/excel_project_pre_costing.js",     
    "Excel LC Details" : "public/js/excel_lc_details.js", 
    "Excel LC Costing" : "public/js/excel_lc_costing.js", 
    "Excel LC No" : "public/js/excel_lc_no.js",
    "Excel MPS Counter" : "public/js/excel_mps_counter.js",
    "Excel LC Pipeline" : "public/js/excel_lc_pipeline.js"
    }
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "excel_erpnext.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "excel_erpnext.install.before_install"
# after_install = "excel_erpnext.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "excel_erpnext.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Customer": {
		"after_insert": "excel_erpnext.doc_events.customer.customer.send_notification",
		
		# "on_cancel": "method",
		# "on_trash": "method"
	},
 "Sales Invoice": {
		"on_submit": "excel_erpnext.doc_events.sales_invoice.sales_invoice.send_notification",
		"on_cancel": "excel_erpnext.doc_events.sales_invoice.sales_invoice.send_notification",
		# "on_cancel": "method",
		# "on_trash": "method"
	},
	"Payment Entry": {
		"on_submit": "excel_erpnext.doc_events.payment_entry.payment_entry.send_notification",
		"on_cancel": "excel_erpnext.doc_events.payment_entry.payment_entry.send_notification",
		# "on_cancel": "method",
		# "on_trash": "method"
	},
	"Journal Entry": {
		"on_submit": "excel_erpnext.doc_events.journal_entry.journal_entry.send_notification",
		"on_cancel": "excel_erpnext.doc_events.journal_entry.journal_entry.send_notification",
		# "on_cancel": "method",
		# "on_trash": "method"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "hourly_long": ["excel_erpnext.schedules.purchase.process_purchase_orders"]
}

# scheduler_events = {
# 	"all": [
# 		"excel_erpnext.tasks.all"
# 	],
# 	"daily": [
# 		"excel_erpnext.tasks.daily"
# 	],
# 	"hourly": [
# 		"excel_erpnext.tasks.hourly"
# 	],
# 	"weekly": [
# 		"excel_erpnext.tasks.weekly"
# 	]
# 	"monthly": [
# 		"excel_erpnext.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "excel_erpnext.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "excel_erpnext.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "excel_erpnext.task.get_dashboard_data"
# }

# fixtures = [
# 	{
#         "dt": "Price List",
#         "filters": [
#             [
#                 "name",
#                 "in",
#                 [
#                   "Bottom Price"  
#                 ],
#             ],
#         ]
#     },
# ]
# fixtures = [
# 	{
#         "dt": "Custom Field",
#         "filters": [
#             [
#                 "name",
#                 "in",
#                 [
#                     "Delivery Note Item-excel_serials",
#                     "Customer-excel_customer_bin_id",
#                     "Customer-excel_customer_trade_license",
#                     "Customer-excel_customer_nid",
#                     "Customer-excel_security_cheque_amount",
#                     "Customer-excel_customer_tin_id",
#                     "Customer-excel_customer_owner_name",
#                     "Customer-excel_customer_owner_farther_name",
#                     "Customer-excel_customer_owner_permanent_address",
#                     "Item-has_excel_serials",
#                     "Stock Entry Detail-excel_serials",
#                     "Payment Entry-excel_tax_payment",
#                     "Payment Entry-excel_territory",
#                     "Journal Entry-excel_territory",
#                     "Journal Entry Account-excel_party_name",
#                     "Stock Entry-excel_territory",
#                     "Bin-excel_item_name",
#                     "Bin-excel_item_brand",
#                     "Bin-excel_item_group",
#                     "Purchase Order-excel_actual_supplier",
#                     "Purchase Order-excel_actual_supplier_name",
#                     "Purchase Order-excel_lc_no",
#                     "Purchase Order-excel_lc_date",
#                     "Purchase Order-excel_pi_no",
#                     "Purchase Order-excel_pi_date",
#                     "Purchase Order-excel_excel_supplier_invoice_date", 
#                     "Purchase Order-excel_remarks", 
#                     "Purchase Order-excel_supplier_invoice_no",
#                     "Purchase Invoice-excel_actual_supplier",
#                     "Purchase Invoice-excel_actual_supplier_name",
#                     "Purchase Invoice-excel_supplier_invoice_no",
#                     "Purchase Invoice-excel_excel_supplier_invoice_date",
#                     "Purchase Invoice-excel_remarks",                     
#                     "Purchase Invoice-excel_lc_no",
#                     "Purchase Invoice-excel_lc_date",
#                     "Purchase Invoice-excel_pi_no",
#                     "Purchase Invoice-excel_pi_date",
#                     "Asset-excel_customer_name", 
#                     "Asset-excel_asset_user",  
#                     "Asset-project",
#                     "Journal Entry-project",  
#                     "Loan-project",  
#                     "Employee Advance-project",                                          
#                     "Asset-excel_device_model",  
#                     "Asset-excel_device_serial", 
#                     "Asset-excel_remarks", 
#                     "Project-mps_assets",
#                     "Project-excel_mps_project_assets", 
#                     "Sales Invoice-excel_customer_name_for_mps_print",
#                     "Stock Entry-excel_customer_name",
#                     "Stock Entry-excel_customer_address",
#                     "Stock Entry-excel_customer_contact",
#                     "Stock Entry-excel_customer_mobile",
#                     "Issue-excel_project",
#                     "Issue-excel_customer_contact_name",
#                     "Issue-excel_customer_contact_number",
#                     "Issue-excel_team_name",
#                     "Issue-excel_service_address",
#                     "Issue-excel_customer_name",
#                     "Task-excel_date",
#                     "Task-excel_time",
#                     "Task-excel_customer_contact_name",
#                     "Task-excel_customer_contact_number",
#                     "Task-excel_service_address",
#                     "Task-excel_assigned_user",
#                     "Task-excel_user_name",
#                     "Task-excel_customer_name",
#                     "Task-excel_remarks",
#                     "Task-excel_assigned_user_2",
#                     "Task-excel_assigned_user_name_2",
#                     "Task-excel_tasks_status",
#                     "Task-excel_project",
#                     "Task-excel_team_name",
#                     "Sales Invoice-mrp_sales_grand_total",
#                     "Sales Invoice Item-mrp_sales_rate",
#                     "Sales Invoice Item-mrp_sales_amount",
#                     "Sales Invoice Item-excel_serials",
#                     "Sales Invoice-excel_invoice_type",
#                     "Employee Advance-excel_employee_email",
#                     "Employee Advance-excel_iou_adjustment_date",
#                     "Employee Advance-excel_supervisor",
#                     "Employee Advance-excel_supervisor_name",
#                     "Customer-excel_fixed_credit_limit",
#                     "Customer-excel_total_conditional_limit",
#                     "Customer-excel_customer_credit_history",
#                     "Customer-excel_conditional_limit_expiry",
#                     "Employee Advance-territory",
#                     "Employee Advance-iou_type",
#                     "Employee Advance-excel_iou_project",
#                     "Employee Advance-customer",
#                     "Employee Advance-excel_iou_project_limit",
#                     "Employee Advance-approver_remarks",
#                     "Employee Advance-updated_reached_credit_limit",
#                     "Employee Advance-reached_credit_limit",
#                     "Employee Advance-employee_request_amount",
#                     "Employee Advance-approved_amount",
#                     "Customer-excel_remaining_balance",
#                 ],
#             ],
#         ]
#     },
# ]
fixtures = [  'Custom Field',  'Property Setter','Print Format']


