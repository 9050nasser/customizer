# Copyright (c) 2013, Ahmed and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, now, date_diff
from erpnext.stock.stock_ledger import get_previous_sle, get_valuation_rate
from erpnext.stock.utils import get_stock_balance 
from datetime import date
from datetime import datetime


def execute(filters=None):
	now = datetime.now()
	columns = get_columns(filters)
	data = get_data(filters)
	data_map ={}
	for d in data :
		if d.item_code not in data_map:
			data_map[d.item_code] = [d]
		else:
			data_map[d.item_code].append(d)
	res =[]
	for v in data_map.values() :
		res.append(v[0])
	data = res
			
	if filters.get("warehouse"): 
		for d in data:
			vr = get_stock_balance(d.item_code,filters.get("warehouse"), date.today(), datetime.now().time(),with_valuation_rate=True, with_serial_no= False )
			qty, rate = vr
			d["valuation_rate"]=rate
	return columns, data


def get_columns(filters):
	"""return columns"""

	columns = [
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 100},
		{"label": _("Item Name"), "fieldname": "item_name", "width": 150},
		{"label": _("Description"), "fieldname": "item_description", "width": 140},
		{"label": _("Price Rate"), "fieldname": "price_list_rate", "fieldtype": "Currency", "width": 90, "convertible": "rate"},
		{"label": _("Stock UOM"), "fieldname": "uom", "fieldtype": "Link", "options": "UOM", "width": 90},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand", "width": 90},
	]
	if filters.get("warehouse"): 
		columns += [
			{"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 90, "convertible": "rate"},
		]

	return columns

def get_conditions(filters):
	conditions = ""
	if not filters.get("price_list"):
		frappe.throw(_("'Price List' is required"))

	if filters.get("item_group"):
		item_group_details = frappe.db.get_value("Item Group",
			filters.get("item_group"), ["lft", "rgt"], as_dict=1)
		if item_group_details:
			conditions += " and exists (select name from `tabItem Group` ig \
				where ig.lft >= %s and ig.rgt <= %s and sle.item_group = ig.name)"%(item_group_details.lft,
				item_group_details.rgt)

	if filters.get("price_list"):
		conditions += " and ip.price_list = %s" % frappe.db.escape(filters.get("price_list"))
		
	if filters.get("item_code"):
		conditions += " and ip.item_code = %s" % frappe.db.escape(filters.get("item_code"))
	
	if filters.get("tag"):
		conditions += " and ip.item_code in (select document_name from `tabTag Link` where document_type='Item' and tag = '%s' ) "%(filters.get("tag"))
	
	conditions += """ and %(transaction_date)s between ifnull(valid_from, '2000-01-01') and ifnull(valid_upto, '2500-12-31')"""
	return conditions
	
def get_data(filters):

	conditions = get_conditions(filters)
	args = {'transaction_date':date.today()}
	return frappe.db.sql("""
		select
			ip.item_code,
			ip.item_name,
			ip.brand,
			ip.price_list,
			ip.item_description,
			ip.uom,
			ip.price_list_rate
		from
			`tabItem Price` ip 		

		where ip.docstatus < 2 %s 
		order by ip.valid_from desc""" %(conditions),args, as_dict=1)
		
		# ~ inner join (
			# ~ select item_code, max(valid_from) as MaxDate
			# ~ from `tabItem Price`
			# ~ group by item_code
		# ~ ) tm on ip.item_code = tm.item_code and ip.valid_from = tm.MaxDate		
	# ~ return frappe.db.sql("""
		# ~ select
			# ~ ip.item_code,
			# ~ ip.item_name,
			# ~ ip.brand,
			# ~ ip.price_list,
			# ~ ip.item_description,
			# ~ ip.uom,
			# ~ ip.price_list_rate
		# ~ from
			# ~ `tabItem Price` ip 
		# ~ inner join (
			# ~ select item_code, max(valid_from) as MaxDate
			# ~ from `tabItem Price`
			# ~ group by item_code
		# ~ ) tm on ip.item_code = tm.item_code and ip.valid_from = tm.MaxDate
		# ~ where ip.docstatus < 2 %s """ %( conditions), as_dict=1)
