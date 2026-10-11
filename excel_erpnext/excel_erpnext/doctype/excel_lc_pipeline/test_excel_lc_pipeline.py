# -*- coding: utf-8 -*-
# Copyright (c) 2021, Castlecraft Ecommerce Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt, nowdate

from excel_erpnext.api.lc_pipeline_allocation import (
	apply_allocation_deltas,
	get_material_requests_for_item,
	rebuild_items_summary,
	recompute_row_remaining,
	validate_allocation_rows,
)

TEST_ITEM = "_Test LC Alloc Item"


def _leaf_item_group():
	grp = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	if grp:
		return grp
	doc = frappe.get_doc(
		{"doctype": "Item Group", "item_group_name": "_Test LC Alloc Group", "parent_item_group": "All Item Groups"}
	).insert(ignore_permissions=True)
	return doc.name


def _ensure_item(code=TEST_ITEM):
	if not frappe.db.exists("Item", code):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": code,
				"item_group": _leaf_item_group(),
				"stock_uom": "Nos",
				"is_stock_item": 0,
			}
		).insert(ignore_permissions=True)
	return code


def _make_mr(item_code, qty, state="Approved", pipeline_qty=0.0, docstatus=1):
	"""Create a Material Request and force the DB state the allocation queries read.

	docstatus/custom_workflow_state are set directly (bypassing the workflow) so
	tests don't depend on workflow transition setup.
	"""
	mr = frappe.new_doc("Material Request")
	mr.material_request_type = "Purchase"
	mr.transaction_date = nowdate()
	mr.schedule_date = nowdate()
	mr.append("items", {"item_code": item_code, "qty": qty, "rate": 1, "schedule_date": nowdate()})
	mr.flags.ignore_permissions = True
	mr.flags.ignore_mandatory = True
	mr.insert(ignore_permissions=True)

	frappe.db.set_value(
		"Material Request",
		mr.name,
		{"docstatus": docstatus, "custom_workflow_state": state},
		update_modified=False,
	)
	frappe.db.set_value(
		"Material Request Item", mr.items[0].name, "custom_pipeline_qty", pipeline_qty, update_modified=False
	)
	return mr.name, mr.items[0].name


def _lc_doc(rows):
	doc = frappe.new_doc("Excel LC Pipeline")
	doc.pipeline_status = "In Progress"
	for r in rows:
		doc.append("custom_items", r)
	return doc


class TestExcelLCPipeline(FrappeTestCase):
	def test_fetch_only_available_eligible(self):
		item = _ensure_item()
		mr1, _ = _make_mr(item, 200, "Approved", 0)  # remaining 200 -> yes
		mr2, _ = _make_mr(item, 150, "Approved", 150)  # remaining 0 -> no
		mr3, _ = _make_mr(item, 300, "Pending", 0, docstatus=0)  # not submitted -> no
		mr4, _ = _make_mr(item, 100, "Approved", 120)  # remaining -20 -> no

		names = {r["material_request"] for r in get_material_requests_for_item(item)}
		self.assertIn(mr1, names)
		self.assertNotIn(mr2, names)
		self.assertNotIn(mr3, names)
		self.assertNotIn(mr4, names)

	def test_allocation_increments_and_release(self):
		item = _ensure_item()
		mr, mri = _make_mr(item, 200, "Approved", 0)
		doc = _lc_doc([
			{"item_code": item, "qty": 100, "custom_material_request": mr, "custom_material_request_item": mri, "custom_request_qty": 200}
		])

		apply_allocation_deltas(doc, sign=1)
		self.assertEqual(flt(frappe.db.get_value("Material Request Item", mri, "custom_pipeline_qty")), 100)

		apply_allocation_deltas(doc, sign=-1)
		self.assertEqual(flt(frappe.db.get_value("Material Request Item", mri, "custom_pipeline_qty")), 0)

	def test_over_allocation_rejected(self):
		item = _ensure_item()
		mr, mri = _make_mr(item, 100, "Approved", 80)  # remaining 20
		doc = _lc_doc([
			{"item_code": item, "qty": 50, "custom_material_request": mr, "custom_material_request_item": mri, "custom_request_qty": 100}
		])
		with self.assertRaises(frappe.ValidationError):
			apply_allocation_deltas(doc, sign=1)
		self.assertEqual(flt(frappe.db.get_value("Material Request Item", mri, "custom_pipeline_qty")), 80)

	def test_competing_allocation_uses_latest_persisted(self):
		item = _ensure_item()
		mr, mri = _make_mr(item, 200, "Approved", 0)

		first = _lc_doc([
			{"item_code": item, "qty": 100, "custom_material_request": mr, "custom_material_request_item": mri, "custom_request_qty": 200}
		])
		apply_allocation_deltas(first, sign=1)  # persists pipeline_qty = 100

		second = _lc_doc([
			{"item_code": item, "qty": 150, "custom_material_request": mr, "custom_material_request_item": mri, "custom_request_qty": 200}
		])
		with self.assertRaises(frappe.ValidationError):  # only 100 remains
			apply_allocation_deltas(second, sign=1)
		self.assertEqual(flt(frappe.db.get_value("Material Request Item", mri, "custom_pipeline_qty")), 100)

	def test_item_code_mismatch_rejected(self):
		item = _ensure_item()
		other = _ensure_item("_Test LC Alloc Item 2")
		mr, mri = _make_mr(item, 100, "Approved", 0)
		doc = _lc_doc([
			{"item_code": other, "qty": 10, "custom_material_request": mr, "custom_material_request_item": mri, "custom_request_qty": 100}
		])
		with self.assertRaises(frappe.ValidationError):
			validate_allocation_rows(doc)

	def test_summary_groups_by_item(self):
		item = _ensure_item()
		doc = _lc_doc([
			{"item_code": item, "custom_request_qty": 120, "qty": 100, "rate": 2},
			{"item_code": item, "custom_request_qty": 60, "qty": 50, "rate": 3},
			{"item_code": item, "custom_request_qty": 30, "qty": 25, "rate": 1},
		])
		rebuild_items_summary(doc)
		self.assertEqual(len(doc.custom_items_summary), 1)
		summary = doc.custom_items_summary[0]
		self.assertEqual(summary.item, item)
		self.assertEqual(flt(summary.proposed_quantity), 210)  # 120 + 60 + 30 (Request Qty)
		self.assertEqual(flt(summary.lc_quantity), 175)  # 100 + 50 + 25 (allocated)
		self.assertEqual(flt(summary.remaining_quantity), 35)  # 210 - 175
		self.assertEqual(flt(summary.rate_usd), 6)  # 2 + 3 + 1

	def test_row_remaining_is_request_minus_qty(self):
		item = _ensure_item()
		doc = _lc_doc([
			{"item_code": item, "custom_request_qty": 200, "qty": 80},  # MR-sourced
			{"item_code": item, "qty": 10},  # manual row, no request qty
		])
		recompute_row_remaining(doc)
		self.assertEqual(flt(doc.custom_items[0].custom_remaining_qty), 120)  # 200 - 80
		# manual row (no request qty) is left untouched
		self.assertEqual(flt(doc.custom_items[1].custom_remaining_qty), 0)
