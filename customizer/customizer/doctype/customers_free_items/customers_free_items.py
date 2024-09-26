# -*- coding: utf-8 -*-
# Copyright (c) 2023, Ahmed and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt, fmt_money, formatdate

class CustomersFreeItems(Document):
	pass
	
	
	def validate(self):
		self.get_total()
		self.set_status()

	def get_total(self):
		total_qty = 0

		for d in self.free_customer_items:
			total_qty += flt(d.total_qty)

		self.total_qty = total_qty

	def set_status(self):
		total_qty = sum(item.total_qty for item in self.free_customer_items)
		for item in self.free_customer_items:
			free_item = frappe.get_doc("Free Items", {"item_code": item.item_code, "enabled": 1})
			if free_item and total_qty >= free_item.qty:
				self.status = "Completed"
				break
