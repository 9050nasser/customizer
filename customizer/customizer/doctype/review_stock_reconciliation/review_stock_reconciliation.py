# -*- coding: utf-8 -*-
# Copyright (c) 2020, Ahmed and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, erpnext
import frappe.defaults
from frappe import msgprint, _
from frappe.utils import cstr, flt, cint
from erpnext.stock.stock_ledger import update_entries_after
from erpnext.controllers.stock_controller import StockController
from erpnext.accounts.utils import get_company_default
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
from erpnext.stock.utils import get_stock_balance, get_incoming_rate, get_available_serial_nos
from erpnext.stock.doctype.batch.batch import get_batch_qty
from frappe.model.document import Document
import copy

class OpeningEntryAccountError(frappe.ValidationError): pass
class EmptyStockReconciliationItemsError(frappe.ValidationError): pass

class ReviewStockReconciliation(StockController):
	def validate(self):
		# ~ msgprint(_("The task has been enqueued as a background job. In case there is any issue on processing in background, the system will add a comment about the error on this Review Stock Reconciliation and revert to the Draft stage"))
		# ~ self.queue_action('on_validate', timeout=400000)
		# ~ if len(self.items) > 500:
			# ~ msgprint(_("The task has been enqueued as a background job. In case there is any issue on processing in background, the system will add a comment about the error on this Stock Reconciliation and revert to the Draft stage"))
			# ~ self.queue_action('on_validate')
		# ~ else:
			# ~ self.on_validate()
		self.on_validate()
		
		# ~ if not self.get("items"):
			# ~ self.get_items_details()
		# ~ self.get_items_details()
		# ~ self.set_total_qty_and_amount()
		# ~ self.remove_items_with_no_change()
		# ~ self.create_stock_reconsilation()
	def before_update_after_submit(self):
		self.on_submit_stock_reconciliation()
		frappe.msgprint("Batch ")
	def on_validate(self):
		if not self.get("items"):
			self.get_items_details()
		# ~ self.validate_duplicate()
		self.set_total_qty_and_amount()
		self.remove_items_with_no_change()
		self.reset_idex()
		self.on_submit_stock_reconciliation()
		# ~ self.create_stock_reconsilation()
		
	def on_submit_stock_reconciliation(self):
		for d in self.get("items"):
			if d.batch_no:
				existing_batch = frappe.get_all("Batch", filters={"item": d.item_code, "name": d.batch_no}, fields=["name"])
				if not existing_batch:
					try:self.create_batch_entry(d)
					except:pass
					frappe.msgprint("Batch '{}' created for item '{}' with batch number '{}'.".format(d.name, d.item_code, d.batch_no))


	def create_batch_entry(self,d):
    		batch_entry = frappe.new_doc("Batch")
    		batch_entry.item = d.item_code
    		batch_entry.batch_id = d.batch_no
    		batch_entry.insert(ignore_permissions=True)
    		frappe.db.commit()

	def remove_items_with_no_change(self):
		"""Remove items if qty or rate is not changed"""
		self.difference_amount = 0.0
		def _changed(item):
			item_dict = get_stock_balance_for(item.item_code, item.warehouse,
				self.posting_date, self.posting_time, batch_no=item.batch_no)
			item.valuation_rate = item_dict.get("rate")
			
			if item.valuation_rate == 0 or not item.valuation_rate :
				item.valuation_rate = frappe.db.get_value("Item", item.item_code,'valuation_rate')
				
			if ((item.qty is None or item.qty==item_dict.get("qty")) and
				(item.valuation_rate is None or item.valuation_rate==item_dict.get("rate")) and
				(not item.serial_no or (item.serial_no == item_dict.get("serial_nos")) )):
				return False
			else:
				# set default as current rates
				if item.qty is None:
					item.qty = item_dict.get("qty")

				if item.valuation_rate is None:
					item.valuation_rate = item_dict.get("rate")

				if item.valuation_rate is None or item.valuation_rate == 0:
					item.valuation_rate = frappe.db.get_value("Item", item.item_code,'valuation_rate')

				if item_dict.get("serial_nos"):
					item.current_serial_no = item_dict.get("serial_nos")
					if self.purpose == "Stock Reconciliation" and not item.serial_no:
						item.serial_no = item.current_serial_no

				item.current_qty = item_dict.get("qty")
				item.current_valuation_rate = item_dict.get("rate")
				item.quantity_difference = flt(item.qty) - flt(item.current_qty)
				item.amount_difference = flt(item.amount) - flt(item.current_amount)
				self.difference_amount += (flt(item.qty, item.precision("qty")) * \
					flt(item.valuation_rate or item_dict.get("rate"), item.precision("valuation_rate")) \
					- flt(item_dict.get("qty"), item.precision("qty")) * flt(item_dict.get("rate"), item.precision("valuation_rate")))
				return True

		items = list(filter(lambda d: _changed(d), self.items))

		if not items:
			frappe.throw(_("None of the items have any change in quantity or value."))

		elif len(items) != len(self.items):
			self.items = items
			for i, item in enumerate(self.items):
				item.idx = i + 1
			frappe.msgprint(_("Removed items with no change in quantity or value."))
	
	def on_submit(self):
		# ~ self.validate_duplicate()
		# ~ self.validate_valuation_rate()
		self.create_stock_reconsilation()
		self.reset_idex()
	
	def submit(self):
		# ~ self.create_stock_reconsilation()
		if len(self.items) > 500:
			msgprint(_("The task has been enqueued as a background job. In case there is any issue on processing in background, the system will add a comment about the error on this Stock Reconciliation and revert to the Draft stage"))
			self.queue_action('submit', timeout=4000000)
		else:
			self._submit()
			
	def validate_valuation_rate(self):
		for item in self.get("items"):
			if item.valuation_rate == 0 or not item.valuation_rate:
				frappe.throw("Valuation Rate requred in row {0} for item {1}".format(item.idx,item.item_code))
	
	def reset_idex(self):
		i=1
		for item in self.get("items"):
			item.idx = i 
			i+=1
	def create_stock_reconsilation(self):
		doc = frappe.new_doc("Stock Reconciliation")
		doc.purpose ="Stock Reconciliation"
		doc.posting_date = self.posting_date
		doc.posting_time = self.posting_time
		doc.set_posting_time = 1
		doc.expense_account =self.expense_account
		doc.cost_center =self.cost_center
		for item in self.get("items"):
			print(item.item_code)
			new_item= {
				"item_code": item.item_code,
				"warehouse": item.warehouse,
				"qty": item.qty,
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
		
	
	def validate_duplicate(self):
		uniqe_items = {}
		sub_list = [d.sub_stock_reconciliation for d in self.get("sub_stock_reconciliation_details")]
		for sub  in sub_list:
			if not uniqe_items.get(sub):
				uniqe_items[sub] = sub
			else :
				frappe.throw("Dublicated Sub Stock Seconciliation")

	def get_items_details(self):
		self.items = []
		uniqe_items = {}
		batched_item = {}
		sub_list = [d.sub_stock_reconciliation for d in self.get("sub_stock_reconciliation_details")]
		items = frappe.get_list('Stock Reconciliation Item', fields=['*'], \
		filters=[['parent', 'IN', sub_list]])
		# ~ frappe.throw(str(len(items)))
		for i in items : 
			if not i.batch_no:
				if not uniqe_items.get(i.item_code):
					uniqe_items[i.item_code] = i
				else :
					uniqe_items[i.item_code]["qty"] = uniqe_items[i.item_code]["qty"] + i["qty"]
			else:
				if not batched_item.get(i.batch_no):
					batched_item[i.batch_no] = i
				else :
					batched_item[i.batch_no]["qty"] = batched_item[i.batch_no]["qty"] + i["qty"]
				
		for item in batched_item:
			batched_item[item]["name"] = ""
			row = self.append('items',batched_item[item])
			
		
		for item in uniqe_items:
			uniqe_items[item]["name"] = ""
			row = self.append('items',uniqe_items[item])

		
	def set_total_qty_and_amount(self):
		for d in self.get("items"):
			d.amount = flt(d.qty, d.precision("qty")) * flt(d.valuation_rate, d.precision("valuation_rate"))
			d.current_amount = (flt(d.current_qty,
				d.precision("current_qty")) * flt(d.current_valuation_rate, d.precision("current_valuation_rate")))

			d.quantity_difference = flt(d.qty) - flt(d.current_qty)
			d.amount_difference = flt(d.amount) - flt(d.current_amount)


@frappe.whitelist()
def get_stock_balance_for(item_code, warehouse,
	posting_date, posting_time, batch_no=None, with_valuation_rate= True):
	frappe.has_permission("Stock Reconciliation", "write", throw = True)
	item_dict = frappe.db.get_value("Item", item_code,
		["has_serial_no", "has_batch_no"], as_dict=1)
	serial_nos = ""
	with_serial_no = True if item_dict.get("has_serial_no") else False
	data = get_stock_balance(item_code, warehouse, posting_date, posting_time,
		with_valuation_rate=with_valuation_rate, with_serial_no=with_serial_no)
	if with_serial_no:qty, rate, serial_nos = data
	else: qty, rate = data
	if item_dict.get("has_batch_no"):qty = get_batch_qty(batch_no, warehouse) or 0
	res =  {
		'item':item_code,
		'batch_no':batch_no,
		'qty': qty,
		'rate': rate,
		'serial_nos': serial_nos
	}
	print(str(res))
	return res 
