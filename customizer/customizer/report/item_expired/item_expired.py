# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import cint, getdate
from frappe.utils import flt, cint, getdate, today
from datetime import datetime, date


def execute(filters=None):
    if not filters:
        filters = {}
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    float_precision = cint(frappe.db.get_default("float_precision")) or 3

    columns = get_columns(filters)
    item_map = get_item_details(filters)
    iwb_map = get_item_warehouse_batch_map(filters, float_precision)

    data = []
    for item in sorted(iwb_map):
        for wh in sorted(iwb_map[item]):
            for batch in sorted(iwb_map[item][wh]):
                qty_dict = iwb_map[item][wh][batch]
                if qty_dict.bal_qty:
                    expiry_date = frappe.db.get_value("Batch", batch, "expiry_date")
                    exp_date = frappe.utils.data.getdate(expiry_date)
                    if exp_date >= getdate(from_date) and exp_date <= getdate(to_date) and qty_dict.expiry_status > 0:
                        data.append([
                            item,
                            item_map[item]["item_name"],
                            item_map[item]["brand"],
                            wh,
                            batch,
                            expiry_date,
                            qty_dict.expiry_status,
                            flt(qty_dict.bal_qty, float_precision)
                        ])

    # sort by expiry date in ascending order
    data = sorted(data, key=lambda x: (frappe.utils.data.getdate(x[5]) if x[5] else frappe.utils.data.getdate('2099-12-31'), x[7]))
       
    return columns, data

def get_columns(filters):

	columns = (
		[_("Item") + ":Link/Item:100"]
		+ [_("Item Name") + "::150"]
		+ [_("Brand") + ":Link/Brand:100"]
		+ [_("Warehouse") + ":Link/Warehouse:180"]
		+ [_("Batch") + ":Link/Batch:180"]
		+ [_("Expires On") + ":Date:90"]
		+ [_("Expiry (In Days)") + ":Int:100"]
		+ [_("Balance Qty") + ":Float:90"]

	)

	return columns


def get_conditions(filters):
	conditions = ""
	
	if not filters.get("from_date"):
		frappe.throw(_("'From Date' is required"))

	if filters.get("to_date"):
		conditions += " and sle.posting_date <= %s" % frappe.db.escape(filters.get("to_date"))
	else:
		frappe.throw(_("'To Date' is required"))

	if filters.get("warehouse"):
		warehouse_details = frappe.db.get_value("Warehouse",
			filters.get("warehouse"), ["lft", "rgt"], as_dict=1)
		if warehouse_details:
			conditions += " and exists (select name from `tabWarehouse` wh \
				where wh.lft >= %s and wh.rgt <= %s and sle.warehouse = wh.name)"%(warehouse_details.lft,
				warehouse_details.rgt)

	if filters.get("warehouse_type") and not filters.get("warehouse"):
		conditions += " and exists (select name from `tabWarehouse` wh \
			where wh.warehouse_type = '%s' and sle.warehouse = wh.name)"%(filters.get("warehouse_type"))

	return conditions
	

def get_stock_ledger_entries(filters):
    conditions = get_conditions(filters)
    return frappe.db.sql(
        """
        SELECT sle.item_code, sle.batch_no, sle.warehouse,
        sle.posting_date, SUM(sle.actual_qty) as actual_qty, b.expiry_date
        FROM `tabStock Ledger Entry` sle
        LEFT JOIN `tabBatch` b ON sle.batch_no = b.name
        WHERE sle.docstatus = 1 AND sle.is_cancelled = 0
        AND IFNULL(sle.batch_no, '') != '' %s AND b.expiry_date != ''
        GROUP BY sle.batch_no, sle.item_code, sle.warehouse
        ORDER BY sle.item_code, sle.warehouse, b.expiry_date ASC
        """ % conditions,
        as_dict=1
    )

def get_item_warehouse_batch_map(filters, float_precision):
	sle = get_stock_ledger_entries(filters)
	iwb_map = {}

	from_date = getdate(filters["from_date"])
	to_date = getdate(filters["to_date"])

	for d in sle:
		iwb_map.setdefault(d.item_code, {}).setdefault(d.warehouse, {}).setdefault(
			d.batch_no, frappe._dict({"expires_on": None, "expiry_status": None, "bal_qty": 0.0}))

		qty_dict = iwb_map[d.item_code][d.warehouse][d.batch_no]

		expiry_date_unicode = frappe.db.get_value("Batch", d.batch_no, "expiry_date")
		qty_dict.expires_on = expiry_date_unicode

		exp_date = frappe.utils.data.getdate(expiry_date_unicode)
		qty_dict.expires_on = exp_date

		expires_in_days = (exp_date - frappe.utils.datetime.date.today()).days

		if expires_in_days > 0:
			qty_dict.expiry_status = expires_in_days
		else:
			qty_dict.expiry_status = 0
			
		qty_dict.bal_qty = flt(qty_dict.bal_qty, float_precision) + flt(d.actual_qty, float_precision)

	return iwb_map


def get_item_details(filters):
	item_map = {}
	for d in frappe.db.sql("select name, item_name, brand from tabItem", as_dict=1):
		item_map.setdefault(d.name, d)

	return item_map
