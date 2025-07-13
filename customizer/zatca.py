import frappe
from frappe.utils import getdate
from zatca2024.zatca2024.zatcasdkcode import zatca_Background
import logging
import time  # Import the time module

# Set up logging
logging.basicConfig(filename='/home/erp/frappe-bench/logs/zatca_process.log', level=logging.INFO)

def process_invoices():
    # Define the cutoff date
    cutoff_date = getdate("2024-10-01")
    
    # Log the start of the process
    logging.info(f"Process started for invoices after {cutoff_date}")
    
    # Fetch all sales invoices where custom_zatca_status is "Not Submitted", docstatus is 1, and created after 1st August 2024
    invoices = frappe.get_all("Sales Invoice", 
                              filters={
                                  "custom_zatca_status": "Not Submitted",
                                  "docstatus": 1,
                                  "posting_date": [">=", cutoff_date]
                              }, 
                              fields=["name", "custom_zatca_status", "posting_date", "posting_time"],
                              order_by="posting_date asc, posting_time asc")  # Order by posting_date and posting_time in ascending order
    
    # Log the number of invoices fetched
    logging.info(f"Fetched {len(invoices)} invoices for processing.")
    
    for invoice in invoices:
        logging.info(f"Processing invoice: {invoice.name}")
        print(f"Processing invoice: {invoice.name}")
        
        if invoice.custom_zatca_status not in ["CLEARED", "REPORTED"]:
            try:
                # Directly call the zatca_Background function with the invoice number
                response = zatca_Background(invoice_number=invoice.name)
                
                # Check the response and handle it
                if response and response.get("message"):
                    frappe.msgprint(response["message"])
                    logging.info(f"Response for invoice {invoice.name}: {response['message']}")
                    print(f"Response for invoice {invoice.name}: {response['message']}")
                
                # Reload the document to reflect any changes
                invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)
                invoice_doc.reload()
                
            except Exception as e:
                logging.error(f"Error processing invoice {invoice.name}: {str(e)}")
                print(f"Error processing invoice {invoice.name}: {str(e)}")
                frappe.log_error(message=str(e), title=f"Error processing invoice {invoice.name}")
        
        # Introduce a small timeout of 2 seconds between each invoice
        time.sleep(4)
    
    # Log the end of the process
    logging.info("Process completed.")
    print("Process completed.")
