import frappe

def patch_delete():
    patches_to_delete = [
        'erpnext.patches.v12_0.update_is_cancelled_field',
        'erpnext.patches.v13_0.add_bin_unique_constraint',
        'erpnext.patches.v14_0.change_is_subcontracted_fieldtype',
        'erpnext.patches.v13_0.update_returned_qty_in_pr_dn',
        'erpnext.patches.v13_0.update_actual_start_and_end_date_in_wo',
        'erpnext.patches.v12_0.update_production_plan_status',
        'erpnext.patches.v13_0.update_reserved_qty_closed_wo',
        'erpnext.patches.v14_0.set_maintain_stock_for_bom_item',
        'erpnext.patches.v13_0.update_docs_link',
        'erpnext.patches.v13_0.item_reposting_for_incorrect_sl_and_gl',
        'erpnext.patches.v13_0.requeue_failed_reposts',
        'erpnext.patches.v14_0.update_flag_for_return_invoices',
        'erpnext.patches.v15_0.set_reserved_stock_in_bin',
        'erpnext.stock.doctype.delivery_note.patches.drop_unused_return_against_index',
        'erpnext.patches.v15_0.update_total_number_of_booked_depreciations'
    ]

    for patch in patches_to_delete:
        frappe.db.sql('DELETE FROM `tabPatch Log` WHERE patch = %s', patch)
        print(f'Deleted patch log entry for {patch}')

    frappe.db.commit()
