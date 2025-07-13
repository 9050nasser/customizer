# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from datetime import datetime
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, cstr
from frappe.model.db_query import DatabaseQuery
from frappe.utils import add_days, getdate, nowdate, nowtime
from frappe import get_list, get_doc
from erpnext.stock.utils import get_stock_balance
import math

    
    	
@frappe.whitelist(allow_guest=True)
# ~ @frappe.whitelist()
def get_stock_balance_for(item_code, warehouse,
	posting_date, posting_time, with_valuation_rate= True):
		
	from erpnext.stock.utils import get_stock_balance
	data = get_stock_balance(item_code, warehouse, posting_date, posting_time,
		with_valuation_rate=with_valuation_rate, with_serial_no=False)

	qty, rate = data

	return {
		'qty': qty,
		'rate': rate,
	}
	
@frappe.whitelist(allow_guest=True)
def get_item_info(item_code, warehouse):
	
	from erpnext.stock.utils import get_stock_balance
	
	data = get_stock_balance(item_code, warehouse, nowdate(), nowtime(),
		with_valuation_rate=True)

	qty, standard_rate = data
	
	item_price_list = frappe.get_list("Item Price", filters=[["price_list", "=", "Standard Selling"]])
	if item_price_list:
		item_price_doc = frappe.get_doc("Item Price", item_price_list[0].name)
		standard_rate =  item_price_doc.price_list_rate
		# ~ standard_rate =  "test"
		return {
			"qty": int(qty),
			"standard_rate" : standard_rate,
		}
		
@frappe.whitelist(allow_guest=True)	
# ~ @frappe.whitelist()
def get_stock_balance_for_list(item_list, warehouse,
	posting_date, posting_time, with_valuation_rate= True):
	res = {}
	
	from erpnext.stock.utils import get_stock_balance
	
	il =  item_list.split(",")
	for i in il:
		data = get_stock_balance(i, warehouse, posting_date, posting_time,
			with_valuation_rate=with_valuation_rate, with_serial_no=False)

		qty, rate = data

		res[i] = {'qty': qty,'rate': rate}
	return res


@frappe.whitelist(allow_guest=True)
def get_item_info1(item_code, warehouse):
	# ~ item_code = "00600"
	# ~ warehouse = "مخزن فرع الستين- جدة - P"
	from erpnext.stock.utils import get_stock_balance
	
	data = get_stock_balance(item_code, warehouse, nowdate(), nowtime(),
		with_valuation_rate=False)

	qty = data
	standard_rate =0
	
	item_price_list = frappe.get_list("Item Price", filters=[["price_list", "=", "Standard Selling"],["item_code","=",item_code]])
	print("1")
	print(item_price_list)
	
	if item_price_list:
		item_price_doc = frappe.get_doc("Item Price", item_price_list[0].name)
		print("2")
		print(item_price_doc.price_list_rate)
		standard_rate =  item_price_doc.price_list_rate
		# ~ standard_rate =  "test"
		return {
			"qty": int(qty),
			"standard_rate" : standard_rate,
		}


@frappe.whitelist(allow_guest=True)	
# ~ @frappe.whitelist()
def get_items(item_list, warehouse):
	res = {}
	# ~ item_list = "00600,030172012952"
	# ~ warehouse = "مخزن فرع الستين- جدة - P"
	from erpnext.stock.utils import get_stock_balance
	
	il =  item_list.split(",")
	
	for i in il:
		data = get_stock_balance(i, warehouse,  nowdate(), nowtime(), with_valuation_rate=True)
		qty, standard_rate = data
		print(i)
		item_price_list = frappe.get_list("Item Price", filters=[["price_list", "=", "Standard Selling"],["item_code","=",i]])
		print(item_price_list)
		if item_price_list:
			print(item_price_list)
			item_price_doc = frappe.get_doc("Item Price", item_price_list[0].name)
			standard_rate =  item_price_doc.price_list_rate
			res[i] = {
				'qty': int(qty),
				'standard_rate': standard_rate
			}
		
	return res

	
@frappe.whitelist(allow_guest=True)
def get_data_for_items(item_code=None, warehouse=None, item_group=None,
	start=0, sort_by='actual_qty', sort_order='desc'):
		
	filters = []
	
	if item_code:
		filters.append(['item_code', '=', item_code])
		
	if warehouse:
		filters.append(['warehouse', '=', warehouse])
		
	if item_group:
		lft, rgt = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"])
		items = frappe.db.sql_list("""
			select i.name from `tabItem` i
			where exists(select name from `tabItem Group`
				where name=i.item_group and lft >=%s and rgt<=%s)
		""", (lft, rgt))
		filters.append(['item_code', 'in', items])
	try:
		# check if user has any restrictions based on user permissions on warehouse
		if DatabaseQuery('Warehouse', user=frappe.session.user).build_match_conditions():
			filters.append(['warehouse', 'in', [w.name for w in frappe.get_list('Warehouse')]])
	except frappe.PermissionError:
		# user does not have access on warehouse
			return []

	items = frappe.db.get_all('Bin', fields=['item_code', 'warehouse', 'projected_qty',
			'reserved_qty', 'reserved_qty_for_production', 'reserved_qty_for_sub_contract', 'actual_qty', 'valuation_rate'],
		or_filters={
			'projected_qty': ['!=', 0],
			'reserved_qty': ['!=', 0],
			'reserved_qty_for_production': ['!=', 0],
			'reserved_qty_for_sub_contract': ['!=', 0],
			'actual_qty': ['!=', 0],
		},
		filters=filters,
		order_by=sort_by + ' ' + sort_order,
		limit_start=start,
		limit_page_length='21')

	for item in items:
		item.update({
			'item_name': frappe.get_cached_value("Item", item.item_code, 'item_name'),
			'disable_quick_entry': frappe.get_cached_value("Item", item.item_code, 'has_batch_no')
				or frappe.get_cached_value("Item", item.item_code, 'has_serial_no'),
		})

	return items
	
	
@frappe.whitelist(allow_guest=True)
def get_data(item_code=None, warehouse=None, item_group=None,
	start=0, sort_by='actual_qty', sort_order='desc'):
		
	filters = []
	
	if item_code:
		filters.append(['item_code', '=', item_code])
		
	if warehouse:
		filters.append(['warehouse', '=', warehouse])
		
	if item_group:
		lft, rgt = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"])
		items = frappe.db.sql_list("""
			select i.name from `tabItem` i
			where exists(select name from `tabItem Group`
				where name=i.item_group and lft >=%s and rgt<=%s)
		""", (lft, rgt))
		filters.append(['item_code', 'in', items])

	items = frappe.db.get_all('Bin', fields=['item_code', 'warehouse','actual_qty'],
		or_filters={
			'actual_qty': ['!=', 0],
		},
		filters=filters,
		order_by=sort_by + ' ' + sort_order,
		limit_start=start,
		limit_page_length='21')

	for item in items:
		item.update({
			'item_name': frappe.get_cached_value("Item", item.item_code, 'item_name'),
		})

	return items



@frappe.whitelist(allow_guest=True)
def get_item_info5(item_code, warehouse):
    data = get_stock_balance(item_code, warehouse, nowdate(), nowtime(), with_valuation_rate=False)
    qty = data
    standard_rate = 0

    item_price_list = get_list("Item Price", filters={"price_list": "Standard Selling", "item_code": item_code})
    
    if item_price_list:
        valid_price = None
        valid_from_list = []
        
        current_date = datetime.now().date()
        current_time = datetime.now().time()
        
        for item_price in item_price_list:
            item_price_doc = get_doc("Item Price", item_price.name)
            valid_upto = item_price_doc.valid_upto
            valid_from = item_price_doc.valid_from
            
            if valid_from and valid_from <= current_date:
                valid_from_list.append((valid_from, item_price_doc))
        
        if valid_from_list:
            valid_from_list.sort(key=lambda x: x[0], reverse=True)
            valid_price = valid_from_list[0][1].price_list_rate
            
            if valid_price:
                valid_upto = valid_from_list[0][1].valid_upto
                if valid_upto and valid_upto < current_date:
                    valid_price = None
        
        if valid_price is not None:
            standard_rate = valid_price
        else:
            for item_price in item_price_list:
                item_price_doc = get_doc("Item Price", item_price.name)
                if item_price_doc.valid_upto is None or item_price_doc.valid_upto < current_date:
                    standard_rate = item_price_doc.price_list_rate
                    break
    
    return {
        "qty": int(qty),
        "standard_rate": standard_rate,
    }



@frappe.whitelist(allow_guest=True)
def get_items2(item_list, warehouse):
    res = {}
    il = item_list.split(",")

    current_date = datetime.now().date()
    current_time_str = datetime.now().time().strftime("%H:%M:%S")
    current_time = datetime.strptime(current_time_str, "%H:%M:%S").time()

    for i in il:
        data = get_stock_balance(i, warehouse, nowdate(), nowtime(), with_valuation_rate=True)
        qty, standard_rate = data

        item_price_list = get_list("Item Price", filters={"price_list": "Standard Selling", "item_code": i})

        valid_price = None

        if item_price_list:
            valid_price = None
            valid_from_list = []

            for item_price in item_price_list:
                item_price_doc = get_doc("Item Price", item_price.name)
                valid_upto = item_price_doc.valid_upto
                valid_from = item_price_doc.valid_from

                if valid_from and valid_from <= current_date:
                    valid_from_list.append((valid_from, item_price_doc))

            if valid_from_list:
                valid_from_list.sort(key=lambda x: x[0], reverse=True)
                valid_price = valid_from_list[0][1].price_list_rate

                if valid_price:
                    valid_upto = valid_from_list[0][1].valid_upto
                    if valid_upto and valid_upto < current_date:
                        valid_price = None

            if valid_price is not None:
                standard_rate = valid_price
            else:
                for item_price in item_price_list:
                    item_price_doc = get_doc("Item Price", item_price.name)
                    if item_price_doc.valid_upto is None or item_price_doc.valid_upto < current_date:
                        standard_rate = item_price_doc.price_list_rate
                        break

        res[i] = {
            'qty': int(qty),
            'standard_rate': standard_rate
        }

    return res


@frappe.whitelist(allow_guest=True)
def get_item_info55(item_code, warehouse, uom):
    data = get_stock_balance(item_code, warehouse, nowdate(), nowtime(), with_valuation_rate=False)
    qty = data
    standard_rate = 0
    conversion_factor = None
    boxes = None

    item_price_list = get_list("Item Price", filters={"price_list": "Standard Selling", "item_code": item_code, "uom": uom})

    if item_price_list:
        valid_price = None
        valid_from_list = []

        current_date = datetime.now().date()
        current_time = datetime.now().time()

        for item_price in item_price_list:
            item_price_doc = get_doc("Item Price", item_price.name)
            valid_upto = item_price_doc.valid_upto
            valid_from = item_price_doc.valid_from

            if valid_from and valid_from <= current_date:
                valid_from_list.append((valid_from, item_price_doc))

        if valid_from_list:
            valid_from_list.sort(key=lambda x: x[0], reverse=True)
            valid_price = valid_from_list[0][1].price_list_rate

            if valid_price:
                valid_upto = valid_from_list[0][1].valid_upto
                if valid_upto and valid_upto < current_date:
                    valid_price = None

        if valid_price is not None:
            standard_rate = valid_price

        if uom:
            conversion_factor = frappe.db.get_value("Item Price", filters={"price_list": "Standard Selling", "item_code": item_code, "uom": uom}, fieldname="conversion_factor")
            if conversion_factor is not None:
                if uom == "Box" or "box":
                    boxes = qty / conversion_factor

    if uom:
        return {
            "qty": int(qty),
            "standard_rate": standard_rate,
            "box_qty": conversion_factor,
            "boxes": boxes if uom == "Box" or "box" else "",
            "uom": uom
        }
    else:
        return {
            "qty": int(qty),
            "standard_rate": standard_rate,
        }


@frappe.whitelist(allow_guest=True)
def get_items_by_warehouse(warehouse=None, start=0, sort_order='desc'):
    filters = []

    if warehouse:
        filters.append(['warehouse', '=', warehouse])

    items = frappe.db.get_all('Bin', fields=['item_code','actual_qty'],
                              or_filters={
                                  'actual_qty': ['!=', 0],
                              },
                              filters=filters,
                              order_by='item_code ' + sort_order,
                              limit_start=start,
                              limit_page_length=500)

    for item in items:
        item.update({
            'item_name': frappe.get_cached_value("Item", item.item_code, 'item_name'),
            'item_price': get_item_price(item.item_code)  
        })

    return items

def get_item_price(item_code):
    item_price = frappe.db.get_value("Item Price", filters={"item_code": item_code, "selling": 1}, fieldname="price_list_rate")
    return item_price



@frappe.whitelist(allow_guest=True)
def get_items_by_warehouse1(warehouse=None, page=1, page_length=500, sort_order='desc'):
    filters = []

    if warehouse:
        filters.append(['warehouse', '=', warehouse])

    page = int(page)
    page_length = int(page_length)

    start = (page - 1) * page_length
    end = start + page_length

    items = frappe.db.get_all('Bin', fields=['item_code', 'actual_qty'],
                              or_filters={
                                  'actual_qty': ['>', 0],
                              },
                              filters=filters,
                              order_by='item_code ' + sort_order,
                              limit_start=0,
                              limit_page_length=None)

    total_items = len(items)
    total_pages = math.ceil(total_items / page_length)

    paginated_items = items[start:end]

    for item in paginated_items:
        item.update({
            'item_name': frappe.get_cached_value("Item", item.item_code, 'item_name'),
            'item_price': get_item_price(item.item_code)
        })

    total_pages_formatted = f"{page}-{total_pages}" if total_pages > 1 else str(total_pages)

    result = {
        'total_items': total_items,
        'total_pages': total_pages_formatted,
        'items': paginated_items
    }

    return result

def get_item_price(item_code):
    item_price = frappe.db.get_value("Item Price", filters={"item_code": item_code, "selling": 1}, fieldname="price_list_rate")
    return item_price
    

@frappe.whitelist(allow_guest=True)
def get_batch_data(item_code=None):

    if not item_code:
        return []

    batch_data = frappe.db.sql("""
        SELECT sle.item_code, sle.warehouse, sle.batch_no, SUM(sle.actual_qty) AS total_qty, batch.expiry_date
        FROM `tabStock Ledger Entry` AS sle
        LEFT JOIN `tabBatch` AS batch ON sle.batch_no = batch.name
        LEFT JOIN `tabBin` AS bin ON sle.item_code = bin.item_code AND sle.warehouse = bin.warehouse
        WHERE sle.item_code = %s AND (batch.expiry_date IS NULL OR batch.expiry_date >= %s)
        GROUP BY sle.warehouse, sle.batch_no
        HAVING total_qty > 0
    """, (item_code, frappe.utils.today()), as_dict=True)

    return batch_data



@frappe.whitelist()
def set_docstatus_to_0(docname):
    try:
        # Set docstatus of the POS Invoice to 0
        frappe.db.set_value('POS Invoice', docname, 'docstatus', 0)
        
        # Get all POS Invoice Items associated with the POS Invoice
        invoice_items = frappe.get_all('POS Invoice Item', filters={'parent': docname}, fields=['name'])
        
        # Set docstatus of all associated POS Invoice Items to 0
        for item in invoice_items:
            frappe.db.set_value('POS Invoice Item', item.name, 'docstatus', 0)
        
        return 'success'
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Failed to set DocStatus')
        return 'failure'

@frappe.whitelist()
def si_set_docstatus_to_0(docname):
    """
    Sets the docstatus of the specified Sales Invoice and all its related documents to 0.
    """
    try:
        # Define related document types and their fields
        related_doc_types = [
            ('GL Entry', 'voucher_no', 'is_cancelled', 1),
            ('Stock Ledger Entry', 'voucher_no', 'is_cancelled', 1),
            ('Sales Invoice Item', 'parent', 'docstatus', 0),
            ('Sales Invoice Payment', 'parent', 'docstatus', 0),
            ('Sales Taxes and Charges', 'parent', 'docstatus', 0)
        ]
        
        # Set docstatus of the Sales Invoice to 0
        frappe.db.set_value('Sales Invoice', docname, 'docstatus', 0)

        # Update related documents
        for doctype, field, target_field, target_value in related_doc_types:
            update_related_docs(doctype, field, docname, target_field, target_value)
        
        # Cancel related Serial and Batch Bundles and set docstatus to 0
        cancel_serial_and_batch_bundles(docname)

        return 'success'
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Failed to set DocStatus')
        return 'failure'

@frappe.whitelist()
def pi_set_docstatus_to_0(docname):
    """
    Sets the docstatus of the specified Sales Invoice and all its related documents to 0.
    """
    try:
        # Define related document types and their fields
        related_doc_types = [
            ('GL Entry', 'voucher_no', 'is_cancelled', 1),
            ('Stock Ledger Entry', 'voucher_no', 'is_cancelled', 1),
            ('Purchase Invoice Item', 'parent', 'docstatus', 0),
            #('Purchase Invoice Payment', 'parent', 'docstatus', 0),
            ('Purchase Taxes and Charges', 'parent', 'docstatus', 0)
        ]
        
        # Set docstatus of the Sales Invoice to 0
        frappe.db.set_value('Purchase Invoice', docname, 'docstatus', 0)

        # Update related documents
        for doctype, field, target_field, target_value in related_doc_types:
            update_related_docs(doctype, field, docname, target_field, target_value)
        
        # Cancel related Serial and Batch Bundles and set docstatus to 0
        cancel_serial_and_batch_bundles(docname)

        return 'success'
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Failed to set DocStatus')
        return 'failure'

def update_related_docs(doctype, field, value, target_field, target_value):
    """
    Updates the specified field of related documents to the target value.
    """
    related_docs = frappe.get_all(doctype, filters={field: value}, fields=['name'])
    for doc in related_docs:
        frappe.db.set_value(doctype, doc.name, target_field, target_value)

def cancel_serial_and_batch_bundles(docname):
    """
    Cancels related Serial and Batch Bundles and sets their docstatus to 0.
    """
    try:
        serial_and_batch_bundles = frappe.get_all('Serial and Batch Bundle', filters={'voucher_no': docname}, fields=['name'])
        for bundle in serial_and_batch_bundles:
            bundle_doc = frappe.get_doc('Serial and Batch Bundle', bundle.name)
            bundle_doc.cancel()
            frappe.db.set_value('Serial and Batch Bundle', bundle.name, 'docstatus', 0)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Failed to set Serial and Batch Bundles')
        return 'failure'



@frappe.request_cache
def get_last_purchase_details():
    item_code = "653945454713"
    doc_name = None
    conversion_rate = 1.0
    
    last_purchase_order = frappe.db.sql(
        """\
        select po.name, po.transaction_date, po.conversion_rate,
            po_item.conversion_factor, po_item.base_price_list_rate,
            po_item.discount_percentage, po_item.base_rate, po_item.base_net_rate
        from `tabPurchase Order` po, `tabPurchase Order Item` po_item
        where po.docstatus = 1 and po_item.item_code = %s and po.name != %s and
            po.name = po_item.parent
        order by po.transaction_date desc, po.name desc
        limit 1""",
        (item_code, cstr(doc_name)),
        as_dict=1,
    )

    # get last purchase receipt item details
    last_purchase_receipt = frappe.db.sql(
        """\
        select pr.name, pr.posting_date, pr.posting_time, pr.conversion_rate,
            pr_item.conversion_factor, pr_item.base_price_list_rate, pr_item.discount_percentage,
            pr_item.base_rate, pr_item.base_net_rate
        from `tabPurchase Receipt` pr, `tabPurchase Receipt Item` pr_item
        where pr.docstatus = 1 and pr_item.item_code = %s and pr.name != %s and
            pr.name = pr_item.parent
        order by pr.posting_date desc, pr.posting_time desc, pr.name desc
        limit 1""",
        (item_code, cstr(doc_name)),
        as_dict=1,
    )

    purchase_order_date = getdate(
        last_purchase_order and last_purchase_order[0].transaction_date or "1900-01-01"
    )
    purchase_receipt_date = getdate(
        last_purchase_receipt and last_purchase_receipt[0].posting_date or "1900-01-01"
    )

    if last_purchase_order and (purchase_order_date >= purchase_receipt_date or not last_purchase_receipt):
        # use purchase order
        last_purchase = last_purchase_order[0]
        purchase_date = purchase_order_date

    elif last_purchase_receipt and (purchase_receipt_date > purchase_order_date or not last_purchase_order):
        # use purchase receipt
        last_purchase = last_purchase_receipt[0]
        purchase_date = purchase_receipt_date

    else:
        return frappe._dict()

    conversion_factor = flt(last_purchase.conversion_factor)
    out = frappe._dict(
        {
            "base_price_list_rate": flt(last_purchase.base_price_list_rate) / conversion_factor,
            "base_rate": flt(last_purchase.base_rate) / conversion_factor,
            "base_net_rate": flt(last_purchase.base_net_rate) / conversion_factor,
            "discount_percentage": flt(last_purchase.discount_percentage),
            "purchase_date": purchase_date,
            "Mad":"Mad"

        }
    )

    conversion_rate = flt(conversion_rate) or 1.0
    out.update(
        {
            "price_list_rate": out.base_price_list_rate / conversion_rate,
            "rate": out.base_rate / conversion_rate,
            "base_rate": out.base_rate,
            "base_net_rate": out.base_net_rate,
            "Name":last_purchase.name
        }
    )

    return out