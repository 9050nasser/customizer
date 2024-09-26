# -*- coding: utf-8 -*-
# Copyright (c) 2021, Ahmed and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


def get_permission_query_conditions(user):
	if not user: 
		user = frappe.session.user 
	if "System Manager" in frappe.get_roles(user):
		return
	return """(`tabAdministrative Communication`.name in (select parent from `tabRecipient` where user = {user}) 
		and `tabAdministrative Communication`.docstatus = 1) or `tabAdministrative Communication`.for_all =1  or `tabAdministrative Communication`.owner ={user}  """.format(user=frappe.db.escape(user))
	



def validate_access_stock_entry(doc, user):
	recipient =[]
	if not user: 
		user = frappe.session.user 
	if "Stock Manager" in frappe.get_roles(user) or "System Manager" in frappe.get_roles(user):
		return True
	if not  (user == doc.from_warehouse_supervise or user == doc.to_warehouse_supervise)  :
		return False
	
	return True
	
def get_permission_query_conditions_stock_entry(user):
	if not user: 
		user = frappe.session.user 
	if "Stock Manager" in frappe.get_roles(user) or "System Manager" in frappe.get_roles(user):
		return
	return """(`tabStock Entry`.from_warehouse_supervise ={user} or `tabStock Entry`.to_warehouse_supervise ={user} )""".format(user=frappe.db.escape(user))
	






