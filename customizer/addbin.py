import frappe
from frappe.utils import flt
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recalculate_bin_values():
    # Fetch all items with has_batch_no = 1
    items = frappe.get_all("Item", filters={"has_batch_no": 1, "disabled": 0, "is_stock_item": 1}, fields=["item_code"])
    a= len(items)
    logger.info(f"Found {len(items)} items with has_batch_no = 0.")

    for item in items:
        item_code = item.item_code
        logger.info(f"Processing item: {item_code} count {a}")
        a-=1

        try:
            # Fetch all distinct warehouses for the given item_code
            warehouses = frappe.get_all("Stock Ledger Entry", filters={"item_code": item_code}, fields=["warehouse"], distinct=True)
            #logger.info(f"Found {len(warehouses)} distinct warehouses for item code {item_code}.")

            for warehouse_entry in warehouses:
                warehouse = warehouse_entry.warehouse
                #logger.info(f"Processing warehouse: {warehouse}")

                try:
                    # Fetch all Stock Ledger Entries for the given item and warehouse
                    stock_ledger_entries = frappe.get_all("Stock Ledger Entry", filters={"item_code": item_code, "warehouse": warehouse}, fields=["actual_qty"])

                    # Initialize quantities
                    actual_qty = 0

                    # Iterate through all entries and sum up the quantities
                    for entry in stock_ledger_entries:
                        actual_qty += flt(entry.actual_qty)
                        #logger.debug(f"Entry actual_qty: {entry.actual_qty}, cumulative actual_qty: {actual_qty}")

                    # Verify the calculated quantities
                    #logger.info(f"Total actual quantity for item {item_code} in warehouse {warehouse}: {actual_qty}")

                    try:
                        # Get the bin document for the given item and warehouse
                        bin = frappe.get_doc("Bin", {"item_code": item_code, "warehouse": warehouse})
                        # bin.actual_qty = actual_qty
                        # bin.projected_qty = actual_qty  # Assuming projected_qty should match actual_qty
                        # bin.save()
                        # frappe.db.commit()
                        # logger.info(f"Found existing Bin for item {item_code} in warehouse {warehouse}")
                        
                    except frappe.exceptions.DoesNotExistError:
                        # Create a new bin document if it doesn't exist
                        bin = frappe.get_doc({
                            "doctype": "Bin",
                            "item_code": item_code,
                            "warehouse": warehouse,
                            "actual_qty": actual_qty,
                            "projected_qty": actual_qty,
                        })
                        bin.insert()
                        frappe.db.commit()
                        logger.info(f"Created new Bin for item {item_code} in warehouse {warehouse}")

                    # Check before updating
                    previous_actual_qty = bin.actual_qty
                    previous_projected_qty = bin.projected_qty

                    # Save the updated bin document
                    
                    #logger.info(f"Updated Bin for item {item_code} in warehouse {warehouse} with actual_qty: {actual_qty} (previous: {previous_actual_qty}), projected_qty: {actual_qty} (previous: {previous_projected_qty})")

                except Exception as e:
                    logger.error(f"Error processing warehouse {warehouse} for item {item_code}: {e}")
                    frappe.db.rollback()

        except Exception as e:
            logger.error(f"Error processing item {item_code}: {e}")
            frappe.db.rollback()

    logger.info("Bin values recalculated successfully for all items with has_batch_no = 1")
    return "Bin values recalculated successfully for all items with has_batch_no = 1"





#full sacale code 
def recalculate_bin_values_old():
    # Fetch all items with has_batch_no = 1
    items = frappe.get_all("Item", filters={"has_batch_no": 0, "disabled": 0, "is_stock_item": 1}, fields=["item_code"])
    logger.info(f"Found {len(items)} items with has_batch_no = 1.")

    for item in items:
        item_code = item.item_code
        logger.info(f"Processing item: {item_code}")

        try:
            # Fetch all distinct warehouses for the given item_code
            warehouses = frappe.get_all("Stock Ledger Entry", filters={"item_code": item_code}, fields=["warehouse"], distinct=True)
            logger.info(f"Found {len(warehouses)} distinct warehouses for item code {item_code}.")

            for warehouse_entry in warehouses:
                warehouse = warehouse_entry.warehouse
                logger.info(f"Processing warehouse: {warehouse}")

                try:
                    # Fetch all Stock Ledger Entries for the given item and warehouse
                    stock_ledger_entries = frappe.get_all("Stock Ledger Entry", filters={"item_code": item_code, "warehouse": warehouse}, fields=["actual_qty"])

                    # Initialize quantities
                    actual_qty = 0

                    # Iterate through all entries and sum up the quantities
                    for entry in stock_ledger_entries:
                        actual_qty += flt(entry.actual_qty)
                        logger.debug(f"Entry actual_qty: {entry.actual_qty}, cumulative actual_qty: {actual_qty}")

                    # Verify the calculated quantities
                    logger.info(f"Total actual quantity for item {item_code} in warehouse {warehouse}: {actual_qty}")

                    try:
                        # Get the bin document for the given item and warehouse
                        bin = frappe.get_doc("Bin", {"item_code": item_code, "warehouse": warehouse})
                        bin.actual_qty = actual_qty
                        bin.projected_qty = actual_qty  # Assuming projected_qty should match actual_qty
                        bin.save()
                        frappe.db.commit()
                        logger.info(f"Found existing Bin for item {item_code} in warehouse {warehouse}")
                    except frappe.exceptions.DoesNotExistError:
                        # Create a new bin document if it doesn't exist
                        bin = frappe.get_doc({
                            "doctype": "Bin",
                            "item_code": item_code,
                            "warehouse": warehouse,
                            "actual_qty": actual_qty,
                            "projected_qty": actual_qty,
                        })
                        bin.insert()
                        frappe.db.commit()
                        logger.info(f"Created new Bin for item {item_code} in warehouse {warehouse}")

                    # Check before updating
                    previous_actual_qty = bin.actual_qty
                    previous_projected_qty = bin.projected_qty

                    # Save the updated bin document
                    bin.save()
                    frappe.db.commit()
                    logger.info(
                        f"Updated Bin for item {item_code} in warehouse {warehouse} with actual_qty: {actual_qty} (previous: {previous_actual_qty}), projected_qty: {actual_qty} (previous: {previous_projected_qty})")

                except Exception as e:
                    logger.error(f"Error processing warehouse {warehouse} for item {item_code}: {e}")
                    frappe.db.rollback()

        except Exception as e:
            logger.error(f"Error processing item {item_code}: {e}")
            frappe.db.rollback()

    logger.info("Bin values recalculated successfully for all items with has_batch_no = 1")
    return "Bin values recalculated successfully for all items with has_batch_no = 1"
