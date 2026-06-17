import frappe
from frappe import _


def _get_excel_psi(item_code):
	name = frappe.db.get_value("Excel PSI", {"item_code": item_code}, "name")
	return frappe.get_doc("Excel PSI", name) if name else None


def _adjust_psi_pipeline(psi, delta):
	psi.pipeline = max(0.0, (psi.pipeline or 0.0) + delta)
	psi.flags.ignore_permissions = True
	psi.save()


def on_submit(doc, method=None):
	"""Decrease Excel PSI pipeline qty for each item when LC Pipeline is submitted."""
	for item in doc.custom_items:
		if not item.item_code or not item.qty:
			continue
		psi = _get_excel_psi(item.item_code)
		if not psi:
			frappe.msgprint(
				_("Excel PSI not found for item <b>{0}</b> — pipeline qty not updated.").format(
					item.item_code
				),
				indicator="orange",
				alert=True,
			)
			continue
		_adjust_psi_pipeline(psi, -item.qty)


def on_cancel(doc, method=None):
	"""Increase Excel PSI pipeline qty for each item when LC Pipeline is cancelled."""
	for item in doc.custom_items:
		if not item.item_code or not item.qty:
			continue
		psi = _get_excel_psi(item.item_code)
		if not psi:
			continue
		_adjust_psi_pipeline(psi, +item.qty)
