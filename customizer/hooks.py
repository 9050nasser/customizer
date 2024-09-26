# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "customizer"
app_title = "Customizer"
app_publisher = "Ahmed"
app_description = "Add extra customization"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "dev.amadi7@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/customizer/css/customizer.css"
app_include_js = [
    "/assets/customizer/js/qrious.min.js",
    "/assets/customizer/js/xlsx.full.min.js"
]
# include js, css files in header of web template
# web_include_css = "/assets/customizer/css/customizer.css"
# web_include_js = "/assets/customizer/js/customizer.js"

# include js in page
page_js = {"point-of-sale" : "public/js/pos_custom.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "customizer.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "customizer.install.before_install"
# after_install = "customizer.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "customizer.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Administrative Communication": "customizer.queries.get_permission_query_conditions",
#	"Stock Entry":	"customizer.queries.get_permission_query_conditions_stock_entry", 
}


has_permission = {
 	"Administrative Communication": "customizer.customizer.doctype.administrative_communication.administrative_communication.validate_access",
#	"Stock Entry": "customizer.queries.validate_access_stock_entry",
	#"Material Request": "customizer.queries.validate_access_material_request", 

}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Salary Slip":{
		"before_validate":["customizer.tool.rewrite_calculate_net_pay"]
	},
	"Sales Invoice":{
	#"customizer.tool.validate_batch",
		"validate":["customizer.tool.validate_max_discount","customizer.tool.validate_pos_profile","customizer.tool.validate_sales_person"\
		,"customizer.tool.validate_pos_profile_cost_center","customizer.tool.validate_return"\
		,"customizer.tool.create_qr_code","customizer.tool.validate_batch","customizer.tool.validate_pos_outstanding", "customizer.tool.validate_item_tax_template","customizer.tool.set_is_free_items", "customizer.tool.validate_eid"],
		"on_cancel":"customizer.tool.validate_cancel_date",
		"before_validate":["customizer.tool.validate_pos_return"],
		"on_submit": ["customizer.tool.validate_returen_role","customizer.tool.create_sil"]
	},
	"Purchase Invoice":{
		"on_cancel":"customizer.tool.validate_cancel_date",
		"on_submit": ["customizer.tool.validate_returen_role"]
	},
	"Stock Entry":{
		"before_validate":["customizer.tool.validate_qty"],
		#"validate":["customizer.tool.validate_warehouse_supervise"]
	},
	"Sales Order":{
		"before_update_after_submit":["customizer.tool.so_calculate_taxes_and_totals"],
		"on_update_after_submit":["customizer.tool.so_calculate_taxes_and_totals"],
		"validate":["customizer.tool.so_calculate_taxes_and_totals"]
	},
	"Salary Structure": {
		"on_submit": "customizer.utils.add_salary_structure_assignment",
		"before_update_after_submit" :"customizer.utils.remove_ss_validate"
	},
	"Leave Application":{
	
		# "before_submit": "customizer.utils.make_ticket_expense_claim",
		"on_submit": ["customizer.utils.make_ticket_expense_claim", "customizer.utils.add_leave_entitlement"],
		"on_trash": "customizer.utils.delete_attendance"
	},
	"POS Closing Voucher":{	
		"on_submit": "customizer.utils.get_zero_vat",
		"before_validate": "customizer.utils.overrid_validate"
	},
	"Contact":{	
		"validate": "customizer.utils.validate_phone"
	},
	"Batch":{
		"validate": ["customizer.tool.before_4_month", "customizer.tool.before_1_month"]
	},
	"Item": {
		"after_insert": "customizer.tool.on_insert_item",
		"validate": ["customizer.reorder_item.reorder_item","customizer.tool.validate_warehouse_for_auto_reorder","customizer.tool.validate_auto_reorder_enabled_in_stock_settings"\
		,"customizer.tool.update_template_tables"]
	},
	"Employee" : {
		"validate": ["customizer.tool.clear_contract_end_fields"]
	},
	#"Bin":{
		#"validate": "customizer.tool.val_warehouse"
	#}
	#"Customer":{
		#"validate": "customizer.utils.validate_mobile_no"
	#}
}
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron": {
        "0 0 1 1 *": [
            "customizer.tool.update_contract_end_dates"
        ]
    },
# 	"all": [
# 		"customizer.tasks.all"
# 	],
 	"daily": [
# 		"customizer.tasks.daily",
		"customizer.tool.update_contract_end_dates",
 	],
 	"hourly": [
# 		"customizer.tasks.hourly",
		"customizer.tool.update_contract_end_dates",
 	],
# 	"weekly": [
# 		"customizer.tasks.weekly"
# 	]
	"monthly": [
# 		"customizer.tasks.monthly"
		"customizer.reorder_item.reorder_item",
		"customizer.reorder_item.create_material_request"
	]
}

# Testing
# -------

# before_tests = "customizer.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "customizer.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "customizer.task.get_dashboard_data"
# }

fixtures = ["Role", "Custom Field", "Custom Script", "Property Setter"]
