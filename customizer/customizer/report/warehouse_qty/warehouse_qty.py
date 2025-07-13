import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
    columns, data = [], []
    columns = get_columns(filters)
    data = get_data(filters, columns)
    return columns, data

def get_columns(filters):
    columns = [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 150},
        {"label": _("Brand"), "fieldname": "brand", "fieldtype": "Data", "width": 150},
    ]

    # Add columns for each warehouse dynamically if no specific warehouse is selected
    if not filters.get('warehouse'):
        warehouses = get_warehouses(filters)
        for warehouse in warehouses:
            columns.append({
                "label": _(warehouse),
                "fieldname": warehouse,
                "fieldtype": "Float",
                "width": 100
            })
    
    columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Float", "width": 100})

    return columns

def get_warehouses(filters):
    # Get a list of all warehouses that are not groups and are included in the report
    warehouse_filters = {'is_group': 0, 'include_report': 1}
    warehouses = frappe.get_all('Warehouse', filters=warehouse_filters, fields=['name'])
    return [wh['name'] for wh in warehouses]



def get_data(filters, columns):
    data = []

    # Fetch stock quantities from Bin table with additional item details
    query = """
        SELECT
            bin.item_code,
            bin.warehouse,
            bin.actual_qty as qty,
            item.item_name,
            item.item_group,
            item.brand
        FROM
            `tabBin` bin
        JOIN
            `tabItem` item ON bin.item_code = item.name
        WHERE
            bin.actual_qty > 0
    """
    
    conditions = []
    parameters = []

    # Apply date filter to ensure it captures quantity up to the `to_date`
    if filters.get('from_date') and filters.get('to_date'):
        query += """
            AND EXISTS (
                SELECT 1 FROM `tabStock Ledger Entry` sle
                WHERE sle.item_code = bin.item_code
                AND sle.warehouse = bin.warehouse
                AND sle.posting_date <= %s
                AND sle.docstatus = 1
            )
        """
        parameters.append(filters.to_date)  # Only consider up to the `to_date`

    # Apply other filters
    if filters.get('warehouse'):
        conditions.append("bin.warehouse = %s")
        parameters.append(filters.warehouse)
    
    if filters.get('item_code'):
        conditions.append("bin.item_code = %s")
        parameters.append(filters.item_code)
    
    if filters.get('item_group'):
        conditions.append("item.item_group = %s")
        parameters.append(filters.item_group)
    
    if filters.get('brand'):
        conditions.append("item.brand = %s")
        parameters.append(filters.brand)
    
    if conditions:
        query += " AND " + " AND ".join(conditions)

    stock_data = frappe.db.sql(query, parameters, as_dict=1)

    # Gather warehouses to build the report structure
    warehouses = {col['fieldname'] for col in columns if col['fieldtype'] == "Float"}

    if filters.get('warehouse'):
        # Directly create data entries if a specific warehouse is chosen
        for row in stock_data:
            item_code = row['item_code']
            qty = flt(row['qty'])

            data.append({
                'item_code': item_code,
                'item_name': row['item_name'],
                'item_group': row['item_group'],
                'brand': row['brand'],
                filters.warehouse: qty,
                'total': qty
            })
    else:
        # Pivot the data for all warehouses
        item_dict = {}
        for row in stock_data:
            item_code = row['item_code']
            warehouse = row['warehouse']
            qty = flt(row['qty'])

            if warehouse not in warehouses:
                continue

            if item_code not in item_dict:
                item_dict[item_code] = {wh: 0 for wh in warehouses}
                item_dict[item_code]['item_code'] = item_code
                item_dict[item_code]['item_name'] = row['item_name']
                item_dict[item_code]['item_group'] = row['item_group']
                item_dict[item_code]['brand'] = row['brand']
                item_dict[item_code]['total'] = 0

            item_dict[item_code][warehouse] += qty
            item_dict[item_code]['total'] += qty

        for item_code, row in item_dict.items():
            data.append(row)

    return data

