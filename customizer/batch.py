import frappe
import logging
from datetime import datetime
import time

# Setup logging
logging.basicConfig(filename='recreate_sle.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Global list to accumulate failed documents
failed_docs = []

def write_failed_docs_to_file():
    # Only write if there are failed documents
    if failed_docs:
        with open('mad.log', 'w') as file:
            for doc_type, doc_name, error in failed_docs:
                file.write(f"{doc_type}, {doc_name}, {error}\n")
        print("Failed documents have been logged to 'mad.log'.")
    else:
        print("No failed documents to log.")

def find_doc_types_with_fields():
    batch_fields = frappe.get_all('DocField', filters={'options': 'Batch'}, fields=['parent'])
    serial_bundle_fields = frappe.get_all('DocField', filters={'options': 'Serial and Batch Bundle'}, fields=['parent'])

    # Extracting unique DocTypes
    doc_types = {d['parent'] for d in batch_fields + serial_bundle_fields}
    return list(doc_types)

def clear_fields_in_db(doc_types, batch_size=10000):
    fields_to_clear = ['batch_no', 'serial_no', 'serial_and_batch_bundle']  # Customize as needed

    for doctype in doc_types:
        for field in fields_to_clear:
            # Check if the field exists in the doctype
            if frappe.db.exists('DocField', {'fieldname': field, 'parent': doctype}):
                try:
                    # Get the total number of rows that need to be updated
                    total_rows = frappe.db.count(doctype, filters={field: ['is', 'set']})
                    processed_rows = 0

                    print(f"Starting to clear `{field}` in `{doctype}` documents...")

                    # Perform updates in batches
                    while processed_rows < total_rows:
                        # Update the field to NULL in batches
                        frappe.db.sql(f"""
                            UPDATE `tab{doctype}`
                            SET `{field}` = NULL
                            WHERE `{field}` IS NOT NULL
                            LIMIT {batch_size}
                        """)
                        frappe.db.commit()  # Commit changes after each batch

                        processed_rows += batch_size
                        if processed_rows > total_rows:
                            processed_rows = total_rows

                        # Calculate progress
                        progress = (processed_rows / total_rows) * 100
                        print(f"Progress: {processed_rows}/{total_rows} rows updated ({progress:.2f}%)")

                        # Optional: sleep briefly to reduce load (customize delay as needed)
                        time.sleep(0.1)

                    print(f"Cleared `{field}` in all `{doctype}` documents.")
                except Exception as e:
                    print(f"Error clearing `{field}` in `{doctype}`: {str(e)}")

def delete_all_records_from_tables(tables, batch_size=10000):
    for table in tables:
        try:
            # Get the total number of records in the table
            total_rows = frappe.db.count(table)
            processed_rows = 0

            print(f"Starting to delete records from `{table}`... Total: {total_rows} rows")

            # Delete records in batches
            while processed_rows < total_rows:
                # Delete records in batches
                frappe.db.sql(f"""
                    DELETE FROM `tab{table}`
                    LIMIT {batch_size}
                """)
                frappe.db.commit()  # Commit changes after each batch

                processed_rows += batch_size
                if processed_rows > total_rows:
                    processed_rows = total_rows

                # Calculate progress
                progress = (processed_rows / total_rows) * 100
                print(f"Progress: {processed_rows}/{total_rows} rows deleted ({progress:.2f}%)")

                # Optional: sleep briefly to reduce load (customize delay as needed)
                time.sleep(0.1)

            print(f"All records deleted from `{table}`.")
        except Exception as e:
            print(f"Error deleting records from `{table}`: {str(e)}")

def clear():
    # print("update tabItem set has_batch_no")
    frappe.db.sql("update tabItem set has_batch_no = 0 ;")
    frappe.db.commit() 
    print("update `tabStock Entry` set custom_branch_type ")
    frappe.db.sql("update `tabStock Entry` set custom_branch_type = 'Store' where custom_branch_type is null;")
    frappe.db.commit() 
    print("update `tabStock Ledger Entry` set stock_queue = '[]' ,has_batch_no =0  ")
    frappe.db.sql("update `tabStock Ledger Entry` set stock_queue = '[]'  ,has_batch_no =0 ")
    frappe.db.commit() 
    tables_to_clear = ['Serial and Batch Bundle','Batch']  # List of tables to delete records from
    delete_all_records_from_tables(tables_to_clear)
    frappe.db.commit() 
    frappe.db.set_single_value("Stock Settings", "do_not_use_batchwise_valuation", 1)
    frappe.db.set_single_value("Stock Settings", "valuation_method", "Moving Average")
    #frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 1)
    frappe.db.commit() 

    doc_types = find_doc_types_with_fields()
    clear_fields_in_db(doc_types)

    #frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 0)
    frappe.db.commit() 
    print("DOne")
