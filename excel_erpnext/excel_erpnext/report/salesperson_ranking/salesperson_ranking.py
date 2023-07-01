# Copyright (c) 2013, Castlecraft Ecommerce Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import requests
import json
from frappe.utils import flt, cint

def execute(filters=None):
	api_key = frappe.get_conf().get("encryption_key")
	
	columns = get_columns(filters)
	data = get_result(filters)
	
	return columns, data

def get_columns(filters):

	columns = [
		{"label": ("Sale Person"), "fieldname": "sales_person", "fieldtype": "data","width": 150},
		{"label": ("Net Sales"), "fieldname": "net_sales", "fieldtype": "Currency","options": "currency","width": 100},
		{"label": ("Paid Amount"), "fieldname": "paid_amount", "fieldtype": "Currency","options": "currency","width": 150},
		{"label": ("Outstanding Amount"), "fieldname": "outstanding_amount", "fieldtype": "Currency","options": "currency","width": 180},
		{"label": ("Sales Collection Ratio"), "fieldname": "sales_collection_ratio", "fieldtype": "Float","width": 150},
		{"label": ("Outstanding Collection Ratio"), "fieldname": "outstanding_collection_ratio", "fieldtype": "Float","width": 150},
		
	]

	return columns

def get_result(filters):
	
	gl_entrie = frappe.db.sql("""
					select
							sp.sales_person, sum(ge.debit) as debit, sum(ge.credit) as credit
					from
							`tabGL Entry` ge
							left join `tabCustomer` cp on cp.name = ge.party left join `tabSales Team` sp on sp.parent = cp.name 
					where
							ge.docstatus < 2
							and ge.party_type="Customer"
							group by sp.sales_person order by sp.sales_person"""
					,as_dict = 1)
	outstandingArr = {}
	for j in gl_entrie:
		debit = j['debit']
		credit = j['credit']
		outstanding = debit - credit
		outstandingArr[j['sales_person']] = outstanding
	
	collection_data = frappe.db.sql(""" SELECT
							sum(pe.paid_amount) as paid_amount, sp.sales_person
							FROM `tabPayment Entry` pe
							left join `tabCustomer` cp on cp.name = pe.party left join `tabSales Team` sp on sp.parent = cp.name 
							where pe.docstatus = 1 and pe.posting_date >= %s and pe.posting_date <= %s and pe.excel_tax_payment = "No" and pe.party_type = "Customer" group by sp.sales_person
							""",(filters.get('from_date'),filters.get('to_date')), as_dict = 1)
	collectionArr = {}
	for k in collection_data:
		collection_amount = k['paid_amount']
		collectionArr[k['sales_person']] = collection_amount

	conditions = ""
	
	conditions += "si.docstatus = 1"
	if filters.get("from_date"): conditions += " and si.posting_date >= '%s'" % filters.get("from_date")
	if filters.get("to_date"): conditions += " and si.posting_date <= '%s' " % filters.get("to_date")
	if filters.get("territory"): conditions += " and cp.territory = '%s' " %filters.get("territory")
	if filters.get("brand"): conditions += " and sii.brand = '%s' " %filters.get("brand")
	
	response = frappe.db.sql("""
			SELECT 
				sum(sii.net_amount) as net_sales, 
				sp.sales_person as sales_person 
			FROM `tabSales Invoice Item` sii left join `tabSales Invoice` si on si.name = sii.parent left join `tabCustomer` cp on cp.name = si.customer left join `tabSales Team` sp on sp.parent = cp.name 
			where
				{conditions}
			group by sp.sales_person order by sum(sii.net_amount) desc""".format(conditions=conditions),as_dict=1)

	
	data = []
	for record in response:
		net_sales = record.net_sales
		sales_person = record.sales_person
		
		if sales_person in outstandingArr:
			outstanding = outstandingArr[sales_person]
		else:
			outstanding = 0
		if sales_person in collectionArr:
			collection = collectionArr[sales_person]
		else:
			collection = 0
		row = {
			"sales_person": sales_person,
			"net_sales": net_sales,
			"paid_amount": collection,
			"outstanding_amount": outstanding,
			"sales_collection_ratio": (collection/net_sales) * 100 if net_sales > 0 else 0,
			"outstanding_collection_ratio": (collection/outstanding) * 100 if outstanding > 0 else 0
		}
		data.append(row)
	return data
	