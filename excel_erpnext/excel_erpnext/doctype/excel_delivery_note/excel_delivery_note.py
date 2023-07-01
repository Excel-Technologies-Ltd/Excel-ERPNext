# -*- coding: utf-8 -*-
# Copyright (c) 2022, Castlecraft Ecommerce Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import uuid
# import frappe

from frappe.model.document import Document

class ExcelDeliveryNote(Document):
	def autoname(self):
		self.name = str(uuid.uuid4())
