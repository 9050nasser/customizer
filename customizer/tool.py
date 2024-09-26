# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import _
from math import ceil
from frappe.utils import  flt, nowdate, add_days, cint ,get_datetime, get_link_to_form, getdate, now, today, nowdate, add_months
import json
from json import dumps, loads
from erpnext.controllers.accounts_controller import (
	validate_taxes_and_charges,
)
from datetime import datetime, timedelta
from frappe.utils import getdate, add_years
from frappe import db
from frappe.utils import add_to_date
import requests



def get_zero_vat():
    poss = frappe.db.sql_list("select name from `tabPOS Closing Voucher` where docstatus=1 ORDER BY name DESC ")
    for pos in poss:
        total_zero_vat_amount = 0
        # if pos=='POS-CLO-2020-00054':
        print('******  '+str(pos)+'  ******')
        doc = frappe.get_doc("POS Closing Voucher", pos)
        for i in range(len(doc.sales_invoices_summary)):
            invoice_name = doc.sales_invoices_summary[i].invoice
            invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
            for l in range(len(invoice_doc.items)):
                if invoice_doc.items[l].item_tax_template=='0%':
                    total_zero_vat_amount = total_zero_vat_amount + invoice_doc.items[l].net_amount
        
        print('.*.*-   '+str(total_zero_vat_amount)+'   -*.*.')
        # ~ doc.total_zero_vat = total_zero_vat_amount
        # ~ doc.save(ignore_permissions=True)
        frappe.db.set_value('POS Closing Voucher',doc.name, 'total_zero_vat', total_zero_vat_amount)
        frappe.db.commit()


def remove_defult_warehouse():
    for item in frappe.get_list('Item'):
        item = frappe.get_doc('Item', item.name)
        print(item.name)
        item.item_defaults = []
        item.flags.ignore_validate = True
        item.save()
        


def so_calculate_taxes_and_totals(doc, method):
    from erpnext.stock.get_item_details import get_item_tax_template
    for item in doc.get("items"):
        if not item.item_tax_template:
            item_code =item.item_code
            out = {}
            item_doc = frappe.get_doc("Item", item_code)
            tax_category = None
            get_item_tax_template({"tax_category": tax_category}, item_doc, out)
            frappe.db.set_value('Sales Order Item',item.name, 'item_tax_template', out["item_tax_template"])
            frappe.db.commit()
            tc = frappe.get_list("Item Tax Template Detail",{"parent":out["item_tax_template"]})
            print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            print({"parent":out["item_tax_template"]})
            print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            if tc:
                for t in tc:
                    tax_doc = frappe.get_doc("Item Tax Template Detail",t)
                    print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
                    print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
                    print({tax_doc.tax_type:tax_doc.tax_rate})
                    print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
                    print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
                    frappe.db.set_value('Sales Order Item',item.name, 'item_tax_rate',str({tax_doc.tax_type:tax_doc.tax_rate}))
                    frappe.db.set_value('Sales Order Item',item.name, 'tax_rate',tax_doc.tax_rate)
                    frappe.db.set_value('Sales Order Item',item.name, 'tax_amount',item.base_net_amount*tax_doc.tax_rate/100.00)

                
        
    doc.calculate_taxes_and_totals()
    

def rewrite_calculate_net_pay(doc, method):
    from erpnext.hr.doctype.salary_slip.salary_slip import SalarySlip
    SalarySlip.calculate_net_pay = calculate_net_pay  

def calculate_net_pay(self):
    from frappe.utils import add_days, cint, cstr, flt, getdate, rounded
    if self.salary_structure and self.get("__islocal"):
        self.calculate_component_amounts("earnings")
    self.gross_pay = self.get_component_totals("earnings")

    if self.salary_structure and self.get("__islocal") :
        self.calculate_component_amounts("deductions")
    self.total_deduction = self.get_component_totals("deductions")

    self.set_loan_repayment()

    self.net_pay = flt(self.gross_pay) - (flt(self.total_deduction) + flt(self.total_loan_repayment))
    self.rounded_total = rounded(self.net_pay)

def validate_pos_return(doc, method):
    from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
    SalesInvoice.validate_pos_return = pos_return_over

def pos_return_over(self):
    if self.is_pos and self.is_return:
        total_amount_in_payments = 0
        for payment in self.payments:
            total_amount_in_payments += payment.amount
        invoice_total = self.rounded_total or self.grand_total
        if self.write_off_amount :
            invoice_total = self.grand_total -self.write_off_amount
            if total_amount_in_payments < invoice_total:
                frappe.throw(_("Total payments amount can't be greater than {0} , Total {1}, Write off {2}"\
                    .format(-self.grand_total--self.write_off_amount,-self.grand_total,-self.write_off_amount)))
            
        if total_amount_in_payments < invoice_total:
            frappe.throw(_("Total payments amount can't be greater than {}".format(-invoice_total)))

def so_calculate_taxes_and_totals_test():
    from erpnext.stock.get_item_details import get_item_tax_template
    item_code ="4002064413143"
    out = {}
    item = frappe.get_doc("Item", item_code)
    tax_category = None
    get_item_tax_template({"tax_category": tax_category}, item, out)
    
    print(out)
    # ~ doc.calculate_taxes_and_totals()
    
    
def validate_write_off_loyality (doc, method):
    if doc.is_return :
        loyalty_amount = frappe.db.get_value('Sales Invoice', {'name': doc.return_against}, 'loyalty_amount')
        if loyalty_amount:
            if int(loyalty_amount) > 0 :
                doc.write_off_amount = -1*loyalty_amount
def validate_max_discount (doc, method):
    if not doc.is_return :
        if doc.pos_coupon_code:
            pricing_rule = frappe.db.get_value('Coupon Code', {'name': doc.pos_coupon_code}, ['pricing_rule'], as_dict=True)
            if pricing_rule:
                print("Hit 1")
                prdoc = frappe.get_doc("Pricing Rule",pricing_rule["pricing_rule"])
                if not doc.additional_discount_percentage :
                    doc.additional_discount_percentage = prdoc.discount_percentage
                
                if doc.additional_discount_percentage :
                    if doc.additional_discount_percentage  != prdoc.discount_percentage:
                        frappe.throw(_("Discount Percentage (% {0} ) not equal to  Cupon (% {1} ) ").format(doc.additional_discount_percentage,prdoc.discount_percentage))
                
                doc.calculate_taxes_and_totals()
                if doc.discount_amount and not doc.pos_coupon_code:
                    if (doc.total*prdoc.discount_percentage / 100.00) != doc.discount_amount : 
                        frappe.throw(_("Discount Amount ( {0} ) not equal to  Cupon ( {1} ) ").format(doc.discount_amount,(doc.total) ))
        
        if not doc.pos_coupon_code and doc.pos_profile   :
            pos_profile = frappe.get_doc("POS Profile",doc.pos_profile)
            max=pos_profile.max_discount
            if doc.additional_discount_percentage:
                if doc.additional_discount_percentage >max:
                    frappe.throw(_("Discount is more than the limit allowed (% {0} )").format(max))
            if pos_profile.max_discount:
                max=pos_profile.max_discount
                for item in doc.get("items"):
                    if item.discount_percentage > max :
                        frappe.throw(_("Discount is more than the limit allowed (% {1} )for item {0}").format(item.item_name,max))
            if doc.discount_amount:
                if (doc.total*max / 100.00) < doc.discount_amount : 
                    frappe.throw(_("Discount Amount ( {0} ) is more than the limit allowed (% {1} )").format(doc.discount_amount,(doc.total*max / 100.00)) )
# ~ def validate_max_discount(doc, method):
    # ~ if not doc.is_return:
        # ~ if doc.pos_coupon_code:
            # ~ pricing_rule = frappe.db.get_value('Coupon Code', {'name': doc.pos_coupon_code}, ['pricing_rule'], as_dict=True)
            # ~ if pricing_rule:
                # ~ print("Hit 1")
                # ~ prdoc = frappe.get_doc("Pricing Rule", pricing_rule["pricing_rule"])
                # ~ if not doc.additional_discount_percentage:
                    # ~ doc.additional_discount_percentage = prdoc.discount_percentage
                
                # ~ if doc.additional_discount_percentage:
                    # ~ if doc.additional_discount_percentage != prdoc.discount_percentage:
                        # ~ frappe.throw(_("Discount Percentage (% {0} ) not equal to Coupon (% {1} ) ").format(
                            # ~ doc.additional_discount_percentage, prdoc.discount_percentage))
                
                # ~ doc.calculate_taxes_and_totals()
                # ~ if doc.discount_amount:
                    # ~ if (doc.total * prdoc.discount_percentage / 100.00) != doc.discount_amount:
    	                    # ~ frappe.throw(_("Discount Amount ( {0} ) not equal to Coupon ( {1} ) ").format(
                            # ~ doc.discount_amount, (doc.total)))
        
        # ~ if not doc.pos_coupon_code and doc.pos_profile:
            # ~ pos_profile = frappe.get_doc("POS Profile", doc.pos_profile)
            # ~ max_discount = pos_profile.max_discount
            # ~ user = frappe.session.user
            # ~ for item in doc.get("items"):
                # ~ if not item.is_free_items:
                    # ~ if item.discount_percentage > max_discount:
                        # ~ frappe.throw(_("Discount is more than the limit allowed (% {0} ) for item {1}").format(
                            # ~ max_discount, item.item_name))
                # ~ elif item.is_free_items and "Casher" not in frappe.get_roles(user):
                    # ~ if item.discount_percentage > max_discount:
                        # ~ frappe.throw(_("Discount is more than the limit allowed (% {0} ) for item {1}").format(
                            # ~ max_discount, item.item_name))
            
            # ~ if doc.discount_amount:
                # ~ if (doc.total * max_discount / 100.00) < doc.discount_amount:
                    # ~ frappe.throw(_("Discount Amount ( {0} ) is more than the limit allowed (% {1} )").format(
                        # ~ doc.discount_amount, (doc.total * max_discount / 100.00)))
                        
def create_sil_for_all():
    ssi_list = frappe.get_all("Sales Invoice", filters={"docstatus": 1},fields=["name"], order_by= 'creation asc')
    index = len(ssi_list)
    arraw = index
    for si in ssi_list:
        print(str(arraw)+" out of " +str(index))
        arraw -= 1
        sil = frappe.new_doc("Sales Invoice Log")
        sil.sales_invoice = si.name
        sil.insert(ignore_permissions=True)
        frappe.db.sql("update `tabSales Invoice` set sales_invoice_id='{1}' where name='{0}'".format(si.name,sil.name))
        frappe.db.commit()
    return ssi_list
    
def create_sil(doc,method):
    sil = frappe.new_doc("Sales Invoice Log")
    sil.sales_invoice = doc.name
    sil.insert(ignore_permissions=True)
    doc.sales_invoice_id = sil.name
    frappe.db.sql("update `tabSales Invoice` set sales_invoice_id='{1}' where name='{0}'".format(doc.name,sil.name))
    frappe.db.commit()


#validate pos and outstanding
def validate_pos_outstanding(doc, method):
	if doc.is_pos and doc.outstanding_amount and int(doc.outstanding_amount) > 0:
		frappe.throw(_("Not Allowed, Outstanding Remaining is {} ").format(doc.outstanding_amount))
		
  
    
def validate_returen_role(doc,method):
    user = frappe.session.user
    if not  ("Return Supervisor" in frappe.get_roles(user)) and doc.is_return:
        frappe.throw("Only Return Supervisor can submit the invoice")

def validate_cancel_date(doc,method):
    from frappe.utils import add_days
    from datetime import date
    user = frappe.session.user
    if add_days(doc.posting_date, 10) < date.today() and not  ("Accounts Manager" in frappe.get_roles(user)):
        frappe.throw("Can not cancel invoice Older than 10 days")

#def validate_rate(doc,method):
#	for item in doc.get("items"):
#		if item.rate <= 0 :
#			frappe.throw(_("Rate is not positive ( {1} )for item {0}").format(item.item_code,item.rate))

def validate_pos_profile (doc, method):
    if doc.pos_profile and doc.is_pos:
        pos_profile = frappe.get_doc("POS Profile",doc.pos_profile)
        users = []
        for user in pos_profile.get("applicable_for_users"):
            users.append(user.user)
        if frappe.session.user not in users :
            frappe.throw(_("User {0} is not Part of {1} POS profile ,Contact System Administrator.").format(frappe.session.user,doc.pos_profile))

def validate_batch (doc, method):
    if doc.pos_profile and doc.is_pos:
        pos_profile = frappe.get_doc("POS Profile",doc.pos_profile)
        auto_select_batch = pos_profile.auto_select_batch
        free_batch = pos_profile.free_batch
        item_batches = []
        delete_item_batches = set()
        for item in doc.get("items"):
            has_batch_no = frappe.db.get_value("Item", {"name": item.item_code}, "has_batch_no")
            if has_batch_no ==1  and auto_select_batch and not item.calculated:
                batchs_list = get_batches(item.item_code, item.warehouse, free_batch)
                if not batchs_list:
                    frappe.throw("No Batch found for "+item.item_code+" the Wrehouse "+item.warehouse)

                    
                total_qty = 0
                for b in batchs_list:
                    if b["qty"] >0:
                    	total_qty += b["qty"]
                        
                        
                rem = item.qty
                if total_qty <item.qty:
                    frappe.throw("Not enagh qty for item "+item.item_code+" requsted : "+str(item.qty)+" Avilable : "+str(total_qty))

                    
                x =0
                for b in batchs_list:
                    print(b)
                print ("iiiiiiiiiiiiiiiiiiiiQTYiiiiiiiiiiiiiiiiiiiiiiiiiiii")
                print (rem)
                print ("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
                # ~ for batch in batchs_list :
                for i in range (0,len(batchs_list)) :
                    if i == 0 :
                        item.batch_no= batchs_list[i]["batch_id"]
                    if rem <=0:
                        break
                    if  batchs_list[i]["qty"] >0:
                        if batchs_list[i]["qty"] > rem  :
                            item_batches.append({"batch_no":batchs_list[i]["batch_id"],"qty":rem,"batch_qty":batchs_list[i]["qty"],"item":item})
                            
                            
                            print ("iiiiiiiiiiiiiiiiiiii111111iiiiiiiiiiiiiiiiiiiiiiiiiiii")
                            print (i)
                            print (rem)
                            print (batchs_list[i]["qty"])
                            print (batchs_list[i]["batch_id"])
                            print ("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
                            rem=0
                            delete_item_batches.add(item)
                            
                        else :
                            item_batches.append({"batch_no":batchs_list[i]["batch_id"],"qty":batchs_list[i]["qty"],"batch_qty":batchs_list[i]["qty"],"item":item})
                           
                            print ("iiiiiiiiiiiiiiiiiiiiii2222iiiiiiiiiiiiiiiiiiiiiiiiii")
                            print (i)
                            print (rem)
                            print (rem-batchs_list[i]["qty"])
                            print (batchs_list[i]["qty"])
                            print (batchs_list[i]["batch_id"])
                            print ("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
                            
                            rem -= batchs_list[i]["qty"]
                            delete_item_batches.add(item)
        
        for batch_info in item_batches :
            item =batch_info["item"]
            new_item = doc.append("items",
                {
                "doctype": "Sales Invoice Item",
                "__islocal": 1,
                "__unsaved": 1,
                "calculated": 1,
                "stock_uom": item.stock_uom,
                "is_free_item": item.is_free_item,
                "delivered_by_supplier": item.delivered_by_supplier,
                "is_fixed_asset": item.is_fixed_asset,
                "enable_deferred_revenue": item.enable_deferred_revenue,
                "allow_zero_valuation_rate": item.allow_zero_valuation_rate,
                "cost_center": item.cost_center,
                "parent": item.parent,
                "parentfield": "items",
                "parenttype": "Sales Invoice",
                "idx": 1,
                "item_code":item.item_code,
                "barcode": item.barcode,
                "item_name": item.item_name,
                "description": item.description,
                "image": item.image,
                "warehouse": item.warehouse,
                "income_account": item.income_account,
                "expense_account": item.expense_account,
                "has_batch_no": item.get("has_batch_no"),
                "batch_no": batch_info["batch_no"],
                "uom": item.uom,
                "qty":batch_info["qty"],
                "stock_qty": batch_info["qty"],
                "price_list_rate": item.price_list_rate,
                "base_price_list_rate": item.base_price_list_rate,
                "rate": item.rate,
                "base_rate": item.base_rate,
                "amount": item.amount,
                "base_amount": item.base_amount,
                "net_rate": item.net_rate,
                "net_amount": item.net_amount,
                "discount_percentage": item.discount_percentage,
                "supplier": item.get("supplier"),
                "update_stock": item.get("update_stock"),
                "weight_per_unit": item.weight_per_unit,
                "weight_uom": item.weight_uom,
                "last_purchase_rate": item.get("last_purchase_rate"),
                "transaction_date": item.get("transaction_date"),
                "conversion_factor": item.conversion_factor,
                "item_group": item.item_group,
                "barcodes": [],
                "brand": item.brand,
                "manufacturer": item.get("manufacturer"),
                "manufacturer_part_no": item.get("manufacturer_part_no"),
                "item_tax_template": item.item_tax_template,
                "item_tax_rate": item.item_tax_rate,
                "customer_item_code": item.customer_item_code,
                "valuation_rate": item.get("valuation_rate"),
                "actual_qty": item.actual_qty,
                "projected_qty": item.get("projected_qty"),
                "reserved_qty": item.get("reserved_qty"),
                "child_docname": item.child_docname,
                "discount_percentage_on_rate":item.discount_percentage_on_rate,
                "discount_amount_on_rate": item.discount_amount_on_rate,
                "actual_batch_qty": batch_info["batch_qty"],
                "total_weight": item.total_weight,
                "tax_rate": item.tax_rate,
                "tax_amount": item.tax_amount,
                "total_amount": item.total_amount,
                "margin_rate_or_amount": item.margin_rate_or_amount,
                "rate_with_margin": item.rate_with_margin,
                "discount_amount": item.discount_amount,
                "base_rate_with_margin": item.base_rate_with_margin,
                "base_net_rate": item.base_net_rate,
                "base_net_amount": item.base_net_amount,
                "delivered_qty": item.delivered_qty,
                "serial_no": item.serial_no,
                })
        
        
        for d in delete_item_batches:
            doc.remove(d)
                
        
                
                    
        for item in doc.get("items"):
            print (item.batch_no)
            print (item.qty)
        doc.calculate_taxes_and_totals()

                    
        
                        
                
                    
                
                
        
def get_batches(item_code, warehouse, free_batch=True, throw=False):
    from datetime import date,datetime
    cond = ''
    q ="""
        select batch_id, sum(`tabStock Ledger Entry`.actual_qty) as qty
        from `tabBatch`
			join `tabStock Ledger Entry` ignore index (item_code, warehouse)
				on (`tabBatch`.batch_id = `tabStock Ledger Entry`.batch_no )
		where `tabStock Ledger Entry`.item_code = %s and `tabStock Ledger Entry`.warehouse = %s
			and (`tabBatch`.expiry_date >= CURDATE() or `tabBatch`.expiry_date IS NULL) {0}
		group by batch_id
		{1}
	"""
    order_by = """order by `tabBatch`.expiry_date ASC,`tabBatch`.free_batch Desc ,`tabBatch`.manufacturing_date ASC, `tabBatch`.creation ASC"""
    if not free_batch :
        order_by = """order by `tabBatch`.expiry_date ASC,`tabBatch`.free_batch ASC ,`tabBatch`.manufacturing_date ASC, `tabBatch`.creation ASC"""
        # ~ cond += "and `tabBatch`.free_batch = 0"
    
    batches = frappe.db.sql(q.format(cond,order_by), (item_code, warehouse), as_dict=True)
    for b in batches :
        if b.qty<0 :  
            print(b)      
            previous_sle = get_previous_sle({
                        "item_code": item_code,
                        "warehouse": warehouse,
                        "posting_date": date.today(),
                        "batch_no": b.batch_id,
                        "posting_time": "23:00"
                    })
            print ("zzzzzzzzzzzzzzzZ")
            print (previous_sle)
            b.qty = previous_sle.qty_after_transaction
    return batches


def get_warehouses():
    frappe.db.sql("update `tabStock Ledger Entry` set batch_no='{0}' where item_code='{1}'".format(name+"-batch",name))

   
   
def get_previous_sle(args, for_update=False):
    args["name"] = args.get("sle", None) or "" 
    print(args)
    sle = get_stock_ledger_entries(args, "<=", "desc", "limit 1", for_update=for_update)
    print (sle)
    if sle:
        return sle[0]
    return {}

def get_stock_ledger_entries(previous_sle, operator=None,
    order="desc", limit=None, for_update=False, debug=False, check_serial_no=True):
    """get stock ledger entries filtered by specific posting datetime conditions"""
    conditions = " and timestamp(posting_date, posting_time) {0} timestamp(%(posting_date)s, %(posting_time)s)".format(operator)
    if previous_sle.get("batch_no"):
        conditions += " and batch_no = %(batch_no)s"
    if previous_sle.get("warehouse"):
        conditions += " and warehouse = %(warehouse)s"
    elif previous_sle.get("warehouse_condition"):
        conditions += " and " + previous_sle.get("warehouse_condition")
    if check_serial_no and previous_sle.get("serial_no"):
        conditions += " and serial_no like {}".format(frappe.db.escape('%{0}%'.format(previous_sle.get("serial_no"))))
    if not previous_sle.get("posting_date"):
        previous_sle["posting_date"] = "1900-01-01"
    if not previous_sle.get("posting_time"):
        previous_sle["posting_time"] = "00:00"
    if operator in (">", "<=") and previous_sle.get("name"):
        conditions += " and name!=%(name)s"
    print(conditions)
    q = """select *, timestamp(posting_date, posting_time) as "timestamp" from `tabStock Ledger Entry`
        where item_code = %%(item_code)s
        and ifnull(is_cancelled, 'No')='No'
        %(conditions)s
        order by timestamp(posting_date, posting_time) %(order)s, creation %(order)s
        %(limit)s %(for_update)s""" % {
            "conditions": conditions,
            "limit": limit or "",
            "for_update": for_update and "for update" or "",
            "order": order
        }
    print(q)
    return frappe.db.sql(q, previous_sle, as_dict=1, debug=debug)
       

def get_batches1():
    from datetime import date,datetime
    cond = ''
    item_code ="7531824361426"
    warehouse = "مخزن فرع الخبر - P"
    free_batch = True
    q ="""
        select batch_id,sum(`tabStock Ledger Entry`.actual_qty) as qty,`tabBatch`.expiry_date 
        from `tabBatch`
			join `tabStock Ledger Entry` ignore index (item_code, warehouse)
				on (`tabBatch`.batch_id = `tabStock Ledger Entry`.batch_no )
		where `tabStock Ledger Entry`.item_code = %s and `tabStock Ledger Entry`.warehouse = %s
			and (`tabBatch`.expiry_date >= CURDATE() or `tabBatch`.expiry_date IS NULL) {0}
		group by batch_id
		{1}
	"""
    order_by = """order by `tabBatch`.expiry_date ASC,`tabBatch`.manufacturing_date ASC, `tabBatch`.creation ASC"""
    if not free_batch :
        cond += "and `tabBatch`.free_batch = 0"
        

    # ~ batches = frappe.db.sql(q.format(cond,order_by), (item_code, warehouse), as_dict=True)
    # ~ for b in batches :
        # ~ if b.qty<0 :  
            # ~ print(b)      
            # ~ previous_sle = get_previous_sle({
                        # ~ "item_code": item_code,
                        # ~ "warehouse": warehouse,
                        # ~ "posting_date": date.today(),
                        # ~ "batch_no": b.batch_id,
                        # ~ "posting_time": "00:00"
                    # ~ })
            # ~ print ("zzzzzzzzzzzzzzzZ")
            # ~ print (previous_sle)
            # ~ b.qty = previous_sle.qty_after_transaction
    # ~ return previous_sle.qty_after_transaction
            # ~ doc = frappe.get_doc("Stock Ledger Entry",previous_sle.name)
            # ~ new_sle = frappe.copy_doc(doc)
            # ~ from pprint import pprint
            # ~ pprint(vars(new_sle))
            # ~ new_sle.actual_qty = (b.qty*-1) + new_sle.qty_after_transaction
            # ~ new_sle.posting_date = date.today()
            # ~ new_sle.posting_time = "12:00"
            # ~ new_sle.warehouse = warehouse
            # ~ print(new_sle.warehouse)
            # ~ new_sle.insert(ignore_permissions=True)
            # ~ frappe.db.commit()
            
    # ~ return new_sle
    
    # ~ from erpnext.stock.stock_ledger import get_previous_sle
    # ~ from datetime import date,datetime
    # ~ return new_sle
    # ~ res =  frappe.db.sql("select distinct warehouse from `tabStock Ledger Entry` where  batch_no='{0}' and item_code='{1}'".format("8009632039718-batch",item_code),as_list=1)
    # ~ print (res)
    
    # ~ for r in res :
        # ~ previous_sle = get_previous_sle({
                        # ~ "item_code": item_code,
                        # ~ "warehouse": r[0],
                        # ~ "posting_date": date.today(),
                        # ~ "posting_time": "12:00"
                    # ~ })

        # ~ doc = frappe.get_doc("Stock Ledger Entry",previous_sle.name)
        # ~ new_sle = frappe.copy_doc(doc)
        # ~ from pprint import pprint
        # ~ pprint(vars(new_sle))
        # ~ new_sle.actual_qty = new_sle.qty_after_transaction
        # ~ new_sle.posting_date = date.today()
        # ~ new_sle.posting_time = "12:00"
        # ~ new_sle.warehouse = r[0]
        # ~ print(new_sle.warehouse)
        # ~ new_sle.insert(ignore_permissions=True)
        # ~ frappe.db.commit()
    
    # ~ print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    # ~ print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    # ~ print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    # ~ print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    return frappe.db.sql(q.format(cond,order_by), (item_code, warehouse), as_dict=True)
    # ~ return batches


def get_batches12(free_batch=True, throw=False):
    from customizer.tool import get_previous_sle
    from datetime import date,datetime
    item_code ="067714103014"
    warehouse = "مخزن فرع الخبر - P"
    cond = ''
    q ="""
        select batch_id, sum(`tabStock Ledger Entry`.actual_qty) as qty
        from `tabBatch`
			join `tabStock Ledger Entry` ignore index (item_code, warehouse)
				on (`tabBatch`.batch_id = `tabStock Ledger Entry`.batch_no )
		where `tabStock Ledger Entry`.item_code = %s and `tabStock Ledger Entry`.warehouse = %s
			and (`tabBatch`.expiry_date >= CURDATE() or `tabBatch`.expiry_date IS NULL) {0}
		group by batch_id
		{1}
	"""
    order_by = """order by `tabBatch`.expiry_date ASC,`tabBatch`.free_batch Desc ,`tabBatch`.manufacturing_date ASC, `tabBatch`.creation ASC"""
    if not free_batch :
        order_by = """order by `tabBatch`.expiry_date ASC,`tabBatch`.free_batch ASC ,`tabBatch`.manufacturing_date ASC, `tabBatch`.creation ASC"""
        # ~ cond += "and `tabBatch`.free_batch = 0"
    
    batches = frappe.db.sql(q.format(cond,order_by), (item_code, warehouse), as_dict=True)
    for b in batches :
        if b.qty<=0 :  
            print(b)      
            previous_sle = get_previous_sle({
                        "item_code": item_code,
                        "warehouse": warehouse,
                        "posting_date": date.today(),
                        "batch_no": b.batch_id,
                        "posting_time": "23:00"
                    })
            print ("zzzzzzzzzzzzzzzZ")
            print (previous_sle)
            doc = frappe.get_doc("Stock Ledger Entry",previous_sle.name)
            new_sle = frappe.copy_doc(doc)
            from pprint import pprint
            pprint(vars(new_sle))
            if new_sle.qty_after_transaction >0:
                new_sle.actual_qty = (b.qty*-1) + new_sle.qty_after_transaction
                new_sle.posting_date = date.today()
                new_sle.posting_time = "12:00"
                new_sle.warehouse = warehouse
                print(new_sle.warehouse)
                new_sle.insert(ignore_permissions=True)
                frappe.db.commit()
            
 
def validate_pos_profile_cost_center (doc, method):
    if doc.pos_profile and doc.is_pos:
        pos_profile = frappe.get_doc("POS Profile",doc.pos_profile)
        if pos_profile.cost_center :
            for item in doc.get("items"):
                item.cost_center = pos_profile.cost_center

def validate_return(doc, method):
    from erpnext.stock.utils import get_stock_balance 

    if doc.is_return and not doc.return_against:
        for item in doc.get("items"):
            data = get_stock_balance(item.item_code, item.warehouse, doc.posting_date, doc.posting_time,
                with_valuation_rate=True, with_serial_no= False )
            qty, rate = data
            
            if rate <= 0 :
                rate = frappe.db.get_value("Item", item.item_code,'valuation_rate')
            if rate <= 0 :
                frappe.throw("Zero Hit "+item.item_code)
            item.rate = rate
        doc.calculate_taxes_and_totals()

def validate_sales_person(doc, method):
    if doc.sales_person and doc.is_pos and doc.sales_person_hit == 0:
        sales_person_doc = frappe.get_doc("Sales Person",doc.sales_person )
        child = frappe.new_doc("Sales Team")
        child.parent = doc.name
        child.parenttype = "Sales Invoice"
        child.sales_person = doc.sales_person
        child.allocated_percentage = 100.00
        child.commission_rate = flt(sales_person_doc.commission_rate,2)
        child.allocated_amount = flt(doc.base_net_total * child.allocated_percentage / 100.0,2)
        child.incentives = flt(child.allocated_amount * child.commission_rate / 100.0,2)
        doc.sales_team.append(child)
        doc.sales_person_hit =1
        
            
def validate_qty (doc, method):
    for item in doc.get("items"):
        item.qty = float(item.qty)  
            


def assign_item_supplier():
    item_list = frappe.get_list ("Item")
    for item in item_list :
        doc=frappe.get_doc("Item",item)
        print (doc.name)
        if doc.supplier_old_system_id :
            supplier =frappe.get_doc("Supplier",{"old_system_id":doc.supplier_old_system_id})
            doc.supplier_items = []
            doc.flags.ignore_validate = True
            child =doc.append("supplier_items",{})
            child.supplier = supplier.name
            doc.save()
            frappe.db.commit()



def read_excel():
    import io
    from frappe.utils.xlsxutils import (
        read_xlsx_file_from_attached_file,
        read_xls_file_from_attached_file,)
    file_path = "/home/frappe/frappe-bench/data/a.xlsx"
    extn = file_path.split(".")[1]
    file_content = None
    with io.open(file_path, mode="rb") as f:
        file_content = f.read()
    data = read_xlsx_file_from_attached_file(fcontent=file_content)
    for d in data:
        try: doc = frappe.get_doc("Item",d[0])
        except:print(d[0])


def add_items():
    from frappe.utils.csvutils import read_csv_content
    from frappe.core.doctype.data_import.importer import upload
    with open("/home/frappe/frappe-bench/apps/customizer/customizer/المعارض/main_warehouse1.csv", "r") as infile:
        rows = read_csv_content(infile.read())
        items =[]
        i = 0
        for index, row in enumerate(rows):
            frappe.db.commit()
            # print (row[0])
            if row[0] and int(row[2]) >= 0 :
                if frappe.db.exists("Item", {"name": row[0]}):
                    doc_item = frappe.get_doc("Item", row[0])
                    items_row = {"doctype": "Stock Reconciliation Item","item_code":row[0],"warehouse": "عيادة لاتيرا - P","qty": row[2],"valuation_rate": doc_item.valuation_rate}
                    items.append(items_row)
                else:
                    print("Item Not Found "+row[0])
        # ss_doc = frappe.get_doc({
        # "doctype":"Stock Reconciliation",
        # "purpose":"Opening Stock",
        # "posting_date":"2020-04-01",
        # "items":items,
        # "expense_account":"1910 - افتتاحي مؤقت - P"
        # })
        # # ss_doc.flags.ignore_validate = True
        # ss_doc.flags.ignore_permissions = True
        # ss_doc.insert()


        print ('*************')

def remove_dupplicate_entry():
    import pandas as pd
    df = pd.read_csv('/home/frappe/frappe-bench/apps/customizer/customizer/العيادات/latira_old.csv', dtype={'code':str})
    df1 = df.groupby(['code'])['qty'].agg(['sum'])
    # df1 = df.groupby(['code','name'])['qty'].sum()
    print(df1)
    df2 = pd.DataFrame()
    cols = ['code']
    for col in cols:
        df2[col] = list(df1['sum'].index.get_level_values(col))
    df2['qty'] = df1['sum'].values
    # df2['code']= df['code'].astype('str')
    df2.to_csv('/home/frappe/frappe-bench/apps/customizer/customizer/latira_new.csv',index = False)


def upload_chart_of_accounts():
    from frappe.utils.csvutils import read_csv_content
    path = frappe.get_app_path("customizer")
    path += "/csv/coa.csv"
    with open(path, "r") as infile:
        rows = read_csv_content(infile.read())
        for index, row in enumerate(rows):
            # print(row[3])
            if not frappe.db.exists("Account", row[0]+" - "+ " - P"):
                acc = frappe.new_doc("Account")
                acc.account_name = row[1]
                acc.parent_account = frappe.get_value("Account", {"account_number": row[4]}, "name")
                acc.account_number = row[0]
                acc.is_group = 1 if row[2] == "0" else 0
                acc.company = "Pets-Oasis"
                # acc.root_type = row[4]
                # acc.root_type = row[5]
                acc.insert()
                # frappe.db.commit()
                print(row[0])



def read_excel_account():
    import io
    from datetime import datetime

    from frappe.utils.xlsxutils import (
        read_xlsx_file_from_attached_file,
        read_xls_file_from_attached_file,)
    file_path = "/home/frappe/frappe-bench/data/b.xlsx"
    extn = file_path.split(".")[1]
    file_content = None
    with io.open(file_path, mode="rb") as f:
        file_content = f.read()
    data = read_xlsx_file_from_attached_file(fcontent=file_content)
    master_name = ""
    # ~ for d in data:
        # ~ if master_name == "":
            # ~ master_name = d[3]
        # ~ try : 

            # ~ if not frappe.db.get_value("Old JV Data", {"journal_dtl_code": d[0]}, 'name'):
                # ~ jv_data = frappe.new_doc("Old JV Data")
                # ~ jv_data.journal_dtl_code = str(d[0])
                # ~ print("add "+str(d[1]))
                # ~ jv_data.journal_dtl_date =str( datetime.strptime(str(d[1])[:19], '%Y-%m-%d %H:%M:%S'))
                # ~ jv_data.journal_dtl_date = str(d[1])
                # ~ jv_data.journal_mstr_year =str( d[2])
                # ~ jv_data.journal_mstr_code = str(d[3])
                # ~ jv_data.account_code = str(d[4])
                # ~ jv_data.journal_dtl_desc = d[5]
                # ~ jv_data.journal_debit = flt(d[6])
                # ~ jv_data.journal_credit = flt(d[7])
                # ~ jv_data.created_on =str( datetime.strptime(str(d[9])[:19], '%Y-%m-%d %H:%M:%S'))
                # ~ jv_data.save()
                # ~ print("add "+str(d[0]))
            # ~ else:
                # ~ print("hit "+str(d[0]))

        # ~ except Exception as e: 
            # ~ print("error")
            # ~ print(e)
            # ~ print(d[4])
            # ~ print("\r")
            
    years =["2011","2012","2013","2014","2015","2016","2017","2018","2019","2020"]
    
    for year in years:
    
        all_old_jv = frappe.db.sql("""select distinct journal_mstr_code from `tabOld JV Data` where journal_mstr_year ={0} """.format(year))
        # ~ all_old_jv = [("474")]
        for d  in all_old_jv:
            # ~ print ("this")
            # ~ print (d[0])
            old_list = frappe.get_list("Old JV Data",{"journal_mstr_code":d[0],"journal_mstr_year":year} )
            
            
            je = frappe.new_doc("Journal Entry")
            je.is_opening = "No"
            je.voucher_type = "Journal Entry"
            je.company = "Pets-Oasis"
            je.old_jv = d[0]
            
            try:
                if old_list:
                    for a in old_list:
                        doc = frappe.get_doc("Old JV Data",{"name":a["name"]})
                        if not je.posting_date : 
                             je.posting_date = doc.journal_dtl_date.date()
                        account = frappe.get_value("Account", {"account_number": str('{:,}'.format(int(doc.account_code)))}, "name")
                        # ~ print(doc.journal_dtl_date.date())
                        if not account:
                            print ("Bad Account")
                            print (doc.account_code)
                        # ~ print(str('{:,}'.format(int(doc.account_code))))
                        # ~ print(account)
                        # ~ print(account)
                        # ~ print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
                        if account:
                            je.append("accounts", 
                                {"account": account,
                                "credit_in_account_currency": doc.journal_credit,
                                "credit": doc.journal_credit,
                                "debit_in_account_currency": doc.journal_debit,
                                "debit": doc.journal_debit,
                                "user_remark": (doc.journal_dtl_desc),
                                })
                
                # ~ for acc in je.get("accounts"):
                    # ~ print(acc.credit_in_account_currency)
                    # ~ print("\r")
                # ~ print("Debits")
                # ~ for acc in je.get("accounts"):
                    # ~ print(acc.debit_in_account_currency)
                    # ~ print("\r")
                je.save()
                print("hit "+str(d[0]))
                print(je.name)
                print("\r")
                frappe.db.commit()

            except Exception as e: 
                print("error")
                print(a)
                print("\r")
                print("\r")
                # ~ print("\r")


def read_excel_item_batch():
    import io
    from datetime import datetime

    from frappe.utils.xlsxutils import (
        read_xlsx_file_from_attached_file,
        read_xls_file_from_attached_file,)
    file_path = "/home/frappe/frappe-bench/data/i1.xlsx"
    extn = file_path.split(".")[1]
    file_content = None
    with io.open(file_path, mode="rb") as f:
        file_content = f.read()
    data = read_xlsx_file_from_attached_file(fcontent=file_content)
    i =0
    for d in data:
        name =""
        try :
            name =""
            item_name =None
            try:
                name = str(int(d[0]))
                item_name = frappe.db.get_value("Item", {"name": name}, "name")
            except Exception as e: 
                name = str(d[0])
                item_name = frappe.db.get_value("Item", {"name": name}, "name")
                
                
            if item_name:
                frappe.db.sql("update `tabItem` set has_batch_no=1 where name='{0}'".format(name))
                frappe.db.commit()
                
                #check for default batch 
                batch_list = frappe.db.get_list("Batch",{'name':name+"-batch"})
                if not batch_list:
                    batch = frappe.new_doc("Batch")
                    batch.batch_id = name+"-batch"
                    batch.item = name
                    batch.save()
                
                frappe.db.sql("update `tabStock Ledger Entry` set batch_no='{0}' where item_code='{1}'".format(name+"-batch",name))
                frappe.db.commit()  
            else :
                temp = "0"+name
                item_name = frappe.db.get_value("Item", {"name": temp}, "name")
                if item_name:
                    frappe.db.sql("update `tabItem` set has_batch_no=1 where name='{0}'".format(temp))
                    frappe.db.commit()
                    
                    #check for default batch 
                    batch_list = frappe.db.get_list("Batch",{'name':temp+"-batch"})
                    if not batch_list:
                        batch = frappe.new_doc("Batch")
                        batch.batch_id = temp+"-batch"
                        batch.item = temp
                        batch.save()
                    
                    frappe.db.sql("update `tabStock Ledger Entry` set batch_no='{0}' where item_code='{1}'".format(temp+"-batch",temp))
                    frappe.db.commit() 
                else :
                    i+=1
                    print (name)

        except Exception as e: 
            print("error")
            print(e)
            i+=1
            print(name)
    print("Bad Items : "+str(i))
        # ~ item_name = frappe.get_value("Item", {"name": d[0]}, "name")
        # ~ if item_name:
            # ~ print("hit1")
            # ~ frappe.db.sql("update `tabItem` set has_batch_no=1 where name='{0}'".format(name))
            # ~ frappe.db.commit()
            
            # ~ #check for default batch 
            # ~ batch_list = frappe.db.get_list("Batch",{'name':name+"-batch"})
            # ~ if not batch_list:
                # ~ batch = frappe.new_doc("Batch")
                # ~ batch.batch_id = name+"-batch"
                # ~ batch.item = name
                # ~ batch.save()
            
            # ~ frappe.db.sql("update `tabStock Ledger Entry` set batch_no='{0}' where item_code='{1}'".format(name+"-batch",name))
            # ~ frappe.db.commit()  
        # ~ else :
            # ~ print("hit2")
            # ~ print (str(d[0]))

def djvs():
    i=0
    for item in frappe.get_list('Journal Entry'):
        item = frappe.get_doc('Journal Entry', item.name)
        i+=1
        print (i)
        print(" - "+item.name)
        item.delete()
        print("delet")
        
def submjvs():
    i=0
    for item in frappe.get_list('Journal Entry',{'docstatus':0}):
        item = frappe.get_doc('Journal Entry', item.name)
        if item.docstatus != 1:
            i+=1
            print (i)
            print(" - "+item.name)
            item.submit()
            print("submit")
            frappe.db.commit()


def edit_is_batch_to_not():
    # ~ doc = frappe.get_doc("Item", name)
    # ~ doc.has_batch_no = 1
    # ~ doc.save()
    frappe.db.sql("update `tabItem` set has_batch_no=0 where name in ('701029101777','5400274730132')")
    frappe.db.commit()
    
    frappe.db.sql("update `tabStock Ledger Entry` set batch_no='' where item_code in ('701029101777','5400274730132')")
    frappe.db.commit()    
    
        
    
    return 'True'

def update_account_number():
    from erpnext.accounts.doctype.account.account import update_account_number
    account_list = frappe.get_list("Account")
    for account in account_list :
        doc = frappe.get_doc("Account",account)
        if doc.account_number:
            print(doc.account_number.replace(',','') )
            update_account_number(doc.name, doc.account_name, doc.account_number.replace(',','') )
            
def rebicate_price_list():
    import copy
    for price in frappe.get_list('Item Price',{'price_list':"White Friday"}):
        item= frappe.get_doc("Item Price",price)
        item.delete()
        frappe.db.commit()
    i = 1
    for price in frappe.get_list('Item Price',{'price_list':"Standard Selling"}):
        item= frappe.get_doc("Item Price",price)
        i+=1

        try :
            new_item = copy.deepcopy(item)
            new_item.name = ""
            new_item.price_list = "White Friday"
            new_item.save()
            frappe.db.commit()
            print(i)
            print(item.name)
        except Exception as e: 
            print("error")
            print(e)


        
def add_quantity_differance_in_stock_entry():
    se_list = frappe.get_list("Stock Ledger Entry",filters={'voucher_type':"Stock Reconciliation"})
    i = len(se_list)
    for se in se_list :
        print(len(se_list))
        print(i)
        i-=1
        
        print(se["name"])
        doc = frappe.get_doc("Stock Ledger Entry",se["name"])
        quantity_difference = flt(frappe.db.get_value("Stock Reconciliation Item",doc.voucher_detail_no,"quantity_difference"))
        item = flt(frappe.db.get_value("Stock Reconciliation Item",doc.voucher_detail_no,"item_code"))
        print(item)
        print(quantity_difference)
        frappe.db.set_value('Stock Ledger Entry',doc.name, 'quantity_difference', quantity_difference)
       
        frappe.db.commit()



def create_qr_code(doc, method=None):
    import io
    import os
    from base64 import b64encode

    import frappe
    from frappe import _
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    from frappe.utils.data import add_to_date, get_time, getdate
    from pyqrcode import create as qr_create
    from erpnext import get_region

    # ~ if not hasattr(doc, 'ksa_einv_qr'):
        # ~ create_custom_fields({
            # ~ doc.doctype: [
                # ~ dict(
                    # ~ fieldname='ksa_einv_qr',
                    # ~ label='KSA E-Invoicing QR',
                    # ~ fieldtype='Attach Image',
                    # ~ read_only=1, no_copy=1, hidden=1
                # ~ )
            # ~ ]
        # ~ })

    # Don't create QR Code if it already exists
    qr_code = doc.get("ksa_einv_qr")
    if qr_code and frappe.db.exists({"doctype": "File", "file_url": qr_code}):
        return

    meta = frappe.get_meta(doc.doctype)

    if "ksa_einv_qr" in [d.fieldname for d in meta.get_image_fields()]:
        ''' TLV conversion for
        1. Seller's Name
        2. VAT Number
        3. Time Stamp
        4. Invoice Amount
        5. VAT Amount
        '''
        tlv_array = []
        # Sellers Name

        seller_name = frappe.db.get_value(
            'Company',
            doc.company,
            'name')

        if not seller_name:
            frappe.throw(_('Arabic name missing for {} in the company document').format(doc.company))

        tag = bytes([1]).hex()
        length = bytes([len(seller_name.encode('utf-8'))]).hex()
        value = seller_name.encode('utf-8').hex()
        tlv_array.append(''.join([tag, length, value]))

        # VAT Number
        tax_id = frappe.db.get_value('Company', doc.company, 'tax_id')
        if not tax_id:
            frappe.throw(_('Tax ID missing for {} in the company document').format(doc.company))

        tag = bytes([2]).hex()
        length = bytes([len(tax_id)]).hex()
        value = tax_id.encode('utf-8').hex()
        tlv_array.append(''.join([tag, length, value]))

        # Time Stamp
        posting_date = getdate(doc.posting_date)
        time = get_time(doc.posting_time)
        seconds = time.hour * 60 * 60 + time.minute * 60 + time.second
        time_stamp = add_to_date(posting_date, seconds=seconds)
        time_stamp = time_stamp.strftime('%Y-%m-%dT%H:%M:%SZ')

        tag = bytes([3]).hex()
        length = bytes([len(time_stamp)]).hex()
        value = time_stamp.encode('utf-8').hex()
        tlv_array.append(''.join([tag, length, value]))

        # Invoice Amount
        invoice_amount = str(doc.grand_total)
        tag = bytes([4]).hex()
        length = bytes([len(invoice_amount)]).hex()
        value = invoice_amount.encode('utf-8').hex()
        tlv_array.append(''.join([tag, length, value]))

        # VAT Amount
        vat_amount = str(doc.total_taxes_and_charges)

        tag = bytes([5]).hex()
        length = bytes([len(vat_amount)]).hex()
        value = vat_amount.encode('utf-8').hex()
        tlv_array.append(''.join([tag, length, value]))

        # Joining bytes into one
        tlv_buff = ''.join(tlv_array)

        # base64 conversion for QR Code
        base64_string = b64encode(bytes.fromhex(tlv_buff)).decode()

        qr_image = io.BytesIO()
        url = qr_create(base64_string, error='L')
        url.png(qr_image, scale=2, quiet_zone=1)

        name = frappe.generate_hash(doc.name, 5)

        # making file
        filename = f"QRCode-{name}.png".replace(os.path.sep, "__")
        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "is_private": 0,
            "content": qr_image.getvalue(),
            "attached_to_doctype": doc.get("doctype"),
            "attached_to_name": doc.get("name"),
            "attached_to_field": "ksa_einv_qr"
        })

        _file.save()

        # assigning to document
        doc.db_set('ksa_einv_qr', _file.file_url)
        doc.notify_update()


def update_wallet(doc,method =None):
    parent_doc = frappe.get_doc("Wallet",doc.parent)
    parent_doc.save(ignore_permissions=True)


def before_4_month(doc, method= None):
	from frappe.utils import add_to_date
	doc.before_4_month = add_to_date(doc.expiry_date, days= -120)
	
def before_1_month(doc, method=None):
	from frappe.utils import add_to_date
	doc.before_1_month = add_to_date(doc.expiry_date, days=-30)
	
	
def validate_warehouse_supervise(doc, method=None):
    user = frappe.session.user 
    if not ("Stock Manager" in frappe.get_roles(user) or "System Manager" in frappe.get_roles(user)):
        if  not (doc.from_warehouse_supervise == frappe.session.user or doc.to_warehouse_supervise == frappe.session.user) and doc.stock_entry_type == "Material Transfer"  and  doc.workflow_state == "Pending for Approval":
            frappe.throw(_("Not Allowed"))

def validate_item_tax_template(doc, method=None):
    for i in doc.get("items"):
        item_tax_list = frappe.get_list("Item Tax",fields=["item_tax_template"], filters={"parent": i.item_code})
        if item_tax_list:
            for it in item_tax_list : 
                if i.item_tax_template != it.item_tax_template:
                    frappe.throw(_("Invalid Item Tax Template for Item"))
        item_group_tax_list = frappe.get_list("Item Tax",fields=["item_tax_template"], filters={"parent": i.item_group})
        if item_group_tax_list :
            for it in item_group_tax_list :
                if i.item_tax_template != it.item_tax_template:
                    frappe.throw(_("Row {0}: Invalid Item Tax Template for item {1} Please Check Item Tax ").format(
							i.idx, frappe.bold(i.item_code)
					))

@frappe.whitelist(allow_guest=True)
def on_insert_item(doc, method):
    return
    import requests
    import json
    
    if isinstance(doc, str):
        doc = frappe.get_doc('Item', doc)
    
    url = "https://petoasisksa.com/wp-json/wcm/api/login"

    payload = json.dumps({
      "username": "app",
      "password": "app@app@123"
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    #print(response.json()["cookie"])
    try : cookie = response.json()["cookie"]
    except: cookie = ""
    url = "https://petoasisksa.com/wp-json/wcm/api/product/add"

    payload = json.dumps({
      "name": doc.item_name,
      "sku": doc.item_code,
      "status": "private",
      "type": "simple",
      "price": str(doc.standard_rate),
      "regular_price": str(doc.standard_rate),
      "sale_price":  str(doc.standard_rate),
      "description": doc.description,
      "short_description": doc.description[:50],
      "manage_stock": "1",
      "categories": [
        {
          "name": doc.item_group
        }
      ],
      "brand": [
        {
          "name": doc.brand
        }
      ]
    })

    print(payload)
    headers = {
      'cookie': cookie,
      'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


# ~ def val_warehouse(doc, method):
    # ~ old_value = frappe.db.get_value("Bin", doc.name, "actual_qty")
    # ~ if doc.actual_qty == 0 or old_value == 0:
        # ~ import requests
        # ~ import json
        # ~ total = frappe.db.sql("SELECT SUM(actual_qty) FROM tabBin WHERE item_code = %s", doc.item_code)[0][0]
        # ~ if  old_value == 0 :
            # ~ total += doc.actual_qty 

        # ~ url = "https://petoasisksa.com/wp-json/wcm/api/login"

        # ~ payload = json.dumps({
            # ~ "username": "app",
            # ~ "password": "app@app@123"
        # ~ })
        # ~ headers = {
            # ~ 'Content-Type': 'application/json'
        # ~ }

        # ~ response = requests.request("POST", url, headers=headers, data=payload)
        # ~ print(response.json()["cookie"])
        # ~ cookie = response.json()["cookie"]
        # ~ url = "https://petoasisksa.com/wp-json/wcm/api/product/add/warehouses"

        # ~ payload = json.dumps({
            # ~ "warehouses": {
                # ~ doc.item_code: [
                    # ~ {
                        # ~ "name": doc.warehouse,
                        # ~ "total_qty": total
                    # ~ }
                # ~ ]
            # ~ }
        # ~ })
        # ~ print(payload)
        # ~ headers = {
            # ~ 'cookie': cookie,
            # ~ 'Content-Type': 'application/json'
        # ~ }

        # ~ response = requests.request("POST", url, headers=headers, data=payload)

        # ~ print(response.text)

def validate_warehouse_for_auto_reorder(doc, method=None):
		warehouse = []
		for d in doc.get("item_auto_reorder"):
			if not d.warehouse_group:
				d.warehouse_group = d.warehouse
			if d.get("warehouse") and d.get("warehouse") not in warehouse:
				warehouse += [d.get("warehouse")]
			else:
				frappe.throw(_("Row {0}: An Reorder entry already exists for this warehouse {1}").format(d.idx, d.warehouse))

			if d.warehouse_reorder_level and not d.warehouse_reorder_qty:
				frappe.throw(_("Row #{0}: Please set reorder quantity").format(d.idx))
				
def validate_auto_reorder_enabled_in_stock_settings(doc, method=None):
		if doc.item_auto_reorder:
			enabled = frappe.db.get_single_value('Stock Settings', 'auto_indent')
			if not enabled:
				frappe.msgprint(msg=_("You have to enable auto re-order in Stock Settings to maintain re-order levels."), title=_("Enable Auto Re-Order"), indicator="orange")

	
def update_template_tables(doc, method=None):
		template = frappe.get_doc("Item", doc.variant_of)

		for d in template.get("taxes"):
			doc.append("taxes", {"item_tax_template": d.item_tax_template})
		if not doc.get("item_auto_reorder"):
			for d in template.get("item_auto_reorder"):
				n = {}
				for k in ("warehouse", "warehouse_reorder_level",
					"warehouse_reorder_qty", "material_request_type"):
					n[k] = d.get(k)
				doc.append("item_auto_reorder", n)
			

def set_is_free_items(doc, method=None):
    if doc.is_pos:
        free_item_codes = frappe.get_all(
            'Free Items',
            filters={'item_code': ['in', [item.item_code for item in doc.items]], 'enabled': 1},
            fields=['item_code', 'is_free_items']
        )

        free_item_dict = {item.item_code: item.is_free_items for item in free_item_codes}

        for item in doc.get("items"):
            item.is_free_items = free_item_dict.get(item.item_code, 0)


def update_contract_end_dates():
    employees = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "date_of_joining", "contract_end_date"])
    
    for employee in employees:
        date_of_joining = employee.date_of_joining
        current_year = datetime.now().year
        contract_end_date = datetime(current_year, date_of_joining.month, date_of_joining.day).date()

        if contract_end_date < datetime.now().date():
            current_year += 1
            contract_end_date = datetime(current_year, date_of_joining.month, date_of_joining.day).date()

        frappe.db.set_value("Employee", employee.name, "contract_end_date", contract_end_date)

        # Calculate and set contract_end_before_3_month
        three_months_before = add_to_date(contract_end_date, days=-90)
        frappe.db.set_value("Employee", employee.name, "contract_end_before_3_month", three_months_before)
		
        # Calculate and set contract_end_before_2_month
        two_month_before = add_to_date(contract_end_date, days=-80)
        frappe.db.set_value("Employee", employee.name, "contract_end_before_2_month", two_month_before)
        
    

def clear_contract_end_fields(doc, method=None):
    if doc.status == "Left":
        doc.contract_end_date = None
        doc.contract_end_before_3_month = None
        doc.contract_end_before_2_month = None



def validate_eid(doc, method=None):
	eid_discount_items = ["SG00","SG01","SG02","SG03","SG04","SG05","SG06"]
	for item in doc.items:
		if item.item_code in eid_discount_items:
			item.is_eid_discount = 1
		else:
			item.is_eid_discount = 0
		
		
	



