import frappe
from frappe.utils import getdate

def get_pos_invoice_items():
    # Define the filters for POS Invoices
    filters = {
        'docstatus': 1,
        'warehouse': "مخزن معرض التخصصي- الرياض - P",
        'posting_date': ['between', ['2024-07-03', '2024-07-04']]
    }
    
    # Fetch all POS Invoice records that match the filters
    pos_invoices = frappe.get_all('POS Invoice', filters=filters, fields=['name'])
    
    # Dictionary to hold items grouped by parent
    items_by_parent = {}
    
    for invoice in pos_invoices:
        # Fetch POS Invoice Items for each invoice
        invoice_items = frappe.get_all(
            'POS Invoice Item',
            filters={
                'parent': invoice.name,
                'batch_no': '',
                'serial_and_batch_bundle': ''
            },
            fields=['*']
        )
        
        # Filter items based on has_batch_no from Item doctype
        for item in invoice_items:
            has_batch_no = frappe.get_value('Item', item.item_code, 'has_batch_no')
            if has_batch_no:
                if item.parent not in items_by_parent:
                    items_by_parent[item.parent] = []
                items_by_parent[item.parent].append(item)
    
    # Print the parent and the list of item codes under it
    for parent, items in items_by_parent.items():
        print(f"Parent: {parent}")
        for item in items:
            print(f"  Item Code: {item.item_code}")
    
    return items_by_parent
