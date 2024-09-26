# Copyright (c) 2013, Ahmed and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import formatdate, getdate, flt, add_days
from datetime import datetime
import datetime
from datetime import date
from frappe import msgprint, _


def execute(filters=None):
	columns, data = get_columns(filters),get_data(filters)
	return columns, data


def get_columns(filters):
    columns = [
	{
	    'label': _('Cost Center'),
	    'fieldtype': 'Link',
            'fieldname': 'cost_center',
            'width': 200,
            'options':"Cost Center"
	    
        },
              
        {
	    'label': _('Vat Zero'),
	    'fieldtype': 'Currency',
            'fieldname': 'vat_zero',
            'width': 120,
	    'default':0.0,
	    'options':0.0
        },
        
        {
	    'label': _('15% Vat Sales'),
	    'fieldtype': 'Currency',
            'fieldname': 'vat_15',
            'width': 120,
	    'default':0.0,
	    'options':0.0
        
        },
        
        {
	    'label': _('Net Total'),
	    'fieldtype': 'Currency',
            'fieldname': 'net_total',
            'width': 120,
	    'default':0.0,
	    'options':0.0
        
        },
        {
	    'label': _('Vat Amount'),
	    'fieldtype': 'Currency',
            'fieldname': 'vat_amount',
            'width': 120,
	    'default':0.0,
	    'options':0.0
        
       },
       
       {
	    'label': _('Grand Total'),
	    'fieldtype': 'Currency',
            'fieldname': 'grand_total',
            'width': 120,
	    'default':0.0,
	    'options':0.0
        
       },
       # ~ {
	    # ~ 'label': _('Outstanding Amount'),
	    # ~ 'fieldtype': 'Currency',
            # ~ 'fieldname': 'outstanding_amount',
            # ~ 'width': 120,
	    # ~ 'default':0.0,
	    # ~ 'options':0.0
        
       # ~ },
       
    ]
    return columns

def get_conditions(filters):
    conditions = ""
    
    if filters.get("cost_center"):
        conditions += f" and si.cost_center = '{filters['cost_center']}'"
    
    # Apply date filter
    if not filters.get("from_time") and filters.get("from_date"):
        conditions += f" and si.posting_date >= '{filters['from_date']}'"
    if not filters.get("to_time") and filters.get("to_date"):
        conditions += f" and si.posting_date <= '{filters['to_date']}'"

    # Apply datetime filter only if time is provided and corresponding date is also present
    if filters.get("from_time") and filters.get("from_date"):
        conditions += f" and CONCAT(si.posting_date, ' ', si.posting_time) >= '{filters['from_date']} {filters['from_time']}'"

    if filters.get("to_time") and filters.get("to_date"):
        conditions += f" and CONCAT(si.posting_date, ' ', si.posting_time) <= '{filters['to_date']} {filters['to_time']}'"

    return conditions

def get_data(filters):
	data=[]
	conditions= get_conditions(filters)
	li_list = frappe.db.sql(""" select i.item_tax_template as tt ,si.cost_center as cost_center , sum(i.net_amount) as amount,
		sum(si.total_taxes_and_charges) as vat_amount
		from `tabSales Invoice Item`as i join `tabSales Invoice` as si on si.name= i.parent
		where si.docstatus=1 {0} group by item_tax_template, si.cost_center""".format(conditions),as_dict=1) 
	
	q= """ select  si.cost_center  as cost_center,
		sum(si.total_taxes_and_charges) as vat_amount,
		sum(si.grand_total) as grand_total,
		sum(si.net_total) as net_total,
		sum(si.outstanding_amount) as outstanding_amount
		from `tabSales Invoice` as si
		where si.docstatus=1 {0}  group by si.cost_center""".format(conditions)
	print("qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq")
	print(q)
	cost_center_list = frappe.db.sql(q,as_dict=1) 
	
	rescs = []
	data ={}
	for cs in cost_center_list :
	    print("aaaaaaaaaaaaaaaaaaaaaaaaaaa")
	    print("aaaaaaaaaaaaaaaaaaaaaaaaaaa")
	    print(cs.cost_center)
	    rescs.append(cs.cost_center)
	    print("aaaaaaaaaaaaaaaaaaaaaaaaaaa")
	    print("aaaaaaaaaaaaaaaaaaaaaaaaaaa")
	    data[cs.cost_center]= {"cost_center":cs.cost_center
		,"vat_amount":cs.vat_amount
		,"net_total":cs.net_total
		,"grand_total":cs.grand_total
		,"outstanding_amount":cs.outstanding_amount
		}
	
	
	all_cs_data = frappe.get_list("Cost Center",filters= [{"is_group":0},{"disabled":0}, {"not_include_report": 0}])
	all_cs = []
	for c in all_cs_data:
	    if not (c.name in rescs):all_cs.append(c.name)
	print(all_cs)
	
	for c in all_cs : 
	    data[c]= {"cost_center":c
		,"vat_amount":0
		,"net_total":0
		,"grand_total":0
		,"outstanding_amount":0
		}
	
	for i in li_list :
	    vat = "vat_zero"	    
	    if i.tt  == "VAT 15%" :
		    vat = "vat_15"
	    if i.cost_center in data :
		    data[i.cost_center].update( {vat : i.amount})
	    else :
		    data[i.cost_center]={vat : i.amount}
	    



	for row in data:
	    print("vat_zero" in data[row])
	    if not "vat_zero" in data[row] :
		    data[row]["vat_zero"]=0
	    if not "vat_15" in data[row] :
		    data[row]["vat_15"]=0
		    
	return list(data.values())
