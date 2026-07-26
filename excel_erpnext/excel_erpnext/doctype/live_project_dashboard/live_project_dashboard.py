# Copyright (c) 2026, Castlecraft Ecommerce Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class LiveProjectDashboard(Document):
	pass


@frappe.whitelist()
def get_iou_totals(wo_number):
	if not wo_number:
		return {"approved_iou": 0, "pending_iou": 0, "iou_voucher": 0}

	advances = frappe.get_all(
		"Employee Advance",
		filters={"custom_work_order_no": wo_number},
		fields=["name", "workflow_state", "approved_amount", "employee_request_amount"],
	)

	approved_iou = 0
	pending_iou = 0

	for advance in advances:
		if advance.workflow_state == "Approved":
			approved_iou += flt(advance.approved_amount)
		elif advance.workflow_state == "Pending":
			pending_iou += flt(advance.approved_amount) or flt(advance.employee_request_amount)

	iou_voucher = 0
	advance_names = [advance.name for advance in advances]

	if advance_names:
		voucher_rows = frappe.get_all(
			"Journal Entry Account",
			filters={
				"docstatus": 1,
				"party_type": "Employee",
				"reference_type": "Employee Advance",
				"reference_name": ["in", advance_names],
			},
			fields=["debit_in_account_currency"],
		)
		iou_voucher = sum(flt(row.debit_in_account_currency) for row in voucher_rows)

	return {"approved_iou": approved_iou, "pending_iou": pending_iou, "iou_voucher": iou_voucher}
