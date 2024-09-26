# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import frappe
import erpnext
from frappe.utils import flt, nowdate, add_days, cint
from frappe import _
from datetime import date

@frappe.whitelist()
def reorder_item(doc, method):
	""" Reorder item if stock reaches reorder level"""
	# if initial setup not completed, return
	if not (frappe.db.a_row_exists("Company") and frappe.db.a_row_exists("Fiscal Year")):
		return

	if cint(frappe.db.get_value('Stock Settings', None, 'auto_indent')):
		return _reorder_item(doc.item_code)
		
def reorder_item1():
	doc = frappe.get_doc("Item", "V051")
	""" Reorder item if stock reaches reorder level"""
	# if initial setup not completed, return
	if not (frappe.db.a_row_exists("Company") and frappe.db.a_row_exists("Fiscal Year")):
		return 1111

	if cint(frappe.db.get_value('Stock Settings', None, 'auto_indent')):
		return _reorder_item(doc.item_code)
		
		
def _reorder_item(item_code):
	material_requests = {"Purchase": {}, "Transfer": {}, "Material Issue": {}, "Manufacture": {}}
	warehouse_company = frappe._dict(frappe.db.sql("""select name, company from `tabWarehouse`
		where disabled=0"""))
	default_company = (erpnext.get_default_company() or
		frappe.db.sql("""select name from tabCompany limit 1""")[0][0])

	items_to_consider = frappe.db.sql_list("""select name, brand from `tabItem` item
		where is_stock_item=1 and has_variants=0
			and disabled=0
			and item.item_code = %(item_code)s 
			and (end_of_life is null or end_of_life='0000-00-00' or end_of_life > %(today)s)
			and (exists (select name from `tabItem Auto Reorder` ir where ir.parent=item.name)
				or (variant_of is not null and variant_of != ''
				and exists (select name from `tabItem Auto Reorder` ir where ir.parent=item.variant_of))
			)""",
		{"today": nowdate(), "item_code": item_code})

	if not items_to_consider:
		return 222
	item_warehouse_projected_qty = get_item_warehouse_projected_qty(items_to_consider)
	return item_warehouse_projected_qty
	
	def add_to_material_request(item_code, warehouse, reorder_level, reorder_qty, material_request_type, warehouse_group=None):
		if warehouse not in warehouse_company:
			# a disabled warehouse
			return

		reorder_level = flt(reorder_level)
		reorder_qty = flt(reorder_qty)

		# projected_qty will be 0 if Bin does not exist
		if warehouse_group:
			projected_qty = flt(item_warehouse_projected_qty.get(item_code, {}).get(warehouse_group))
		else:
			projected_qty = flt(item_warehouse_projected_qty.get(item_code, {}).get(warehouse))

		if (reorder_level or reorder_qty) and projected_qty < reorder_level:
			deficiency = reorder_level - projected_qty
			if deficiency > reorder_qty:
				reorder_qty = deficiency

			company = warehouse_company.get(warehouse) or default_company

			material_requests[material_request_type].setdefault(company, []).append({
				"item_code": item_code,
				"warehouse": warehouse,
				"reorder_qty": reorder_qty
			})

	for item_code in items_to_consider:
		item = frappe.get_doc("Item", item_code)

		if item.variant_of and not item.get("item_auto_reorder"):
			item.update_template_tables()

		if item.get("item_auto_reorder"):
			for d in item.get("item_auto_reorder"):
				add_to_material_request(item_code, d.warehouse, d.warehouse_reorder_level,
					d.warehouse_reorder_qty, d.material_request_type, warehouse_group=d.warehouse_group)

	if material_requests:
		return create_material_request(material_requests)

def get_item_warehouse_projected_qty(items_to_consider):
	item_warehouse_projected_qty = {}

	for item_code, warehouse, projected_qty in frappe.db.sql("""select item_code, warehouse, projected_qty
		from tabBin where item_code in ({0})
			and (warehouse != "" and warehouse is not null)"""\
		.format(", ".join(["%s"] * len(items_to_consider))), items_to_consider):

		if item_code not in item_warehouse_projected_qty:
			item_warehouse_projected_qty.setdefault(item_code, {})

		if warehouse not in item_warehouse_projected_qty.get(item_code):
			item_warehouse_projected_qty[item_code][warehouse] = flt(projected_qty)

		warehouse_doc = frappe.get_doc("Warehouse", warehouse)

		while warehouse_doc.parent_warehouse:
			if not item_warehouse_projected_qty.get(item_code, {}).get(warehouse_doc.parent_warehouse):
				item_warehouse_projected_qty.setdefault(item_code, {})[warehouse_doc.parent_warehouse] = flt(projected_qty)
			else:
				item_warehouse_projected_qty[item_code][warehouse_doc.parent_warehouse] += flt(projected_qty)
			warehouse_doc = frappe.get_doc("Warehouse", warehouse_doc.parent_warehouse)

	return item_warehouse_projected_qty
		

def create_material_request(material_requests=None):
    if material_requests is None:
        material_request_type = "Purchase"
        material_requests = {
            material_request_type: {
                frappe.defaults.get_user_default("company"): []
            }
        }
        
        # Get list of items with reorder qty from item and item auto reorder child table 
        items = frappe.db.sql("""
            SELECT DISTINCT
                i.item_code,
                iar.warehouse,
                iar.warehouse_reorder_level,
                iar.warehouse_reorder_qty
            FROM
                `tabItem` i
            INNER JOIN
                `tabItem Auto Reorder` iar ON i.name = iar.parent
            WHERE
                iar.warehouse_reorder_qty > 0
        """, as_dict=True)
        
        # Add items to material requests
        for item in items:
            material_requests[material_request_type][frappe.defaults.get_user_default("company")].append({
                "item_code": item.item_code,
                "warehouse": item.warehouse,
                "reorder_qty": item.warehouse_reorder_qty
            })

    mr_list = []
    exceptions_list = []

    def _log_exception():
        if frappe.local.message_log:
            exceptions_list.extend(frappe.local.message_log)
            frappe.local.message_log = []
        else:
            exceptions_list.append(frappe.get_traceback())

        frappe.log_error(frappe.get_traceback())

    for request_type in material_requests:
        for company in material_requests[request_type]:
            try:
                items = material_requests[request_type][company]
                if not items:
                    continue
                
                # Separate warehouses 
                warehouses = set([d["warehouse"] for d in items])

                for warehouse in warehouses:
                    warehouse_items = [d for d in items if d["warehouse"] == warehouse]

                    mr = frappe.new_doc("Material Request")
                    mr.update({
                        "company": company,
                        "transaction_date": nowdate(),
                        "material_request_type": "Material Transfer" if request_type == "Transfer" else request_type
                    })
					
                    for d in warehouse_items:
                        d = frappe._dict(d)
                        item = frappe.get_doc("Item", d.item_code)
                        uom = item.stock_uom
                        conversion_factor = 1.0

                        if request_type == "Purchase":
                            uom = item.purchase_uom or item.stock_uom
                            if uom != item.stock_uom:
                                conversion_factor = frappe.db.get_value("UOM Conversion Detail",
                                    {"parent": item.name, "uom": uom}, "conversion_factor") or 1.0
                        mr.append("items", {
                            "doctype": "Material Request Item",
                            "item_code": d.item_code,
							"schedule_date": add_days(nowdate(), 3),  
                            "qty": d.reorder_qty / conversion_factor,
                            "uom": uom,
                            "stock_uom": item.stock_uom,
                            "warehouse": d.warehouse,
                            "item_name": item.item_name,
                            "description": item.description,
                            "item_group": item.item_group,
                            "brand": item.brand,
                        })

                    schedule_dates = [d.schedule_date for d in mr.items]
                    mr.schedule_date = max(schedule_dates or [nowdate()])
                    mr.flags.ignore_mandatory = True
                    mr.insert()
                    mr.submit()
                    mr_list.append(mr)

            except:
                _log_exception()

    if mr_list:
        if getattr(frappe.local, "reorder_email_notify", None) is None:
            frappe.local.reorder_email_notify = cint(frappe.db.get_value("Stock Settings", None,
                "reorder_email_notify"))

        if frappe.local.reorder_email_notify:
            send_email_notification(mr_list)

    return mr_list

def send_email_notification(mr_list=None):
	""" Notify user about auto creation of indent"""
	if mr_list is None:
		mr_list = []

	email_list = frappe.db.sql_list("""select distinct r.parent
		from `tabHas Role` r, tabUser p
		where p.name = r.parent and p.enabled = 1 and p.docstatus < 2
		and r.role in ('Branch Manager','Branch Manager')
		and p.name not in ('Administrator', 'All', 'Guest')""")

	msg = frappe.render_template("templates/emails/reorder_item.html", {
		"mr_list": mr_list
	})

	frappe.sendmail(recipients=email_list,
		subject=_('Auto Material Requests Generated'), message = msg)
		
