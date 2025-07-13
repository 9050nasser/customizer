from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, flt
from datetime import datetime, timedelta
import calendar

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
            'width': 120
        }
    ]

    # Define month columns from Jan to Dec
    months = [
        ('Jan', '01'), ('Feb', '02'), ('Mar', '03'), ('Apr', '04'),
        ('May', '05'), ('Jun', '06'), ('Jul', '07'), ('Aug', '08'),
        ('Sep', '09'), ('Oct', '10'), ('Nov', '11'), ('Dec', '12')
    ]

    for month_name, month_num in months:
        columns.append({
            'label': month_name,
            'fieldtype': 'Currency',
            'fieldname': month_num,
            'width': 120
        })

    return columns

def get_conditions(filters):
    conditions = []
    params = {}

    # Check if the cost_center filter is passed and add to conditions
    if filters.get("cost_center"): 
        conditions.append("si.cost_center = %(cost_center)s")
        params["cost_center"] = filters.get("cost_center")

    # Check if from_date and to_date are provided
    from_date = getdate(filters.get("from_date")) if filters.get("from_date") else None
    to_date = getdate(filters.get("to_date")) if filters.get("to_date") else None
    
    if from_date and to_date:
        conditions.append("si.posting_date BETWEEN %(from_date)s AND %(to_date)s")
        params["from_date"] = filters.get("from_date")
        params["to_date"] = filters.get("to_date")

        # Get previous month date range with the same days
        def shift_to_previous_month(date):
            prev_month = date.month - 1 if date.month > 1 else 12
            prev_year = date.year if date.month > 1 else date.year - 1
            
            # Handle cases where the previous month doesn't have the same day
            last_day_prev_month = calendar.monthrange(prev_year, prev_month)[1]
            new_day = min(date.day, last_day_prev_month)
            
            return date.replace(year=prev_year, month=prev_month, day=new_day)

        previous_month_start = shift_to_previous_month(from_date)
        previous_month_end = shift_to_previous_month(to_date)

        conditions.append("si.posting_date BETWEEN %(previous_month_start)s AND %(previous_month_end)s")
        params["previous_month_start"] = previous_month_start
        params["previous_month_end"] = previous_month_end

    return " AND ".join(conditions), params



def get_data(filters):
    conditions, params = get_conditions(filters)
    from_date = getdate(filters.get("from_date")) if filters.get("from_date") else None
    to_date = getdate(filters.get("to_date")) if filters.get("to_date") else None
    
    if not from_date or not to_date:
        return []

    # Determine the number of days to consider per month
    total_days = (to_date - from_date).days + 1
    
    # Calculate the previous month (i.e., the month before the 'from_date')
    previous_month = (from_date.replace(day=1) - timedelta(days=1)).strftime('%m')

    # Prepare the query
    query = f"""
        SELECT 
            DATE_FORMAT(si.posting_date, '%%Y-%%m') AS month,
            si.cost_center AS cost_center,
            SUM(si.net_total) AS net_total
        FROM 
            `tabSales Invoice` AS si
        WHERE 
            si.docstatus = 1 
            AND (si.posting_date BETWEEN %(from_date)s AND %(to_date)s 
                OR si.posting_date BETWEEN %(previous_month_start)s AND %(previous_month_end)s)
        {('AND si.cost_center = %(cost_center)s' if filters.get("cost_center") else '')}
        GROUP BY 
            DATE_FORMAT(si.posting_date, '%%Y-%%m'), si.cost_center
    """

    # Print the query for debugging
    print("Generated Query: ", query)

    sales_data = frappe.db.sql(query, params, as_dict=True)

    cost_center_data = {}
    months_in_range = set()
    
    # Include the previous month in the range
    months_in_range.add(previous_month)
    
    # Add all months from the selected date range to the set
    current_date = from_date
    while current_date <= to_date:
        months_in_range.add(current_date.strftime('%m'))
        current_date += timedelta(days=32)
        current_date = current_date.replace(day=1)
    
    # Initialize cost center data
    for entry in sales_data:
        cost_center = entry.cost_center
        month = entry.month[-2:]
        
        if cost_center not in cost_center_data:
            cost_center_data[cost_center] = {'cost_center': cost_center, 'net_total': 0.0}
        
        cost_center_data[cost_center][month] = flt(entry.net_total)
        cost_center_data[cost_center]['net_total'] += flt(entry.net_total)

    # Fill missing months with 0.0 within the selected range
    for cost_center in cost_center_data:
        for month_num in months_in_range:
            if month_num not in cost_center_data[cost_center]:
                cost_center_data[cost_center][month_num] = 0.0

    return list(cost_center_data.values())

