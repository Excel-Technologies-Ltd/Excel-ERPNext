# -*- coding: utf-8 -*-
# Copyright (c) 2026, Castlecraft Ecommerce Pvt. Ltd. and contributors
"""Material Request -> Excel LC Pipeline allocation.

Lets an LC Pipeline draw item quantities from specific Material Request rows,
tracks how much of each request row has been consumed (Material Request Item
``custom_pipeline_qty``), prevents over-allocation (including under concurrent
submits), and maintains the read-only consolidated ``custom_items_summary``.

This lives beside the existing Excel PSI sync in
``doc_events/excel_lc_pipeline/excel_lc_pipeline.py`` and never touches any
existing field or table.
"""

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt

# A Material Request row is allocatable only once the request is submitted and in
# one of these workflow states (per product decision).
ELIGIBLE_STATES = ("Approved", "Approved by Finance Officer")

# Tolerance for float comparisons on quantities.
_EPS = 1e-9


@frappe.whitelist()
def get_material_requests_for_item(item_code):
	"""Return eligible Material Request rows for ``item_code`` that still have a
	positive remaining quantity, using the latest persisted values.

	Remaining Qty = Request Qty (qty) - Pipeline Qty (custom_pipeline_qty).
	"""
	if not item_code:
		return []

	frappe.has_permission("Material Request", throw=True)

	rows = frappe.db.sql(
		"""
		SELECT
			mri.name AS material_request_item,
			mri.parent AS material_request,
			mri.item_code AS item_code,
			mri.item_name AS item_name,
			mri.qty AS request_qty,
			IFNULL(mri.custom_pipeline_qty, 0) AS pipeline_qty,
			(mri.qty - IFNULL(mri.custom_pipeline_qty, 0)) AS remaining_qty,
			mr.custom_workflow_state AS workflow_state,
			mr.transaction_date AS transaction_date
		FROM `tabMaterial Request Item` mri
		INNER JOIN `tabMaterial Request` mr ON mr.name = mri.parent
		WHERE mri.item_code = %(item_code)s
			AND mr.docstatus = 1
			AND mr.custom_workflow_state IN %(states)s
			AND (mri.qty - IFNULL(mri.custom_pipeline_qty, 0)) > %(eps)s
		ORDER BY mr.transaction_date ASC, mri.parent ASC
		""",
		{"item_code": item_code, "states": ELIGIBLE_STATES, "eps": _EPS},
		as_dict=True,
	)
	return rows


@frappe.whitelist()
def get_material_request_item_detail(material_request, item_code):
	"""Return the matching Material Request Item row for a manually selected
	``material_request`` + ``item_code``.

	Used when a user picks a Material Request directly in the Items grid (instead
	of via the Fetch dialog) so Request Qty / MR Item Ref back-fill and Remaining
	can compute. When the request carries more than one row for the same item, the
	one with positive remaining quantity is preferred (else the first row).

	Remaining Qty = Request Qty (qty) - Pipeline Qty (custom_pipeline_qty).
	"""
	if not material_request or not item_code:
		return {}

	frappe.has_permission("Material Request", throw=True)

	rows = frappe.db.sql(
		"""
		SELECT
			mri.name AS material_request_item,
			mri.parent AS material_request,
			mri.item_code AS item_code,
			mri.item_name AS item_name,
			mri.qty AS request_qty,
			IFNULL(mri.custom_pipeline_qty, 0) AS pipeline_qty,
			(mri.qty - IFNULL(mri.custom_pipeline_qty, 0)) AS remaining_qty
		FROM `tabMaterial Request Item` mri
		WHERE mri.parent = %(material_request)s
			AND mri.item_code = %(item_code)s
		ORDER BY (mri.qty - IFNULL(mri.custom_pipeline_qty, 0)) DESC, mri.idx ASC
		""",
		{"material_request": material_request, "item_code": item_code},
		as_dict=True,
	)
	return rows[0] if rows else {}


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def material_request_link_query(doctype, txt, searchfield, start, page_len, filters):
	"""Link-field query for the ``Material Request`` column in the Items grid.

	Restricts the dropdown to Material Requests that are:
	  - Submitted (``docstatus = 1``), and
	  - contain the currently selected ``item_code`` on at least one of their rows.

	``item_code`` is passed through ``filters`` from the grid row; when it is empty
	(no item chosen yet) the item restriction is skipped and only submitted requests
	are shown.
	"""
	filters = filters or {}
	item_code = filters.get("item_code")

	conditions = ["mr.docstatus = 1"]
	params = {
		"txt": "%%%s%%" % txt,
		"start": start,
		"page_len": page_len,
	}

	if item_code:
		# Only requests that still have available quantity for this item
		# (Quantity - Pipeline Qty > 0) -- mirrors the Fetch Material Requests dialog.
		conditions.append(
			"EXISTS (SELECT 1 FROM `tabMaterial Request Item` mri "
			"WHERE mri.parent = mr.name AND mri.item_code = %(item_code)s "
			"AND (mri.qty - IFNULL(mri.custom_pipeline_qty, 0)) > %(eps)s)"
		)
		params["item_code"] = item_code
		params["eps"] = _EPS

	where = " AND ".join(conditions)
	return frappe.db.sql(
		"""
		SELECT mr.name, mr.title
		FROM `tabMaterial Request` mr
		WHERE {where}
			AND (mr.name LIKE %(txt)s OR mr.title LIKE %(txt)s)
		ORDER BY mr.transaction_date DESC, mr.name DESC
		LIMIT %(start)s, %(page_len)s
		""".format(where=where),
		params,
	)


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def recompute_row_remaining(doc):
	"""Each Items row's Remaining Qty = Request Qty - allocated Quantity.

	Only applied to rows sourced from a Material Request (those carry a Request
	Quantity); manually-added rows have no Request Quantity and are left alone.
	"""
	for row in doc.get("custom_items") or []:
		if flt(row.get("custom_request_qty")):
			row.custom_remaining_qty = flt(row.custom_request_qty) - flt(row.qty)


def rebuild_items_summary(doc):
	"""Recompute ``custom_items_summary`` from ``custom_items``, one row per unique
	item code.

	- Proposed Quantity : sum of Request Quantity across the item's rows (falls
	                      back to the allocated qty for manual rows with no request).
	- LC Quantity       : sum of the allocated ``qty`` placed on this LC.
	- Remaining Quantity: Proposed - LC (= sum of each row's Request - Quantity).
	- Rate (USD)        : sum of the item's row ``rate`` (blank when the item has
	                      no rows -- i.e. no summary row is emitted at all).
	- Total Amount (USD): sum of the item's row Amount (qty * rate).
	"""
	groups = {}
	order = []
	for row in doc.get("custom_items") or []:
		if not row.item_code:
			continue
		if row.item_code not in groups:
			groups[row.item_code] = {"proposed": 0.0, "lc": 0.0, "rate_usd": 0.0, "amount": 0.0}
			order.append(row.item_code)
		# Request Quantity is the "proposed"; fall back to qty for manual rows.
		groups[row.item_code]["proposed"] += flt(row.get("custom_request_qty")) or flt(row.qty)
		groups[row.item_code]["lc"] += flt(row.qty)
		groups[row.item_code]["rate_usd"] += flt(row.rate)
		# Total Amount is the sum of each row's Amount (qty * rate).
		groups[row.item_code]["amount"] += flt(row.get("amount")) or (flt(row.qty) * flt(row.rate))

	doc.set("custom_items_summary", [])
	for item_code in order:
		g = groups[item_code]
		doc.append(
			"custom_items_summary",
			{
				"item": item_code,
				"proposed_quantity": g["proposed"],
				"lc_quantity": g["lc"],
				"remaining_quantity": g["proposed"] - g["lc"],
				"rate_usd": g["rate_usd"],
				"total_amount_usd": g["amount"],
			},
		)


# ---------------------------------------------------------------------------
# Allocation validation + persistence
# ---------------------------------------------------------------------------

def validate_allocation_rows(doc):
	"""Early (pre-submit) checks on allocation rows for fast, friendly feedback.

	The authoritative, race-safe check runs again under a row lock in
	``apply_allocation_deltas`` at submit time.
	"""
	for row in doc.get("custom_items") or []:
		mri_name = (row.get("custom_material_request_item") or "").strip()
		if not mri_name:
			continue

		if flt(row.qty) <= 0:
			frappe.throw(
				_("Row #{0}: Allocation Quantity must be greater than zero.").format(row.idx)
			)

		mri = frappe.db.get_value(
			"Material Request Item",
			mri_name,
			["name", "parent", "item_code", "qty", "custom_pipeline_qty"],
			as_dict=True,
		)
		if not mri:
			frappe.throw(
				_("Row #{0}: Material Request Item {1} does not exist.").format(
					row.idx, frappe.bold(mri_name)
				)
			)

		if mri.item_code != row.item_code:
			frappe.throw(
				_("Row #{0}: Item {1} does not match the referenced Material Request Item ({2}).").format(
					row.idx, frappe.bold(row.item_code), frappe.bold(mri.item_code)
				)
			)

		_assert_mr_eligible(doc, row, mri.parent)


def apply_allocation_deltas(doc, sign):
	"""Apply ``sign * qty`` to each referenced Material Request Item's
	``custom_pipeline_qty``.

	Runs inside the submit/cancel transaction. Each MR Item row is locked with
	``SELECT ... FOR UPDATE`` and its Pipeline Qty re-read under the lock, so two
	LC Pipelines submitting against the same request row cannot both consume the
	same remaining quantity -- the second blocks, then re-validates against the
	now-updated value and is rejected if it over-allocates. Any throw rolls the
	whole transaction back.

	sign = +1 on submit (allocate), -1 on cancel (release).
	"""
	for row in doc.get("custom_items") or []:
		mri_name = (row.get("custom_material_request_item") or "").strip()
		if not mri_name:
			continue

		alloc = flt(row.qty)
		if alloc <= 0:
			continue

		mri = frappe.db.get_value(
			"Material Request Item",
			mri_name,
			["name", "parent", "item_code", "qty", "custom_pipeline_qty"],
			as_dict=True,
			for_update=True,
		)
		if not mri:
			if sign > 0:
				frappe.throw(
					_("Row #{0}: Material Request Item {1} no longer exists.").format(
						row.idx, frappe.bold(mri_name)
					)
				)
			# Nothing to release if the row is gone.
			continue

		current = flt(mri.custom_pipeline_qty)

		if sign > 0:
			_assert_mr_eligible(doc, row, mri.parent)
			available = flt(mri.qty) - current
			if alloc > available + _EPS:
				frappe.throw(
					_(
						"Row #{0}: Allocation {1} for item {2} exceeds the available "
						"quantity ({3}) on Material Request {4}."
					).format(
						row.idx,
						alloc,
						frappe.bold(mri.item_code),
						available,
						frappe.bold(mri.parent),
					)
				)

		new_val = max(0.0, current + sign * alloc)
		frappe.db.set_value(
			"Material Request Item",
			mri_name,
			"custom_pipeline_qty",
			new_val,
			update_modified=False,
		)


def _assert_mr_eligible(doc, row, mr_name):
	state, docstatus = frappe.db.get_value(
		"Material Request", mr_name, ["custom_workflow_state", "docstatus"]
	) or (None, None)

	if docstatus != 1 or state not in ELIGIBLE_STATES:
		frappe.throw(
			_(
				"Row #{0}: Material Request {1} is not eligible for allocation "
				"(must be submitted and Approved)."
			).format(row.idx, frappe.bold(mr_name))
		)
