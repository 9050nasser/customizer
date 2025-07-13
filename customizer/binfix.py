import frappe
from frappe.utils import flt
import logging

# Setup console logger
console_logger = logging.getLogger("bin_recalculation")
console_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
console_logger.addHandler(console_handler)

def recalculate_bin_qty_for_all_items():
    items = frappe.get_all("Item", filters={"disabled": 0,"name":"4002064412917"}, fields=["name"])
    warehouses = frappe.get_all("Warehouse", filters={"is_group": 0}, fields=["name"])

    for item in items:
        item_code = item.name
        for warehouse in warehouses:
            warehouse_name = warehouse.name
            try:
                bin_name = get_or_make_bin(item_code, warehouse_name)
                recalculate_bin(bin_name, item_code, warehouse_name)
                console_logger.info(f"Recalculated bin for Item: {item_code} in Warehouse: {warehouse_name}")

            except Exception as e:
                console_logger.error(f"Failed to recalculate bin for Item: {item_code} in Warehouse: {warehouse_name} - {e}")

def get_or_make_bin(item_code, warehouse):
    bin_name = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse})
    if not bin_name:
        bin_doc = frappe.get_doc({
            "doctype": "Bin",
            "item_code": item_code,
            "warehouse": warehouse
        })
        bin_doc.insert()
        bin_name = bin_doc.name
    return bin_name

def recalculate_bin(bin_name, item_code, warehouse_name):
    actual_qty = frappe.db.sql("""
        select sum(actual_qty) from `tabStock Ledger Entry` 
        where item_code=%s and warehouse=%s
    """, (item_code, warehouse_name))[0][0] or 0

    frappe.db.set_value("Bin", bin_name, "actual_qty", flt(actual_qty))
