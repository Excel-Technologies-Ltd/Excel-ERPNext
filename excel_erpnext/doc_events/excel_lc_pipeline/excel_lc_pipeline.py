import frappe
from frappe import _
from frappe.utils import flt


def _get_excel_psi(item_code):
	name = frappe.db.get_value("Excel PSI", {"item_code": item_code}, "name")
	return frappe.get_doc("Excel PSI", name) if name else None


def validate(doc, method=None):
	"""Each item's qty can't exceed what's actually available to place into an LC —
	Excel PSI's Under Production + Backlog for that item."""
	for item in doc.custom_items:
		if not item.item_code or not item.qty:
			continue

		psi = _get_excel_psi(item.item_code)
		available = (flt(psi.under_production) + flt(psi.backlog)) if psi else 0.0

		if flt(item.qty) > available:
			frappe.throw(
				_(
					"Row #{0}: Quantity ({1}) for item {2} exceeds the available Under "
					"Production + Backlog qty ({3}) in Excel PSI."
				).format(item.idx, flt(item.qty), frappe.bold(item.item_code), available)
			)


def on_submit(doc, method=None):
	"""Submitting an LC Pipeline is what puts its qty into Excel PSI's Pipeline now
	(drafts no longer touch Pipeline at all). Also closes out Under Production:
	whatever this submission's qty didn't cover of the current Under Production
	carries forward into Backlog, then Under Production resets to 0."""
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

		under_production = flt(psi.under_production)
		psi.pipeline = flt(psi.pipeline) + flt(item.qty)
		psi.backlog = max(0.0, flt(psi.backlog) + under_production - flt(item.qty))
		psi.under_production = 0.0
		psi.flags.ignore_permissions = True
		psi.save()


def on_update_after_submit(doc, method=None):
	"""Fires when a submitted LC Pipeline is saved again (e.g. flipping Pipeline
	Status from In Progress to Complete — allow_on_submit lets that field be edited
	post-submit). Once it's Complete, the qty is done moving through the pipeline,
	so pull it back out of Excel PSI's Pipeline."""
	doc_before = doc.get_doc_before_save()
	if not doc_before:
		return
	if doc_before.pipeline_status == "Complete" or doc.pipeline_status != "Complete":
		return

	for item in doc.custom_items:
		if not item.item_code or not item.qty:
			continue

		psi = _get_excel_psi(item.item_code)
		if not psi:
			continue

		psi.pipeline = max(0.0, flt(psi.pipeline) - flt(item.qty))
		psi.flags.ignore_permissions = True
		psi.save()


def on_cancel(doc, method=None):
	"""A cancelled LC Pipeline's qty never ships: it goes back into Backlog and is
	tracked separately in Cancelled Qty. Pipeline is only pulled back down if it
	still held this qty — i.e. the doc hadn't already gone to Complete, which would
	have deducted it already (see on_update_after_submit)."""
	for item in doc.custom_items:
		if not item.item_code or not item.qty:
			continue

		psi = _get_excel_psi(item.item_code)
		if not psi:
			continue

		if doc.pipeline_status != "Complete":
			psi.pipeline = max(0.0, flt(psi.pipeline) - flt(item.qty))
		psi.backlog = flt(psi.backlog) + flt(item.qty)
		psi.cancelled_lc_pipeline_qty = flt(psi.cancelled_lc_pipeline_qty) + flt(item.qty)
		psi.flags.ignore_permissions = True
		psi.save()
