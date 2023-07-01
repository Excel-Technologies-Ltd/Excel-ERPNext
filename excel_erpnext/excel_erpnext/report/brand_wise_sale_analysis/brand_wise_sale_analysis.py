# Copyright (c) 2013, Castlecraft Ecommerce Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import requests
import json
from frappe.utils import flt, cint
from collections import defaultdict

def execute(filters=None):
	api_key = frappe.get_conf().get("encryption_key")
	
	#columns = get_columns(filters)
	columns,data = get_result(filters)
	
	return columns, data

def multi_dict(K, type):
    if K == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: multi_dict(K-1, type))

def get_result(filters):
	columns = [
		{"label": ("Territory"), "fieldname": "territory", "fieldtype": "data","width": 100},
		{"label": ("Customer Group"), "fieldname": "customer_group", "fieldtype": "data","width": 100},
		{"label": ("Customer"), "fieldname": "customer", "fieldtype": "data","width": 100},
		{"label": ("Customer Name"), "fieldname": "customer_name", "fieldtype": "data","width": 150},
		{"label": ("Sale Person"), "fieldname": "sales_person", "fieldtype": "data","width": 100},
	]
	conditions = ""
	
	conditions += "si.docstatus = 1"
	if filters.get("from_date"): conditions += " and si.posting_date >= '%s'" % filters.get("from_date")
	if filters.get("to_date"): conditions += " and si.posting_date <= '%s' " % filters.get("to_date")
	if filters.get("territory"): conditions += " and cp.territory = '%s' " %filters.get("territory")
	if filters.get("sales_person"): conditions += " and sp.sales_person = '%s' " %filters.get("sales_person")
	if filters.get("brand"): conditions += " and sii.brand = '%s' " %filters.get("brand")
	if filters.get("customer_group"): conditions += " and cp.customer_group = '%s' " %filters.get("customer_group")

	response = frappe.db.sql("""
			SELECT 
				si.customer, cp.customer_name, cp.territory, cp.customer_group, sp.sales_person, sii.brand,
				sum(sii.net_amount) as net_sales, 
				sp.sales_person as sales_person 
			FROM `tabSales Invoice Item` sii left join `tabSales Invoice` si on si.name = sii.parent left join `tabCustomer` cp on cp.name = si.customer left join `tabSales Team` sp on sp.parent = cp.name 
			where
				{conditions}
			group by cp.territory, cp.customer_group, si.customer, sp.sales_person, sii.brand order by cp.territory, cp.customer_group, si.customer, sp.sales_person, sii.brand""".format(conditions=conditions),as_dict=1)

	
	data = []
	bArr = []
	cArr = {}
	test_dict = multi_dict(5, str)
	
	for j in response:
		net_sales = j.net_sales
		test_dict[j['territory']][j['customer_group']][j['customer']][j['sales_person']][j['brand']] = net_sales
		cArr[j['customer']] = j['customer_name']
		if j['brand'] not in bArr and j['brand'] :
			bArr.append(j['brand'])
	bArr.sort()
	for i in bArr:
		columns += [{"label": (i), "fieldname": i, "fieldtype": "data","width": 100}]
	
	for r in test_dict:
		for cg in test_dict[r]:
			for cu in test_dict[r][cg]:
				for sp in test_dict[r][cg][cu]:
					row = {}
					row['territory'] = r
					row['customer_group'] = cg
					row['customer'] = cu
					row['customer_name'] = cArr[cu]
					row['sales_person'] = sp
					
					for brand in bArr:
						row[brand] = test_dict[r][cg][cu][sp][brand]
					data.append(row)
	return columns, data
	