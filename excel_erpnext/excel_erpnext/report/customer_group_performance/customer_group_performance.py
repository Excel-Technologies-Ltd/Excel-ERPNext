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
	data,total_net_sales,total_collection = get_result(filters)
	
	return columns, data

def get_columns(filters):

	columns = [
		{"label": ("Territory"), "fieldname": "territory", "fieldtype": "data","width": 100},
		{"label": ("Customer Group"), "fieldname": "customer_group", "fieldtype": "data","width": 150},
		{"label": ("Total Account Receivable"), "fieldname": "total_account_receivable", "fieldtype": "Currency","options": "currency","width": 150},
		{"label": ("Net Sales"), "fieldname": "net_sales", "fieldtype": "Currency","options": "currency","width": 100},
		{"label": ("Collection"), "fieldname": "paid_amount", "fieldtype": "Currency","options": "currency","width": 100},
		{"label": ("Sales Collection Ratio"), "fieldname": "sales_collection_ratio", "fieldtype": "Float","width": 100},
		{"label": ("Account Receivable Collection Ratio"), "fieldname": "outstanding_collection_ratio", "fieldtype": "Float","width": 100},
		{"label": ("Sales Contribution in Company"), "fieldname": "sales_contribution", "fieldtype": "Float","width": 100},
		{"label": ("Collection Contribution in Company"), "fieldname": "collection_contribution", "fieldtype": "Float","width": 100},
	]

	return columns

def get_result(filters):
	
	gl_entrie = frappe.db.sql("""
					select
							cu.territory, cu.customer_group, sum(gl.debit) as debit, sum(gl.credit) as credit
					from
							`tabGL Entry` gl left join `tabCustomer` cu on  cu.name = gl.party
					where
							gl.docstatus < 2
							and gl.party_type="Customer"
							group by cu.territory, cu.customer_group order by cu.territory, cu.customer_group"""
					,as_dict = 1)
	outstandingArr = {}
	for j in gl_entrie:
		debit = j['debit']
		credit = j['credit']
		outstanding = debit - credit
		outstandingArr[j['territory']+":"+j['customer_group']]= outstanding
	
	collection_data = frappe.db.sql(""" SELECT
							sum(pe.paid_amount) as paid_amount, cu.territory, cu.customer_group
							FROM `tabPayment Entry` pe left join `tabCustomer` cu on  cu.name = pe.party
							where pe.docstatus = 1 and pe.posting_date >= %s and pe.posting_date <= %s and pe.excel_tax_payment = "No" and pe.party_type = "Customer" group by cu.territory, cu.customer_group
							""",(filters.get('from_date'),filters.get('to_date')), as_dict = 1)
	collectionArr = {}
	total_collection = 0
	for k in collection_data:
		collection_amount = k['paid_amount']
		collectionArr[k['territory']+":"+k['customer_group']] = collection_amount
		total_collection += collection_amount

	conditions = ""
	
	conditions += "si.docstatus = 1"
	if filters.get("from_date"): conditions += " and si.posting_date >= '%s'" % filters.get("from_date")
	if filters.get("to_date"): conditions += " and si.posting_date <= '%s' " % filters.get("to_date")
	if filters.get("territory"): conditions += " and cp.territory = '%s' " %filters.get("territory")
	if filters.get("brand"): conditions += " and sii.brand = '%s' " %filters.get("brand")
	if filters.get("customer_group"): conditions += " and cp.customer_group = '%s' " %filters.get("customer_group")

	response = frappe.db.sql("""
			SELECT 
				cp.customer_group, cp.territory, 
				sum(sii.net_amount) as net_sales 
			FROM `tabSales Invoice Item` sii left join `tabSales Invoice` si on si.name = sii.parent left join `tabCustomer` cp on cp.name = si.customer
			where
				{conditions}
			group by cp.customer_group, cp.territory order by sum(sii.net_amount) desc""".format(conditions=conditions),as_dict=1)

	
	data = []
	total_net_sales = 0
	for record in response:
		customer_group = record.customer_group
		territory = record.territory
		total_net_sales += record.net_sales
	for record in response:
		customer_group = record.customer_group
		territory = record.territory
		net_sales = record.net_sales
		key = territory+":"+customer_group
		if key in outstandingArr:			
			outstanding = outstandingArr[key]		
		else:
			outstanding = 0
		if key in collectionArr:
		 	collection = collectionArr[key]
		else:
		 	collection = 0
		
		sales_contribution = (net_sales/total_net_sales) * 100
		collection_contribution = (collection/total_collection) * 100
		row = {
			"territory": territory,
			"customer_group": customer_group,
			"net_sales": net_sales,
			"paid_amount": collection,
			"total_account_receivable": outstanding,
			"sales_collection_ratio": (collection/net_sales) * 100 if net_sales > 0 else 0,
			"outstanding_collection_ratio": (collection/outstanding) * 100 if outstanding > 0 else 0,
			"sales_contribution": sales_contribution,
			"collection_contribution": collection_contribution,
			
		}
		data.append(row)
	return data, 0,0
	