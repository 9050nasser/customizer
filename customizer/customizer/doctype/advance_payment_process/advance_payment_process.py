# -*- coding: utf-8 -*-
# Copyright (c) 2021, Ahmed and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from erpnext.accounts.utils import get_balance_on
import frappe
from frappe.model.document import Document

class AdvancePaymentProcess(Document):
	
	def get_employee_advance_balance (self,employee):
		party_type="Employee"
		party = employee
		cost_center =None
		account = self.advance_payment_account
		return get_balance_on(account=account,party_type=party_type, party=party, cost_center=cost_center)
