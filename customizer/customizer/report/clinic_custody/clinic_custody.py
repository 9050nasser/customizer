# Copyright (c) 2013, Ahmed and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _


def execute(filters=None):
    columns=get_columns(filters)
    data = get_data(filters)
    for d  in data  :
        d["commission_rate"] =0
        d["commission"] =0
        d["commission_tax"] =0
        d["is_return"]=0
        if d["mada"]  != "none":
            if  d["mada"] == "more":
                d["commission_rate"] = 40
                d["commission"] = 40*d["sc"]
                d["commission_tax"] = 0.15*d["commission"]
            if d["mada"] == "less":
                d["commission_rate"] = 0.006
                d["commission"] = 0.006*d["collected_amount"]
                d["commission_tax"] = 0.15*d["commission"]
            if d["mada"] == "return":
                d["is_return"]= d["collected_amount"]
                d["commission_rate"] = 0
                d["commission"] = 0*d["collected_amount"]
                d["commission_tax"] = 0*d["commission"]
                d["collected_amount"] = 0
        for pe in ("master","Master","visa","Visa") :
            if pe in str(d["mode_of_payment"]):
                d["commission_rate"] = 0.02
                d["commission"] = 0.02*d["collected_amount"]
                d["commission_tax"] = 0.15*d["commission"]
	

    return columns, data
    


def get_columns(filters):
    columns = [
        {
            'label': _('Mode of Payment'),
            'fieldtype': 'Data',
            'fieldname': 'mode_of_payment',
            'width': 200,

        }
        , 
        {
            'label': _('Collected Amount'),
            'fieldtype': 'Currency',
            'fieldname': 'collected_amount',
            'width': 200,
        }
        , 
       
        {
            'label': _('SI Return '),
            'fieldtype': 'Float',
            'fieldname': 'is_return',
            "default":0.0,
            'options':0.0,
            'width': 150,
        }
        ,
        {
            'label': _('Sales Invoice Count'),
            'fieldtype': 'Float',
            'fieldname': 'sc',
            "default":0.0,
            'options':0.0,
            'width': 150,
        }
        
    
    ]
    return columns

def get_conditions(filters):
    conditions = ""

    if filters.get("cost_center"): conditions += " and si.cost_center= '{0}' ".format(filters.get("cost_center"))
    if filters.get("pos_profile"): conditions += " and si.pos_profile= '{0}' ".format(filters.get("pos_profile"))
    if filters.get("from_date"): conditions += " and si.posting_date>='{0}' ".format(filters.get("from_date"))
    if filters.get("to_date"): conditions += " and si.posting_date<='{0}' ".format(filters.get("to_date"))


    return conditions


def get_data(filters):
    data=[]
    conditions = get_conditions(filters)
    li_list = frappe.db.sql("""select p.mode_of_payment as  mode_of_payment , abs(sum(p.amount)) as collected_amount ,"none" as mada, count(si.name) as sc from `tabSales Invoice Payment` 
    as p join `tabSales Invoice` as si 
    on si.name =p.parent 
    where si.docstatus =1 and si.is_return = 0 and p.mode_of_payment not like "%Mada%" {0} and p.mode_of_payment not like "%master ecommerce%" {0}  and p.mode_of_payment not like "%Mada ecommerc%" {0}
    group by p.mode_of_payment""".format(conditions),as_dict=1)
     
    li_list_is_return = frappe.db.sql("""select CONCAT(p.mode_of_payment," -Is Return") as  mode_of_payment, abs(sum(p.amount)) as collected_amount  ,"return" as mada, count(si.name) as sc from `tabSales Invoice Payment` 
    as p join `tabSales Invoice` as si 
    on si.name =p.parent 
    where si.docstatus =1 and si.is_return =1 and p.mode_of_payment not like "%master ecommerce%" {0} and p.mode_of_payment not like "%Mada ecommerc%" {0}
    group by p.mode_of_payment """.format(conditions),as_dict=1)
       
    mada_list_more_than5000 = frappe.db.sql("""select CONCAT(p.mode_of_payment,"-More than 5000") as  mode_of_payment ,  abs(sum(p.amount)) as collected_amount ,"more" as mada, count(si.name) as sc from `tabSales Invoice Payment` 
    as p join `tabSales Invoice` as si 
    on si.name =p.parent 
    where si.docstatus =1  and p.mode_of_payment like "%Mada%" and p.mode_of_payment not like "%master ecommerce%" {0} and p.mode_of_payment not like "%Mada ecommerc%" {0}
    and p.amount >= 5000{0}  group by p.mode_of_payment""".format(conditions),as_dict=1)
    
    mada_list_less_than5000 = frappe.db.sql("""select CONCAT(p.mode_of_payment,"-Less than 5000") as  mode_of_payment , abs(sum(p.amount)) as collected_amount ,
    "less" as mada ,count(si.name) as sc
    from `tabSales Invoice Payment` 
    as p join `tabSales Invoice` as si 
    on si.name =p.parent 
    where si.docstatus =1 and si.is_return =0 and p.mode_of_payment like "%Mada%" and p.mode_of_payment not like "%master ecommerce%" {0} and p.mode_of_payment not like "%Mada ecommerc%" {0}
     and p.amount <= 4999{0}  group by p.mode_of_payment""".format(conditions),as_dict=1)
    
    pe_list = frappe.db.sql("""select pe.mode_of_payment as  mode_of_payment , abs(sum(per.allocated_amount)) as collected_amount ,"none" as mada, count(si.name) as sc   from `tabPayment Entry` 
    as pe , `tabSales Invoice` as si ,`tabPayment Entry Reference` as per 
    where  per.reference_name = si.name and per.parent = pe.name 
    and pe.mode_of_payment not like "%Mada%" and pe.mode_of_payment not like "%master ecommerce%" {0} and pe.mode_of_payment not like "%Mada ecommerc%" {0} and pe.mode_of_payment not like "%Mada ecommerc%" {0}
    and si.status ="Paid" and si.is_return =0  and si.docstatus =1 {0}   group by pe.mode_of_payment""".format(conditions),as_dict=1)
    
    pe_list_more_than5000 = frappe.db.sql("""select CONCAT(pe.mode_of_payment,"-More than 5000-PE") as  mode_of_payment , abs(sum(si.grand_total)) as collected_amount ,"more" as mada, count(si.name) as sc  from `tabPayment Entry` 
    as pe , `tabSales Invoice` as si ,`tabPayment Entry Reference` as per 
    where  per.reference_name = si.name and per.parent = pe.name 
    and pe.mode_of_payment  like "%Mada%" and pe.mode_of_payment not like "%master ecommerce%" {0} and pe.mode_of_payment not like "%Mada ecommerc%" {0}
    and si.status ="Paid" and si.docstatus =1 and si.is_return =0   and si.grand_total > 5000 {0}  group by pe.mode_of_payment""".format(conditions),as_dict=1)
    
    
    pe_list_less_than5000 = frappe.db.sql("""select CONCAT(pe.mode_of_payment,"-Less than 5000-PE") as  mode_of_payment , abs(sum(per.allocated_amount)) as collected_amount ,
    "less" as mada ,count(si.name) as sc
    from `tabPayment Entry`as pe , 
    `tabSales Invoice` as si ,`tabPayment Entry Reference` as per 
    where  per.reference_name = si.name and per.parent = pe.name 
    and pe.mode_of_payment not like "%Mada%"  and pe.mode_of_payment not like "%master ecommerce%" {0} and pe.mode_of_payment not like "%Mada ecommerc%" {0}
    and si.status ="Paid" and si.docstatus =1 and si.is_return =0   and si.grand_total <= 5000 {0}  group by pe.mode_of_payment""".format(conditions),as_dict=1)
    
    
    data=[*li_list,*li_list_is_return, *pe_list,*mada_list_more_than5000,*mada_list_less_than5000,*pe_list_more_than5000,*pe_list_less_than5000]
    
    return data
