import frappe

@frappe.whitelist()
def custom_repost_stock(item_code, warehouse):
    stock_entries = frappe.get_list("Stock Ledger Entry", filters={"item_code": item_code, "warehouse": warehouse}, order_by="posting_date asc, posting_time asc, creation asc")
    
    for entry in stock_entries:
        sle = frappe.get_doc("Stock Ledger Entry", entry.name)
        sle.repost()


