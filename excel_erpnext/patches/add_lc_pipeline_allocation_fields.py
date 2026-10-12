# -*- coding: utf-8 -*-
# Copyright (c) 2026, Castlecraft Ecommerce Pvt. Ltd. and contributors
"""Create the custom fields that back Material Request -> LC Pipeline allocation.

Migration-safe: create_custom_fields is idempotent (updates in place if the field
already exists), so re-running this patch is harmless. No data backfill is needed:
existing submitted LC Pipelines carry no Material Request references, so every
Material Request Item's Pipeline Qty correctly starts at 0.
"""

from __future__ import unicode_literals

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(get_custom_fields(), ignore_validate=True)


def get_custom_fields():
	return {
		"Material Request Item": [
			{
				"fieldname": "custom_pipeline_qty",
				"label": "Pipeline Qty",
				"fieldtype": "Float",
				"insert_after": "custom_pipeline",
				"default": "0",
				"read_only": 1,
				"no_copy": 1,
				"description": (
					"Cumulative quantity allocated to submitted Excel LC Pipelines "
					"from this specific Material Request row."
				),
			}
		],
		"Excel LC Pipeline Item": [
			{
				"fieldname": "custom_material_request",
				"label": "Material Request",
				"fieldtype": "Link",
				"options": "Material Request",
				"insert_after": "item_name",
				"in_list_view": 1,
				"columns": 2,
			},
			{
				"fieldname": "custom_material_request_item",
				"label": "MR Item Ref",
				"fieldtype": "Data",
				"insert_after": "custom_material_request",
				"read_only": 1,
				"description": (
					"Name of the source Material Request Item row. Links this "
					"allocation to a single request line so quantities are tracked "
					"per row, not per item code."
				),
			},
			{
				"fieldname": "custom_request_qty",
				"label": "PO Qty",
				"fieldtype": "Float",
				"insert_after": "qty",
				"read_only": 1,
				"in_list_view": 1,
				"columns": 1,
				"description": (
					"Quantity still available on the source Material Request row "
					"(Material Request Item Quantity - Pipeline Qty)."
				),
			},
			{
				"fieldname": "custom_remaining_qty",
				"label": "Remaining Qty",
				"fieldtype": "Float",
				"insert_after": "custom_request_qty",
				"read_only": 1,
				"in_list_view": 1,
				"columns": 1,
			},
		],
		"Excel LC Pipeline": [
			{
				"fieldname": "custom_items_summary_section",
				"label": "Items Summary",
				"fieldtype": "Section Break",
				"insert_after": "custom_total_amount_usd",
			},
			{
				"fieldname": "custom_items_summary",
				"label": "Items Summary",
				"fieldtype": "Table",
				"options": "Excel LC Pipeline Item Summary",
				"insert_after": "custom_items_summary_section",
				"read_only": 1,
				"description": "Auto-generated, grouped one row per unique item.",
			},
		],
	}
