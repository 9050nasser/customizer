# encoding: utf-8
# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import formatdate, getdate, flt, add_days
from datetime import datetime
import datetime
from frappe.utils import cint, cstr, flt, nowdate, comma_and, date_diff, time_diff, getdate, get_datetime, get_time
from frappe import msgprint, _
from datetime import date


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    
    mode_list =get_mods(filters)
    tax_list = get_tax(filters)
    
    add_mode_of_payment_columns(columns,mode_list)
    mode_of_payment_zero_values(data,mode_list)
    add_mode_of_payment_data(data)
    
    add_tax_columns(columns,tax_list)
    tax_zero_values(data,tax_list)
    add_tax_data(data)
    return columns, data

    
def mode_of_payment_zero_values(data,mode_list):
    for d in data:
        for mod in mode_list:
            d[mod.mode_of_payment] = 0

def add_mode_of_payment_data(data):
    for d in data:
        doc = frappe.get_doc("POS Closing Voucher", d.name)
        for i in doc.payment_reconciliation:
            d[i.mode_of_payment] = i.collected_amount
    
    
def add_mode_of_payment_columns(columns,mode_list):
    for mode in mode_list :
       columns.append({
            'label': _(mode.mode_of_payment),
            'fieldtype': 'Currency',
            'fieldname': mode.mode_of_payment,
            'default': 0,
            'width': 100,
            }) 
    
def tax_zero_values(data,tax_list):
    for d in data:
        for tax in tax_list:
            d['tax_'+str(tax.rate)] = 1

def add_tax_data(data):
    for d in data:
        doc = frappe.get_doc("POS Closing Voucher", d.name)
        for i in doc.taxes:
            d['tax_'+str(i.rate)] = i.amount
    
    
def add_tax_columns(columns,tax_list):
    for tax in tax_list :
        columns.append({
            'label': _(tax.rate),
            'fieldtype': 'Currency',
            'fieldname': 'tax_'+str(tax.rate),
            'default': 0,
            'width': 100,
            }) 
    
def get_mods(filters):
    conditions = get_conditions(filters)
    mode_list = frappe.db.sql("""select distinct mode_of_payment from `tabPOS Closing Voucher Details` where parent in (select name from `tabPOS Closing Voucher`
        where docstatus = 1 {0} )""".format(conditions),as_dict=1)
    return mode_list

def get_tax(filters):
    conditions = get_conditions(filters)
    tax_list = frappe.db.sql("""select distinct rate from `tabPOS Closing Voucher Taxes` where parent in (select name from `tabPOS Closing Voucher`
        where docstatus = 1 {0} )""".format(conditions),as_dict=1)
    return tax_list
    
def get_columns(filters):
    columns = [
        {
            'label': _('POS Closing Voucher'),
            'fieldtype': 'Link',
            'fieldname': 'name',
            'width': 200,
            'options': 'POS Closing Voucher'
        }
        ,
        {
            'label': _('POS Profile'),
            'fieldtype': 'Link',
            'fieldname': 'pos_profile',
            'width': 100,
            'options': 'POS Profile'
        }
        , 
        {
            'label': _('Period Start Date'),
            'fieldtype': 'Date',
            'fieldname': 'period_start_date',
            'width': 100,
        }
        , 
        {
            'label': _('Period End Date'),
            'fieldtype': 'Date',
            'fieldname': 'period_end_date',
            'width': 100,
        }
        ,
        {
            'label': _('Grand Total'),
            'fieldtype': 'Currency',
            'fieldname': 'grand_total',
            'width': 100,
        }
        , 
        {
            'label': _('Net Total'),
            'fieldtype': 'Currency',
            'fieldname': 'net_total',
            'width': 100,
        }
        , 
        {
            'label': _('Total Zero Vat'),
            'fieldtype': 'Currency',
            'fieldname': 'total_zero_vat',
            'width': 100,
        }
    
    ]
    return columns
    

def get_conditions(filters):
    conditions = ""

    if filters.get("cost_center"):
        conditions += " and pos_profile in (select name from `tabPOS Profile` where cost_center = '{0}')".format(filters.get("cost_center"))
    if filters.get("pos_profile"): conditions += " and pos_profile= '{0}' ".format(filters.get("pos_profile"))
    if filters.get("cashier"): conditions += " and user= '{0}' ".format(filters.get("cashier"))
    if filters.get("from_date"): conditions += " and posting_date>='{0}' ".format(filters.get("from_date"))
    if filters.get("to_date"): conditions += " and posting_date<='{0}' ".format(filters.get("to_date"))


    return conditions


def get_data(filters):
    data=[]
    
    conditions = get_conditions(filters)
    q = """select name,period_start_date,period_end_date, pos_profile, grand_total, net_total, total_zero_vat from `tabPOS Closing Voucher`
        where docstatus = 1 {0} """.format(conditions)
    frappe.msgprint(q)
    li_list = frappe.db.sql(q,as_dict=1)
    return li_list
