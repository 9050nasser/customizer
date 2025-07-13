import frappe
from frappe.utils import getdate, get_time

def validate_pos_invoice(doc, method):
    if doc.is_return == 1 and not frappe.get_value("POS Invoice", doc.return_against, "consolidated_invoice"):
        frappe.throw("POS Invoice is not consolidated. Wait a few minutes and try again.")

import time

def on_submit_pos_invoice(doc, method):
    # Create a minimal Sales Invoice, ignoring mandatory fields and validation
    sales_invoice = frappe.new_doc("Sales Invoice")

    # Set basic fields (even these will skip validation)
    sales_invoice.custom_sales_person = doc.custom_sales_person
    sales_invoice.customer = doc.customer
    sales_invoice.company = doc.company
    sales_invoice.posting_date = getdate(doc.posting_date)
    sales_invoice.posting_time = get_time(doc.posting_time)
    sales_invoice.set_posting_time = 1
    sales_invoice.is_pos = 1
    sales_invoice.pos_profile = doc.pos_profile
    sales_invoice.currency = doc.currency
    sales_invoice.custom_walaa_code = doc.custom_walaa_code
    sales_invoice.coupon_code = doc.coupon_code
    sales_invoice.company_address = doc.company_address
    sales_invoice.customer_address = doc.customer_address

    # Save the minimal Sales Invoice ignoring mandatory and validation checks
    sales_invoice.flags.ignore_mandatory = True
    sales_invoice.flags.ignore_validate = True
    sales_invoice.save(ignore_permissions=True)

    # Ensure the Sales Invoice is saved before proceeding
    frappe.db.commit()  # Commit to the database to avoid race conditions

    # Enqueue the task to update the Sales Invoice with full data from the POS Invoice
    frappe.enqueue(
        "customizer.event.update_sales_invoice_with_pos_data",
        pos_invoice_name=doc.name,
        sales_invoice_name=sales_invoice.name,
        queue="long",
        timeout=6000
    )

    # Update the POS Invoice with the reference to the consolidated Sales Invoice
    doc.consolidated_invoice = sales_invoice.name
    doc.db_update()

def update_sales_invoice_with_pos_data(pos_invoice_name, sales_invoice_name):
    try:
        # Fetch the POS Invoice and Sales Invoice documents
        pos_invoice = frappe.get_doc("POS Invoice", pos_invoice_name)
        sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_name)

        # Populate sales invoice fields from POS invoice
        sales_invoice.customer = pos_invoice.customer
        sales_invoice.custom_sales_person = pos_invoice.custom_sales_person
        sales_invoice.cost_center = pos_invoice.cost_center
        sales_invoice.customer_group = pos_invoice.customer_group
        sales_invoice.taxes_and_charges = pos_invoice.taxes_and_charges
        sales_invoice.conversion_rate = pos_invoice.conversion_rate
        sales_invoice.selling_price_list = pos_invoice.selling_price_list
        sales_invoice.price_list_currency = pos_invoice.price_list_currency
        sales_invoice.apply_discount_on = pos_invoice.apply_discount_on
        sales_invoice.additional_discount_percentage = pos_invoice.additional_discount_percentage
        sales_invoice.discount_amount = pos_invoice.discount_amount
        sales_invoice.rounding_adjustment = pos_invoice.rounding_adjustment
        sales_invoice.base_rounding_adjustment = pos_invoice.base_rounding_adjustment
        sales_invoice.base_rounded_total = pos_invoice.base_rounded_total
        sales_invoice.rounded_total = pos_invoice.rounded_total
        sales_invoice.status = pos_invoice.status
        sales_invoice.debit_to = pos_invoice.debit_to
        sales_invoice.due_date = pos_invoice.due_date
        sales_invoice.update_stock = pos_invoice.update_stock
        sales_invoice.set_warehouse = pos_invoice.set_warehouse
        sales_invoice.total_qty = pos_invoice.total_qty
        sales_invoice.base_total = pos_invoice.base_total
        sales_invoice.net_total = pos_invoice.net_total
        sales_invoice.total_net_weight = pos_invoice.total_net_weight
        sales_invoice.base_total_taxes_and_charges = pos_invoice.base_total_taxes_and_charges
        sales_invoice.total_taxes_and_charges = pos_invoice.total_taxes_and_charges
        sales_invoice.base_grand_total = pos_invoice.base_grand_total
        sales_invoice.grand_total = pos_invoice.grand_total
        sales_invoice.base_in_words = pos_invoice.base_in_words
        sales_invoice.in_words = pos_invoice.in_words
        sales_invoice.paid_amount = pos_invoice.paid_amount
        sales_invoice.write_off_amount = pos_invoice.write_off_amount
        sales_invoice.custom_walaa_code = pos_invoice.custom_walaa_code
        sales_invoice.coupon_code = pos_invoice.coupon_code

        # Handle return case - ensure return_against is valid
        if pos_invoice.is_return:
            sales_invoice.is_return = 1
            sales_invoice.return_against = frappe.get_value("POS Invoice", pos_invoice.return_against, "consolidated_invoice")

        # Copy items from POS Invoice to Sales Invoice, filtering out zero-quantity items
        sales_invoice.items = []
        for item in pos_invoice.items:
            print(item.qty)
            if item.qty != 0:  # Prevent 0 qty items in return invoices
                si_item = sales_invoice.append("items", {})
                si_item.update({
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount,
                    "base_rate": item.base_rate,
                    "base_amount": item.base_amount,
                    "warehouse": item.warehouse,
                    "batch_no": item.batch_no,
                    "serial_no": item.serial_no,
                    "cost_center": sales_invoice.cost_center
                })

        # Copy taxes from POS Invoice to Sales Invoice with mandatory fields check
        sales_invoice.taxes = []
        for tax in pos_invoice.taxes:
            if tax.charge_type and tax.account_head and tax.description:  # Ensuring mandatory fields are present
                si_tax = sales_invoice.append("taxes", {})
                si_tax.update({
                    "charge_type": tax.charge_type,
                    "account_head": tax.account_head,
                    "description": tax.description,
                    "rate": tax.rate,
                    "tax_amount": tax.tax_amount,
                    "base_tax_amount": tax.base_tax_amount,
                })

        # Copy pricing rules
       # sales_invoice.custom_coupon_code = pos_invoice.coupon_code
        #sales_invoice.pricing_rules = []
        #for pr in pos_invoice.pricing_rules:
         #   si_pr = sales_invoice.append("pricing_rules", {})
          #  si_pr.update({
           #     "pricing_rule": pr.pricing_rule,
            #    "item_code": pr.item_code,
             #   "margin_type": pr.margin_type,
              #  "rate_or_discount": pr.rate_or_discount,
               # "child_docname": pr.child_docname,
                #"rule_applied": pr.rule_applied,
           # })

        # Copy payments from POS Invoice to Sales Invoice
        sales_invoice.payments = []
        for payment in pos_invoice.payments:
            si_payment = sales_invoice.append("payments", {})
            si_payment.update({
                "mode_of_payment": payment.mode_of_payment,
                "amount": payment.amount,
                "base_amount": payment.base_amount,
                "account": payment.account
            })

        # Copy loyalty program details safely
        if pos_invoice.redeem_loyalty_points:
            sales_invoice.redeem_loyalty_points = 1
            sales_invoice.loyalty_points = pos_invoice.loyalty_points
            sales_invoice.loyalty_amount = pos_invoice.loyalty_amount
            sales_invoice.loyalty_redemption_account = pos_invoice.loyalty_redemption_account
            sales_invoice.loyalty_redemption_cost_center = pos_invoice.loyalty_redemption_cost_center

        # Copy additional information such as pricing rule, sales partner, etc.
        sales_invoice.loyalty_program = pos_invoice.loyalty_program
        sales_invoice.sales_partner = pos_invoice.sales_partner
        sales_invoice.commission_rate = pos_invoice.commission_rate
        sales_invoice.total_commission = pos_invoice.total_commission
        sales_invoice.campaign = pos_invoice.campaign
        #sales_invoice.custom_coupon_code = pos_invoice.campaign

        # Check and assign default customer if missing
        if not sales_invoice.customer:
            sales_invoice.customer = frappe.db.get_value("POS Profile", sales_invoice.pos_profile, "customer")

        # Submit the Sales Invoice after updating it
        sales_invoice.save(ignore_permissions=True)
        sales_invoice.flags.ignore_permissions = True
        sales_invoice.submit()

        # Update POS Invoice with the reference to the consolidated Sales Invoice
        pos_invoice.consolidated_invoice = sales_invoice.name
        if not pos_invoice.customer:
            pos_invoice.customer = frappe.db.get_value("POS Profile", pos_invoice.pos_profile, "customer")
        pos_invoice.db_update()

    except frappe.ValidationError as e:
        frappe.log_error(f"Validation Error in {sales_invoice_name}: {str(e)}", "update_sales_invoice_with_pos_data")
        print(f"Validation Error in {sales_invoice_name}: {str(e)}")
    except frappe.DoesNotExistError as e:
        frappe.log_error(f"Document Missing Error in {sales_invoice_name}: {str(e)}", "update_sales_invoice_with_pos_data")
        print(f"Document Missing Error in {sales_invoice_name}: {str(e)}")
    except Exception as e:
        frappe.log_error(f"General Error in {sales_invoice_name}: {str(e)}", "update_sales_invoice_with_pos_data")
        print(f"General Error in {sales_invoice_name}: {str(e)}")



def fix():
    update_sales_invoice_with_pos_data("KHe-POS-2025-16476", "ACC-SINV-2024-68398")


import frappe
import traceback

def get_pos_invoices_with_draft_consolidated_invoice():
    # Fetch all POS Invoices where the consolidated invoice is in draft status (docstatus = 0)
    pos_invoices = frappe.db.sql("""
        SELECT
            pos.name, pos.creation, pos.consolidated_invoice
        FROM
            `tabPOS Invoice` pos
        JOIN
            `tabSales Invoice` sales ON pos.consolidated_invoice = sales.name
        WHERE
            sales.docstatus = 0  -- Ensure the Sales Invoice is in draft status
            AND pos.docstatus = 1  -- Ensure the POS Invoice itself is also in draft
            and pos.posting_date > "2024-10-01"
    """, as_dict=True)
    print("HI!")
    print(pos_invoices)
    for invoice in pos_invoices:
        print(invoice)
        try:
            # Assuming update_sales_invoice_with_pos_data is a function you defined elsewhere
            update_sales_invoice_with_pos_data(invoice["name"], invoice["consolidated_invoice"])
            print(invoice["consolidated_invoice"])
            frappe.db.commit()
        except Exception as e:
            # Print the error message with traceback
            print(invoice["consolidated_invoice"] + " error")
            print("Error details:", str(e))
            traceback.print_exc()  # This will print the full traceback of the error
    return pos_invoices


from frappe.utils import today, now_datetime

def fix22():
    # Fetch all draft Sales Invoices created today with no items
    sales_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"status": "Draft", "posting_date": today()},
        fields=["name"]
    )

    for sinv in sales_invoices:
        sales_invoice_name = sinv["name"]
        
        # Find POS Invoice that references this Sales Invoice
        pos_invoice = frappe.get_value("POS Invoice", {"consolidated_invoice": sales_invoice_name}, "name")
        print(pos_invoice)
        print(sales_invoice_name)


        if pos_invoice:
            # Trigger the function to update Sales Invoice with POS data
            update_sales_invoice_with_pos_data(pos_invoice, sales_invoice_name)
