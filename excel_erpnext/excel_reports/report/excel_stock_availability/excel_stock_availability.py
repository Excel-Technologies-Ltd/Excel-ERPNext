# Copyright (c) 2024, Castlecraft Ecommerce Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe import _

def execute(filters=None):
	data=get_data(filters)
	columns=get_columns()
	
	return columns, data
def get_columns():
    columns = [
        {
            'fieldname': 'item_code',
            'label': ('Item Code'),
            'fieldtype': 'Link',
            'options': 'Item',
            'width':150
        },
        {
            'fieldname': 'excel_item_name',
            'label': ('Item Name'),
            'fieldtype': 'Data',
             'width':250
            
        },
         {
            'fieldname': 'excel_item_group',
            'label': ('Item Group'),
            'fieldtype': 'Link',
            'options': 'Item Group'
        },
        {
            'fieldname': 'excel_item_brand',
            'label': ('Item Brand'),
            'fieldtype': 'Link',
            'options': 'Brand'
        },
     	{
            'fieldname': 'warehouse',
            'label': ('Warehouse'),
            'fieldtype': 'Link',
            'options': 'Warehouse'
        },
      {
            'fieldname': 'stock_uom',
            'label': ('Stock UOM'),
            'fieldtype': 'Link',
            'options': 'UOM'
        },
      	{
          'fieldname': 'actual_qty',
        	'label': ('Balance Qty'),
           'fieldtype': 'Float'
           
        },
      	{
            'fieldname': 'valuation_rate',
        	'label': ('Valuation Rate'),
           'fieldtype': 'Float'
        },
      	{
			'fieldname': 'stock_value',
        	'label': ('Balance Value'),
           'fieldtype': 'Float'
        },
       	
        
    ]
    return columns


def get_conditions(filter):
    conditions={
		
	}
    if filter.get("item_code"):
        conditions.update({"item_code":filter.get("item_code")})
    if filter.get("excel_item_name"):
        conditions.update({"excel_item_name":filter.get("excel_item_name")})
    if filter.get("excel_item_brand"):
        conditions.update({"excel_item_brand":filter.get("excel_item_brand")})
    if filter.get("excel_item_group"):
        conditions.update({"excel_item_group":filter.get("excel_item_group")})
    if filter.get("warehouse"):
        conditions.update({"warehouse":filter.get("warehouse")})
    return conditions  

def get_data(filter):
    conditions=get_conditions(filter)
    get_bin_list = frappe.get_list(
        "Bin",
        filters=conditions,
        fields=["item_code", "excel_item_name", "excel_item_brand", "excel_item_group","warehouse","actual_qty","valuation_rate","stock_value","stock_uom"],
    )
    return get_bin_list
