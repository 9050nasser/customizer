# -*- coding: utf-8 -*-
# Copyright (c) 2023, Ahmed and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from datetime import date, datetime
from frappe.utils import nowdate



class FreeItems(Document):
	def validate(self):
		self.validate_items()
		self.validate_qty()
	
	def validate_items(self):
		if not self.item_code:
			frappe.throw(_("Item Code is required"))
	
	def validate_qty(self):
		self.qty = self.total_qty + self.free_item
	
