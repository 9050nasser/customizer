from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import date

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
            'label': _('Target'),
            'fieldtype': 'Float',
            'fieldname': 'target',
            'width': 120,
            'default': 0.0,
            'options': 0.0
        },
        # ~ {
            # ~ 'label': _('Vat Zero'),
            # ~ 'fieldtype': 'Currency',
            # ~ 'fieldname': 'vat_zero',
            # ~ 'width': 120,
            # ~ 'default': 0.0,
            # ~ 'options': 0.0
        # ~ },
        # ~ {
            # ~ 'label': _('15% Vat'),
            # ~ 'fieldtype': 'Currency',
            # ~ 'fieldname': 'vat_15',
            # ~ 'width': 120,
            # ~ 'default': 0.0,
            # ~ 'options': 0.0
        # ~ },
        # ~ {
            # ~ 'label': _('Day Sales'),
            # ~ 'fieldtype': 'Currency',
            # ~ 'fieldname': 'day_sales',
            # ~ 'width': 120,
            # ~ 'default': 0.0,
            # ~ 'options': 0.0
        # ~ },
        {
            'label': _('Total MTD'),
            'fieldtype': 'Currency',
            'fieldname': 'total_mtd',
            'width': 120,
            'default': 0.0,
            'options': 0.0
        },
        {
            'label': _('Average Daily Balance'),
            'fieldtype': 'Currency',
            'fieldname': 'average_daily_balance',
            'width': 120,
            'default': 0.0,
            'options': 0.0
        },
        {
            'label': _('Total Balance'),
            'fieldtype': 'Currency',
            'fieldname': 'total_balance',
            'width': 120,
            'default': 0.0,
            'options': 0.0
        },
        {
            'label': _('Achievement'),
            'fieldtype': 'Percent',
            'fieldname': 'achievement',
            'width': 120,
            'default': 0.0,
            'options': 0.0,
            'precision': 2
        },
    ]
    return columns

def get_conditions(filters):
    conditions = ""
    if filters.get("cost_center"):
        conditions += " and  si.cost_center= '{0}' ".format(filters.get("cost_center"))
    if filters.get("from_date"):
        conditions += " and si.posting_date >= '{0}' ".format(filters.get("from_date"))
    if filters.get("to_date"):
        conditions += " and si.posting_date <= '{0}' ".format(filters.get("to_date"))
    return conditions



def get_data(filters):
    data = []
    conditions = get_conditions(filters)
    work_day_balance = filters.get("work_day_balance")

    # Fetch target from POS Profile using SQL query
    target_data = frappe.db.sql("""
        SELECT cost_center, target 
        FROM `tabPOS Profile`
    """, as_dict=True)

    # Create a dictionary to store target values by cost center
    target_map = {row['cost_center']: row['target'] for row in target_data}

    # Calculate the start date of the month
    today = date.today()
    start_date_of_month = date(today.year, today.month, 1)

    # Retrieve data from Sales Invoice and Sales Invoice Item
    invoice_item_query = """
        SELECT si.cost_center AS cost_center,
               SUM(CASE WHEN i.item_tax_template = 'VAT 15%' THEN i.net_amount ELSE 0 END) AS vat_15,
               SUM(CASE WHEN i.item_tax_template = '0%' THEN i.net_amount ELSE 0 END) AS vat_zero
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` i ON si.name = i.parent
        WHERE si.docstatus = 1 AND si.posting_date >= '{start_date}' AND si.posting_date <= '{end_date}' {conditions}
        GROUP BY si.cost_center
    """.format(start_date=start_date_of_month, end_date=today, conditions=conditions)

    invoice_item_data = frappe.db.sql(invoice_item_query, as_dict=True)

    # Process retrieved data
    for row in invoice_item_data:
        cost_center = row.get("cost_center")
        vat_15 = row.get("vat_15", 0)
        vat_zero = row.get("vat_zero", 0)
        target = target_map.get(cost_center, 0)

        # Calculate Day Sales (vat0 + vat15)
        day_sales = vat_zero + vat_15

        # Calculate Total MTD (Month-To-Date)
        total_mtd = vat_zero + vat_15

        # Calculate Total Balance (Main Target - Total MTD)
        total_balance = target - total_mtd

        # Calculate Achievement (Total MTD / Target)
        achievement = (total_mtd / target) * 100 if target != 0 else 0

        # Calculate Average Daily Balance
        average_daily_balance = total_balance / float(work_day_balance)

        # Append calculated data to result
        data.append({
            "cost_center": cost_center,
            "vat_15": vat_15,
            "vat_zero": vat_zero,
            "target": target,
            "day_sales": day_sales,
            "total_mtd": total_mtd,
            "total_balance": total_balance,
            "achievement": achievement,
            "average_daily_balance": average_daily_balance,
        })

    return data






