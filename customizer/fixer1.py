# custom_patch.py
import frappe

def execute():
    # Pre model sync patches
    run_patch("erpnext.patches.v12_0.update_is_cancelled_field")
    run_patch("erpnext.patches.v13_0.add_bin_unique_constraint")
    run_patch("erpnext.patches.v14_0.change_is_subcontracted_fieldtype")
    run_patch("erpnext.patches.v13_0.update_returned_qty_in_pr_dn")
    run_patch("erpnext.patches.v13_0.update_actual_start_and_end_date_in_wo")
    run_patch("erpnext.patches.v12_0.update_production_plan_status")
    run_patch("erpnext.patches.v13_0.update_reserved_qty_closed_wo")
    run_patch("erpnext.patches.v14_0.set_maintain_stock_for_bom_item")

    # Post model sync patches
    run_patch("erpnext.patches.v13_0.update_docs_link")
    run_patch("erpnext.patches.v13_0.item_reposting_for_incorrect_sl_and_gl")
    run_patch("erpnext.patches.v13_0.requeue_failed_reposts")
    run_patch("erpnext.patches.v14_0.update_flag_for_return_invoices")
    run_patch("erpnext.patches.v15_0.set_reserved_stock_in_bin")
    run_patch("erpnext.stock.doctype.delivery_note.patches.drop_unused_return_against_index")
    run_patch("erpnext.patches.v15_0.update_total_number_of_booked_depreciations")

def run_patch(patch):
    print(f"Executing patch: {patch}")
    frappe.get_attr(patch).execute()
