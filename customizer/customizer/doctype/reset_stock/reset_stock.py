# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.stock.utils import get_stock_balance, get_incoming_rate, get_available_serial_nos
from frappe.utils import cstr, flt, cint
from frappe import msgprint, _
import copy

class ResetStock(Document):
	def on_submit(self):
		# ~ self.validate_duplicate()
		# ~ self.validate_valuation_rate()
		self.set_total_qty_and_amount()
		self.validate_data()
		self.create_stock_reconsilation()
	

	def submit(self):
		# ~ self.create_stock_reconsilation()
		if len(self.items) > 500:
			self.validate_data()
			msgprint(_("The task has been enqueued as a background job. In case there is any issue on processing in background, the system will add a comment about the error on this Stock Reconciliation and revert to the Draft stage"))
			self.queue_action('submit', timeout=4000000)
		else:
			self._submit()
	
	def create_stock_reconsilation(self):
		doc = frappe.new_doc("Stock Reconciliation")
		doc.purpose ="Stock Reconciliation"
		doc.expense_account =self.expense_account
		doc.cost_center =self.cost_center
		for item in self.get("items"):
			print(item.item_code)
			new_item= {
				"item_code": item.item_code,
				"warehouse": item.warehouse,
				"qty": 0,
				"batch_no": item.batch_no,
				"item_name": item.item_name,
				"valuation_rate": item.valuation_rate,
				"current_qty":  item.current_qty,
				"current_valuation_rate":  item.current_valuation_rate
			}
			row = doc.append('items',new_item)
			doc.flags.ignore_validate = True
			doc.flags.ignore_mandatory = True
			doc.save()
			frappe.db.commit()
			
			# ~ new_item = copy.deepcopy(item)
			# ~ new_item.name = ""
			# ~ row = doc.append('items',new_item)
			# ~ doc.flags.ignore_validate = True
			# ~ doc.flags.ignore_mandatory = True
			# ~ doc.save()
			# ~ frappe.db.commit()
		doc.save()

	def set_total_qty_and_amount(self):
		for d in self.get("items"):
			try:
				d.amount = flt(d.qty, d.precision("qty")) * flt(d.valuation_rate, d.precision("valuation_rate"))
			except:
				frappe.throw(str(dir(d)))
				d.amount = flt(0,2) * flt(d.valuation_rate, 2)
				
			d.current_amount = (flt(d.current_qty,
				d.precision("current_qty")) * flt(d.current_valuation_rate, d.precision("current_valuation_rate")))

			d.quantity_difference = flt(d.qty) - flt(d.current_qty)
			d.amount_difference = flt(d.amount) - flt(d.current_amount)

	def validate(self):
		self.validate_data()
		self.set_total_qty_and_amount()
		
	def validate_data(self):
		def _get_msg(row_num, msg):
			return _("Row # {0}: ").format(row_num+1) + msg

		self.validation_messages = []
		item_warehouse_combinations = []

		default_currency = frappe.db.get_default("currency")
		new_batched_items =[]
		for row_num, row in enumerate(self.items):
			new_batched_items.extend(self.validate_item(row.item_code, row))

			# do not allow negative quantity
			if flt(row.qty) < 0:
				row.qty=0.00
				

			# do not allow negative valuation
			if flt(row.valuation_rate) < 0:
				self.validation_messages.append(_get_msg(row_num,
					_("Negative Valuation Rate is not allowed")))


		# throw all validation messages
		if self.validation_messages:
			for msg in self.validation_messages:
				msgprint(msg)

			raise frappe.ValidationError(self.validation_messages)
		if new_batched_items :
			# ~ frappe.throw(str(len(new_batched_items)))
			i=1
			for item in new_batched_items:
				print(i)
				i+=1
				print(item.item_code)
				print(item.batch_no)
				self.append("items",item)
		self.reset_idex()
	
	def reset_idex(self):
		i=1
		for item in self.get("items"):
			item.idx = i 
			i+=1
		

	def validate_item(self, item_code, row):
		from erpnext.stock.doctype.item.item import validate_end_of_life, \
			validate_is_stock_item, validate_cancelled_item
		batched_items = []
		# using try except to catch all validation msgs and display together

		try:
			item = frappe.get_doc("Item", item_code)

			# end of life and stock item
			validate_end_of_life(item_code, item.end_of_life, item.disabled, verbose=0)
			validate_is_stock_item(item_code, item.is_stock_item, verbose=0)

			# item should not be serialized
			if item.has_serial_no and not row.serial_no and not item.serial_no_series:
				raise frappe.ValidationError(_("Serial no(s) required for serialized item {0}").format(item_code))

			# item managed batch-wise not allowed
			if item.has_batch_no and not row.batch_no :
				raise frappe.ValidationError(_("Batch no is required for batched item {0}").format(item_code))

			# docstatus should be < 2
			validate_cancelled_item(item_code, item.docstatus, verbose=0)
			return batched_items
		except Exception as e:
			self.validation_messages.append(_("Row # ") + ("%d: " % (row.idx)) + cstr(e))
			return []

@frappe.whitelist()
def get_items(warehouse, posting_date, posting_time, company,review_stock_reconciliation):
	
	lft, rgt = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"])
	if not review_stock_reconciliation:
		items = frappe.db.sql("""
			select i.name, i.item_name, bin.warehouse
			from tabBin bin, tabItem i
			where i.name=bin.item_code and i.disabled=0 and i.is_stock_item = 1
			and i.has_variants = 0 and i.has_batch_no = 0
			and exists(select name from `tabWarehouse` where lft >= %s and rgt <= %s and name=bin.warehouse)
		""", (lft, rgt))
	else :
		items = frappe.db.sql("""
			select i.name, i.item_name, bin.warehouse
			from tabBin bin, tabItem i
			where i.name=bin.item_code and i.disabled=0 and i.is_stock_item = 1
			and i.has_variants = 0 and i.has_batch_no = 0
			and exists(select name from `tabWarehouse` where lft >= %s and rgt <= %s and name=bin.warehouse)
			and i.name not in (select distinct ssri.item_code from `tabStock Reconciliation Item` as ssri where ssri.parent = %s)
		""", (lft, rgt,review_stock_reconciliation))
	
	review_batchs = frappe.db.sql("""select distinct batch_no from `tabStock Reconciliation Item` where parent = %s
	""", (review_stock_reconciliation),as_list=True)	
	
	batches_in_warehouse = frappe.db.sql('''select batch_no, sum(actual_qty) as qty,item_code
		from `tabStock Ledger Entry`
		where warehouse=%s
		group by batch_no''', (warehouse), as_dict=1)

	# ~ items += frappe.db.sql("""
		# ~ select i.name, i.item_name, id.default_warehouse
		# ~ from tabItem i, `tabItem Default` id
		# ~ where i.name = id.parent
			# ~ and exists(select name from `tabWarehouse` where lft >= %s and rgt <= %s and name=id.default_warehouse)
			# ~ and i.is_stock_item = 1 and i.has_serial_no = 0 and i.has_batch_no = 0
			# ~ and i.has_variants = 0 and i.disabled = 0 and id.company=%s
		# ~ group by i.name
	# ~ """, (lft, rgt, company))

	res = []
	for d in set(items):
		stock_bal = get_stock_balance(d[0], d[2], posting_date, posting_time,
			with_valuation_rate=True)
		if stock_bal[0] != 0:
			if frappe.db.get_value("Item", d[0], "disabled") == 0:
				res.append({
					"item_code": d[0],
					"warehouse": d[2],
					"qty": 0,
					"item_name": d[1],
					"valuation_rate": stock_bal[1],
					"current_qty": stock_bal[0],
					"current_valuation_rate": stock_bal[1]
				})
	flat_list = [item for sublist in review_batchs for item in sublist]
	for b in batches_in_warehouse:
		print(b)
		if b.batch_no and b.batch_no!="":
			if b.batch_no not in flat_list:
				stock_bal = get_stock_balance(b.item_code, warehouse, posting_date, posting_time,
					with_valuation_rate=True)
				if  b.qty != 0:
					if frappe.db.get_value("Item",b.item_code, "disabled") == 0:
						res.append({
							"item_code": b.item_code,
							"warehouse": warehouse,
							"qty": 0,
							"batch_no": b.batch_no,
							# ~ "item_name": b.item_name,
							"valuation_rate": stock_bal[1],
							"current_qty": b.qty,
							"current_valuation_rate": stock_bal[1]
						})
	

	return res


def get_batch_qty(batch_no=None, warehouse=None, item_code=None):
	"""Returns batch actual qty if warehouse is passed,
		or returns dict of qty by warehouse if warehouse is None

	The user must pass either batch_no or batch_no + warehouse or item_code + warehouse

	:param batch_no: Optional - give qty for this batch no
	:param warehouse: Optional - give qty for this warehouse
	:param item_code: Optional - give qty for this item"""

	out = 0
	if batch_no and warehouse:
		out = float(frappe.db.sql("""select sum(actual_qty)
			from `tabStock Ledger Entry`
			where warehouse=%s and batch_no=%s""",
			(warehouse, batch_no))[0][0] or 0)

	if batch_no and not warehouse:
		out = frappe.db.sql('''select warehouse, sum(actual_qty) as qty
			from `tabStock Ledger Entry`
			where batch_no=%s
			group by warehouse''', batch_no, as_dict=1)

	if not batch_no and item_code and warehouse:
		out = frappe.db.sql('''select batch_no, sum(actual_qty) as qty
			from `tabStock Ledger Entry`
			where item_code = %s and warehouse=%s
			group by batch_no''', (item_code, warehouse), as_dict=1)

	return out
