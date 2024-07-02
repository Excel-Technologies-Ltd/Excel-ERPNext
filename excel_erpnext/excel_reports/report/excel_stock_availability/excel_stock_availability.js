// Copyright (c) 2024, Castlecraft Ecommerce Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excel Stock Availability"] = {
	"filters": [
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
		  },
		  {
			fieldname: "excel_item_name",
			label: __("Item Name"),
			fieldtype: "Data",
			
		  },
		  {
			fieldname: "excel_item_brand",
			label: __("Item Brand"),
			fieldtype: "Link",
			options:"Brand"
			
		  },
		  {
			fieldname: "excel_item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options:"Item Group"
		  },
		  {
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options:"Warehouse"
		  }
	
	]
};
