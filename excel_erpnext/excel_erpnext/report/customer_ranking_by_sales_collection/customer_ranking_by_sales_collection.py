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
		{"label": ("Customer Code"), "fieldname": "customer", "fieldtype": "data","width": 100},
		{"label": ("Customer Name"), "fieldname": "customer_name", "fieldtype": "data","width": 150},
		{"label": ("Net Sales"), "fieldname": "net_sales", "fieldtype": "Currency","options": "currency","width": 100},
		{"label": ("Paid Amount"), "fieldname": "paid_amount", "fieldtype": "Currency","options": "currency","width": 150},
		{"label": ("Outstanding Amount"), "fieldname": "outstanding_amount", "fieldtype": "Currency","options": "currency","width": 180},
		{"label": ("Rebate"), "fieldname": "rebate_amount", "fieldtype": "Currency","options": "currency","width": 180},
		{"label": ("Sales Collection Ratio"), "fieldname": "sales_collection_ratio", "fieldtype": "Float","width": 150},
		{"label": ("Outstanding Collection Ratio"), "fieldname": "outstanding_collection_ratio", "fieldtype": "Float","width": 150},
		{"label": ("Sale Person"), "fieldname": "sales_person", "fieldtype": "data","width": 150},
	]

	return columns

def get_result(filters):
	
	conditions1 = ""
	conditions1 += "ge.docstatus < 2 and ge.party_type='Customer'"	
	if filters.get("territory"): conditions1 += " and cp.territory = '%s' " %filters.get("territory")
	if filters.get("sales_person"): conditions1 += " and sp.sales_person = '%s' " %filters.get("sales_person")
	if filters.get("customer_group"): conditions1 += " and cp.customer_group = '%s' " %filters.get("customer_group")
	if filters.get("customer"): conditions1 += " and cp.name = '%s' " %filters.get("customer")
	gl_entrie = frappe.db.sql("""
					select
							ge.party, cp.customer_name, sp.sales_person, sum(ge.debit) as debit, sum(ge.credit) as credit
					from
							`tabGL Entry` ge
							left join `tabCustomer` cp on cp.name = ge.party left join `tabSales Team` sp on sp.parent = cp.name 
					where
						{conditions}
							group by ge.party order by ge.party""".format(conditions=conditions1)
					,as_dict = 1)
	cArr = {}
	sArr = {}
	outstandingArr = {}
	for j in gl_entrie:
		debit = j['debit']
		credit = j['credit']
		outstanding = debit - credit
		outstandingArr[j['party']] = outstanding
		cArr[j['party']] = j['customer_name']
		sArr[j['party']] = j['sales_person']
	
	conditions2 = ""
	conditions2 += "pe.docstatus = 1 and pe.excel_tax_payment = 'No' and pe.party_type = 'Customer'"	
	if filters.get("from_date"): conditions2 += " and pe.posting_date >= '%s'" % filters.get("from_date")
	if filters.get("to_date"): conditions2 += " and pe.posting_date <= '%s' " % filters.get("to_date")
	if filters.get("territory"): conditions2 += " and cp.territory = '%s' " %filters.get("territory")
	if filters.get("sales_person"): conditions2 += " and sp.sales_person = '%s' " %filters.get("sales_person")
	if filters.get("customer_group"): conditions2 += " and cp.customer_group = '%s' " %filters.get("customer_group")
	if filters.get("customer"): conditions2 += " and cp.name = '%s' " %filters.get("customer")
	collection_data = frappe.db.sql(""" SELECT
							sum(pe.paid_amount) as paid_amount, sp.sales_person, pe.party, cp.customer_name
							FROM `tabPayment Entry` pe
							left join `tabCustomer` cp on cp.name = pe.party left join `tabSales Team` sp on sp.parent = cp.name 
							where 
								{conditions} 
									group by pe.party""".format(conditions=conditions2), as_dict = 1)
	collectionArr = {}
	for k in collection_data:
		collection_amount = k['paid_amount']
		collectionArr[k['party']] = collection_amount
		cArr[k['party']] = k['customer_name']
		sArr[k['party']] = k['sales_person']

	conditions3 = ""
	conditions3 += "pe.docstatus = 1 and pe.account like '%Accounts Receivable%' and pe.party_type = 'Customer'"	
	if filters.get("from_date"): conditions3 += " and je.posting_date >= '%s'" % filters.get("from_date")
	if filters.get("to_date"): conditions3 += " and je.posting_date <= '%s' " % filters.get("to_date")
	if filters.get("territory"): conditions3 += " and cp.territory = '%s' " %filters.get("territory")
	if filters.get("sales_person"): conditions3 += " and sp.sales_person = '%s' " %filters.get("sales_person")
	if filters.get("customer_group"): conditions3 += " and cp.customer_group = '%s' " %filters.get("customer_group")
	if filters.get("customer"): conditions3 += " and cp.name = '%s' " %filters.get("customer")
	rebate_data = frappe.db.sql(""" SELECT
							sum(pe.credit) as rebate, sp.sales_person, pe.party, cp.customer_name
							FROM `tabJournal Entry Account` pe 
							left join `tabJournal Entry` je on je.name = pe.parent 
							left join `tabCustomer` cp on cp.name = pe.party left join `tabSales Team` sp on sp.parent = cp.name 
							where 
								{conditions} 
									group by pe.party""".format(conditions=conditions3), as_dict = 1)
	rebateArr = {}
	for r in rebate_data:
		rebate_amount = r['rebate']
		rebateArr[r['party']] = rebate_amount
		cArr[r['party']] = r['customer_name']
		sArr[r['party']] = r['sales_person']

	conditions = ""
	
	conditions += "si.docstatus = 1"
	if filters.get("from_date"): conditions += " and si.posting_date >= '%s'" % filters.get("from_date")
	if filters.get("to_date"): conditions += " and si.posting_date <= '%s' " % filters.get("to_date")
	if filters.get("territory"): conditions += " and cp.territory = '%s' " %filters.get("territory")
	if filters.get("sales_person"): conditions += " and sp.sales_person = '%s' " %filters.get("sales_person")
	if filters.get("brand"): conditions += " and sii.brand = '%s' " %filters.get("brand")
	if filters.get("customer_group"): conditions += " and cp.customer_group = '%s' " %filters.get("customer_group")
	if filters.get("customer"): conditions += " and cp.name = '%s' " %filters.get("customer")

	sales_data = frappe.db.sql("""
			SELECT 
				si.customer, cp.customer_name,
				sum(sii.net_amount) as net_sales, 
				sp.sales_person as sales_person 
			FROM `tabSales Invoice Item` sii left join `tabSales Invoice` si on si.name = sii.parent left join `tabCustomer` cp on cp.name = si.customer left join `tabSales Team` sp on sp.parent = cp.name 
			where
				{conditions}
			group by si.customer order by sum(sii.net_amount) desc""".format(conditions=conditions),as_dict=1)

	
	salesArr = {}
	customerArr = {}
	for s in sales_data:
		sales_amount = s['net_sales']
		customer_name = s['customer_name']
		salesArr[s['customer']] = sales_amount
		customerArr[s['customer']] = customer_name
		sArr[j['party']] = s['sales_person']

	data = []
	
	for customer in customerArr:
		customer_name = customerArr[customer]
		net_sales = salesArr[customer]
		if customer in sArr:
			sales_person = sArr[customer]
		else:
			sales_person = ''
				
		if customer in outstandingArr:
			outstanding = outstandingArr[customer]
		else:
			outstanding = 0

		if customer in collectionArr:
			collection = collectionArr[customer]
		else:
			collection = 0
		
		if customer in rebateArr:
			rebate_amount = rebateArr[customer]
		else:
			rebate_amount = 0
		row = {
			"customer": customer,
			"customer_name": customer_name,
			"net_sales": net_sales,
			"paid_amount": collection,
			"outstanding_amount": outstanding,
			"rebate_amount": rebate_amount,
			"sales_collection_ratio": (collection/net_sales) * 100 if net_sales > 0 else 0,
			"outstanding_collection_ratio": (collection/outstanding) * 100 if outstanding > 0 else 0,
			"sales_person": sales_person,
		}
		data.append(row)
	if not filters.get("brand"):
		for c in cArr:
			if c not in customerArr:
				customer_name = cArr[c]
				if c in sArr:
					sales_person = sArr[c]
				else:
					sales_person = ''

				if c in collectionArr:
					collection = collectionArr[c]
				else:
					collection = 0

				if c in outstandingArr:
					outstanding = outstandingArr[c]
				else:
					outstanding = 0

				if c in rebateArr:
					rebate_amount = rebateArr[c]
				else:
					rebate_amount = 0
				row = {
					"customer": c,
					"customer_name": customer_name,
					"net_sales": 0,
					"paid_amount": collection,
					"outstanding_amount": outstanding,
					"rebate_amount": rebate_amount,
					"sales_collection_ratio": 0,
					"outstanding_collection_ratio": (collection/outstanding) * 100 if outstanding > 0 else 0,
					"sales_person": sales_person,
				}
				data.append(row)
	# for record in response:
	# 	customer = record.customer
	# 	customer_name = record.customer_name
	# 	net_sales = record.net_sales
	# 	sales_person = record.sales_person
		
	# 	if customer in outstandingArr:
	# 		outstanding = outstandingArr[customer]
	# 	else:
	# 		outstanding = 0

	# 	if customer in collectionArr:
	# 		collection = collectionArr[customer]
	# 	else:
	# 		collection = 0
	# 	row = {
	# 		"customer": customer,
	# 		"customer_name": customer_name,
	# 		"net_sales": net_sales,
	# 		"paid_amount": collection,
	# 		"outstanding_amount": outstanding,
	# 		"sales_collection_ratio": (collection/net_sales) * 100 if net_sales > 0 else 0,
	# 		"outstanding_collection_ratio": (collection/outstanding) * 100 if outstanding > 0 else 0,
	# 		"sales_person": sales_person,
	# 	}
	# 	data.append(row)
	return data
	