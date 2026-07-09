import frappe
from frappe import _
from frappe.utils import flt


def _get_excel_psi(item_code):
	name = frappe.db.get_value("Excel PSI", {"item_code": item_code}, "name")
	return frappe.get_doc("Excel PSI", name) if name else None


def _items_by_code(items):
	codes = set()
	for item in items or []:
		if item.item_code:
			codes.add(item.item_code)
	return codes


def _pipeline_qty_for_item(item_code):
	"""Sum of qty for this item across every *draft* Excel LC Pipeline. Only drafts
	count — once a pipeline is submitted, its qty has been closed out into
	Backlog/Under Production (see on_submit) and should drop out of Pipeline
	entirely. Recomputed from scratch each time so it can't drift, the same
	reasoning as Excel PSI's proposed/under-production sync."""
	rows = frappe.db.sql(
		"""
		SELECT SUM(lci.qty) AS total
		FROM `tabExcel LC Pipeline Item` lci
		INNER JOIN `tabExcel LC Pipeline` lc ON lc.name = lci.parent
		WHERE lci.item_code = %(item_code)s
		  AND lc.docstatus = 0
		""",
		{"item_code": item_code},
		as_dict=True,
	)
	return flt(rows[0].total) if rows and rows[0].total else 0.0


def _sync_psi_pipeline(item_code):
	psi = _get_excel_psi(item_code)
	if not psi:
		return

	correct_pipeline = _pipeline_qty_for_item(item_code)
	if flt(psi.pipeline) == correct_pipeline:
		return

	psi.pipeline = correct_pipeline
	psi.flags.ignore_permissions = True
	psi.save()


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


def on_update(doc, method=None):
	"""Mirror this LC Pipeline's item quantities into Excel PSI's Pipeline field on
	every save — draft or submitted — so the qty shows up immediately rather than
	only once submitted. Frappe also runs on_update as part of submit (before
	on_submit), so this covers that transition too."""
	doc_before = doc.get_doc_before_save()
	old_codes = _items_by_code(doc_before.custom_items) if doc_before else set()
	new_codes = _items_by_code(doc.custom_items)

	for item_code in old_codes | new_codes:
		_sync_psi_pipeline(item_code)


def on_submit(doc, method=None):
	"""Close out Under Production: whatever this submission's qty didn't cover of
	the current Under Production carries forward into Backlog, then Under
	Production resets to 0. Pipeline itself is already up to date via on_update
	(which also runs during submit), so it isn't touched here."""
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
		psi.backlog = max(0.0, flt(psi.backlog) + under_production - flt(item.qty))
		psi.under_production = 0.0
		psi.flags.ignore_permissions = True
		psi.save()


def on_cancel(doc, method=None):
	"""Recompute Pipeline (the cancelled document naturally drops out of the sum).
	Best-effort restore of Under Production by adding the qty back — Backlog isn't
	perfectly restored if the original submit also drew from it, since on_submit
	doesn't keep a record of the pre-submit split between Under Production and
	Backlog."""
	for item in doc.custom_items:
		if not item.item_code:
			continue
		_sync_psi_pipeline(item.item_code)

		if not item.qty:
			continue
		psi = _get_excel_psi(item.item_code)
		if not psi:
			continue
		psi.under_production = flt(psi.under_production) + flt(item.qty)
		psi.flags.ignore_permissions = True
		psi.save()


def on_trash(doc, method=None):
	"""A draft LC Pipeline can be deleted outright (no on_cancel fires for that) —
	recompute Pipeline so its qty drops out of the sum."""
	for item_code in _items_by_code(doc.custom_items):
		_sync_psi_pipeline(item_code)
