from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import formatdate, getdate, flt, add_days
from datetime import datetime, timedelta
from frappe import msgprint, _

def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {
            'label': _('Cost Center'),
            'fieldtype': 'Link',
            'fieldname': 'cost_center',
            'width': 200,
            'options': "Cost Center"
        },
        {
            'label': _('Net Total'),
            'fieldtype': 'Currency',
            'fieldname': 'net_total',
            'width': 120,
            'default': 0.0,
            'options': 0.0
        }
    ]

    start_date = getdate(filters.get('from_date'))
    end_date = getdate(filters.get('to_date'))
    delta = timedelta(days=1)

    while start_date <= end_date:
        columns.append({
            'label': formatdate(start_date),
            'fieldtype': 'Currency',
            'fieldname': start_date.strftime('%Y-%m-%d'),
            'width': 120,
            'default': 0.0,
            'options': 0.0
        })
        start_date += delta

    return columns

def get_conditions(filters):
    conditions = ""
    if filters.get("cost_center"): 
        conditions += " and si.cost_center= '{0}' ".format(filters.get("cost_center"))
    if filters.get("from_date"): 
        conditions += " and si.posting_date>='{0}' ".format(filters.get("from_date"))
    if filters.get("to_date"): 
        conditions += " and si.posting_date<='{0}' ".format(filters.get("to_date"))
 
    return conditions

def get_data(filters):
    data = []
    conditions = get_conditions(filters)
    query = """
        select 
            si.posting_date as posting_date,
            si.cost_center as cost_center,
            sum(si.net_total) as net_total
        from 
            `tabSales Invoice` as si
        where 
            si.docstatus=1 {0}  
        group by 
            si.posting_date, si.cost_center
    """.format(conditions)
    
    sales_data = frappe.db.sql(query, as_dict=1)
    
    cost_center_data = {}
    
    for entry in sales_data:
        cost_center = entry.cost_center
        posting_date = entry.posting_date.strftime('%Y-%m-%d')
        net_total = entry.net_total
        
        if cost_center not in cost_center_data:
            cost_center_data[cost_center] = {'cost_center': cost_center, 'net_total': 0.0}
        
        cost_center_data[cost_center][posting_date] = net_total
        cost_center_data[cost_center]['net_total'] += net_total  # Add to total net amount
    
    # Filling missing dates with 0.0
    start_date = getdate(filters.get('from_date'))
    end_date = getdate(filters.get('to_date'))
    delta = timedelta(days=1)
    
    while start_date <= end_date:
        date_str = start_date.strftime('%Y-%m-%d')
        for cost_center in cost_center_data:
            if date_str not in cost_center_data[cost_center]:
                cost_center_data[cost_center][date_str] = 0.0
        start_date += delta
    
    data = list(cost_center_data.values())
    
    return data

