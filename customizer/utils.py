# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
from frappe import _
import json
from frappe.utils import cint, getdate, formatdate,get_datetime
from datetime import tzinfo, timedelta, datetime
from dateutil import parser
from datetime import date
from dateutil.relativedelta import relativedelta
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, \
    comma_or, get_fullname, add_years, add_months, add_days, nowdate , comma_and, get_first_day, get_last_day
from frappe.model.mapper import get_mapped_doc
import datetime
from frappe.core.doctype.communication.email import make
from frappe.desk.form.load import get_attachments
import  erpnext
import frappe.defaults
from frappe import _
from frappe.utils import cstr, cint, flt, comma_or, getdate, nowdate, formatdate, format_time
from erpnext.stock.utils import get_incoming_rate
from erpnext.stock.stock_ledger import get_previous_sle, NegativeStockError, get_valuation_rate
from erpnext.stock.get_item_details import get_bin_details, get_default_cost_center, get_conversion_factor, get_reserved_qty_for_so
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.stock.doctype.batch.batch import get_batch_no, set_batch_nos, get_batch_qty
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.manufacturing.doctype.bom.bom import validate_bom_no, add_additional_cost
from erpnext.stock.utils import get_bin
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.doctype.serial_no.serial_no import update_serial_nos_after_submit, get_serial_nos
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import OpeningEntryAccountError
import json
from six import string_types, itervalues, iteritems
from frappe.database import get_db



import frappe

def get_all_doctypes_in_module(module_name=None):
    """
    Fetch all doctypes in a specific module, or in all modules if module_name is None.

    Args:
    module_name (str, optional): The name of the module to filter doctypes. Defaults to None.

    Returns:
    list: A list of doctype names.
    """
    filters = {}
    if module_name:
        filters['module'] = module_name

    doctypes = frappe.get_all('DocType', filters=filters, fields=['name'])
    return [doctype.name for doctype in doctypes]

def format_mysqldump_commands_for_module(module_name=None):
    parent_doctypes = get_all_doctypes_in_module(module_name)
    for parent_doctype in parent_doctypes:
        child_tables = get_child_tables_for_doctype(parent_doctype)
        if child_tables:  # Proceed only if there are child tables
            mysqldump_command = f"mysqldump -u username -p --no-create-info database_name"

            # Add each child table name
            for table in child_tables:
                mysqldump_command += f" '{table}'"
            
            # Specify the output file
            mysqldump_command += f" > {parent_doctype}.sql"
            
            print(mysqldump_command)


def get_child_tables_for_doctype(parent_doctype):
    """
    Function to get all child tables linked to a parent doctype.

    Args:
    parent_doctype (str): The name of the parent doctype.

    Returns:
    list: A list of child table doctypes associated with the parent doctype.
    """
    # Fetch all fields of the parent doctype that are of type 'Table'
    child_tables = frappe.get_all('DocField', fields=['options'], filters={
        'parent': parent_doctype,
        'fieldtype': 'Table'
    })

    # Extract the names of the child tables from the 'options' field
    child_table_names = [field.options for field in child_tables]

    return child_table_names

def run_info(parent_doctype):
    child_tables = get_child_tables_for_doctype(parent_doctype)
    # Prepare the base of the mysqldump command
    mysqldump_command = f"mysqldump -u username -p --no-create-info database_name"
    
    # Add each child table name, enclosed in quotes
    for table in child_tables:
        mysqldump_command += f" '{table}'"
    
    # Specify the output file at the end
    mysqldump_command += f" > {parent_doctype}.sql"
    
    print(mysqldump_command)


def submitmr():
	doc=frappe.get_doc("Stock Reconciliation","MAT-RECO-2024-00420")
	#on_submit_stock_reconciliation(doc)
	doc.submit()
	print("done")

def submitse():
	doc=frappe.get_doc("Stock Entry","MAT-STE-2024-00648")
	#on_submit_stock_reconciliation(doc)
	doc.submit()
	print("done")

def on_submit_stock_reconciliation(self):
    for d in self.get("items"):
            if d.batch_no:
                    existing_batch = frappe.get_all("Batch", filters={"item": d.item_code, "name": d.batch_no}, fields=["name"])
                    if not existing_batch:
                            create_batch_entry(d)
                            print("Batch '{}' created for item '{}' with batch number '{}'.".format(d.name, d.item_code, d.batch_no))


def create_batch_entry(d):
    batch_entry = frappe.new_doc("Batch")
    batch_entry.name = d.batch_no
    batch_entry.item = d.item_code
    #batch_entry.expiry_date = "2024-12-31"
    batch_entry.batch_id = d.batch_no
    batch_entry.insert(ignore_permissions=True)
    frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def edit_journal_entry(journal_name):
    doc = frappe.get_doc("Journal Entry", journal_name)
    doc.cancel()

    frappe.db.sql("update `tabJournal Entry` set docstatus=0 where name='{0}'".format(journal_name))
    return 'True'
						

def validate_phone(doc, method):
    import re
    regex = r"^((\+9665)|(05))[0|3-9][0-9]{7}$"
    for d in doc.get("phone_nos"):
        test_str = d.phone
        matches = re.match(regex, test_str)
        
        if not matches :
            frappe.throw("""Bad Phone Number {0}""".format(d.phone))
    
def get_zero_vat(doc, method):
    total_zero_vat_amount = 0

    for i in range(len(doc.sales_invoices_summary)):
        invoice_name = doc.sales_invoices_summary[i].invoice
        invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
        for l in range(len(invoice_doc.items)):

            if invoice_doc.items[l].item_tax_template=='0%':
                total_zero_vat_amount = total_zero_vat_amount + invoice_doc.items[l].net_amount
    # doc.total_zero_vat = total_zero_vat_amount
    # doc.save(ignore_permissions=True)
    frappe.db.sql("update `tabPOS Closing Voucher` set total_zero_vat='{0}' where name='{1}'".format(total_zero_vat_amount, doc.name))
    frappe.db.commit()
    
def overrid_validate(doc, method):
    doc.validate = pos_closing_validate(doc)

def pos_closing_validate(self):
    from erpnext.selling.doctype.pos_closing_voucher.pos_closing_voucher import get_invoices
    self.validate_difference()
    self.validate_collected_amount()
    filters = {
			'doc': self.name,
			'from_date': self.period_start_date,
			'to_date': self.period_end_date,
			'company': self.company,
			'pos_profile': self.pos_profile,
			'user': self.user,
			'is_pos': 1
		}
    # ~ invoice_list = get_invoices(filters)
    # ~ self.set_invoice_list(invoice_list)


@frappe.whitelist()
def pos_cv_get_closing_voucher_details(data):
    import json
    from erpnext.selling.doctype.pos_closing_voucher.pos_closing_voucher import get_sales_summary,get_tax_details,get_mode_of_payment_details
    # ~ from types import SimpleNamespace
    # ~ self = json.loads(data, object_hook=lambda d: SimpleNamespace(**d))
    self =frappe.get_doc(json.loads(data))
    
    filters = {
        'doc': self.name,
        'from_date': self.period_start_date,
        'to_date': self.period_end_date,
        'company': self.company,
        'pos_profile': self.pos_profile,
        'user': self.user,
        'is_pos': 1
    }

    invoice_list = get_invoices(filters)
    self.set_invoice_list(invoice_list)

    sales_summary = get_sales_summary(invoice_list)
    self.set_sales_summary_values(sales_summary)
    self.total_amount = sales_summary['grand_total']
    self.validate_difference()
    self.validate_collected_amount()
    
    if not self.get('payment_reconciliation'):
        mop = get_mode_of_payment_details(invoice_list)
        self.set_mode_of_payments(mop)

    taxes = get_tax_details(invoice_list)
    self.set_taxes(taxes)

    return self.get_payment_reconciliation_details()





# @frappe.whitelist()
# def edit_journal_entry(journal_name):
#     doc = frappe.get_doc("Journal Entry", journal_name)
#     # doc.docstatus = 0
#     doc.cancle()
#     # doc.save(ignore_permissions=True)
#     return True

    

@frappe.whitelist()
def get_salary_components():
    return frappe.db.sql("""select name, type, salary_component_abbr, amount 
        from `tabSalary Component` where salary_component_abbr in ('B', 'T', 'H', 'GOSI')""", as_dict = True)

def add_salary_structure_assignment(doc, method):
    
    if not frappe.db.exists("Salary Structure Assignment", {"employee": doc.employee, "docstatus": 1}):
        frappe.get_doc({
            "doctype":"Salary Structure Assignment",
            "employee": doc.employee,
            "salary_structure": doc.name,
            "from_date": doc.date_of_joining,
            "docstatus": 1
        }).insert(ignore_permissions=True)
    else:
        salary_structure_name = frappe.get_value("Salary Structure Assignment", filters = {"employee": doc.employee, "docstatus": 1}, fieldname = "salary_structure")

        frappe.throw("""Employee {0} is assigned to salary structure <b><a href="#Form/Salary Structure/{1}">{1}</a></b>""".format(doc.employee, salary_structure_name))

def remove_ss_validate(doc, method):
    doc.flags.ignore_validate_update_after_submit = True


@frappe.whitelist()
def make_salary_slip(source_name, target_doc = None, employee = None, as_print = False, print_format = None):
    def postprocess(source, target):
        if employee:
            employee_details = frappe.db.get_value("Employee", employee,
                ["employee_name", "branch", "designation", "department"], as_dict=1)
            target.employee = employee
            target.employee_name = employee_details.employee_name
            target.branch = employee_details.branch
            target.designation = employee_details.designation
            target.department = employee_details.department
        target.run_method('process_salary_structure')

    doc = get_mapped_doc("Salary Structure", source_name, {
        "Salary Structure": {
            "doctype": "Salary Slip",
            "field_map": {
                "total_earning": "gross_pay",
                "name": "salary_structure"
            }
        }
    }, target_doc, postprocess, ignore_permissions=True, ignore_child_tables=True)

    if cint(as_print):
        doc.name = 'Preview for {0}'.format(employee)
        return frappe.get_print(doc.doctype, doc.name, doc = doc, print_format = print_format)
    else:
        return doc


def make_ticket_expense_claim(doc, method):

    leave_allocation_records = get_leave_allocation_records(nowdate(), doc.employee, "Annual Leave - اجازة اعتيادية")
    if leave_allocation_records:
        from_date = leave_allocation_records[doc.employee]["Annual Leave - اجازة اعتيادية"].from_date
        to_date = leave_allocation_records[doc.employee]["Annual Leave - اجازة اعتيادية"].to_date

        existing_leaves = []
        existing_leaves = frappe.db.sql(""" select name from `tabLeave Application` where employee='{0}' and 
            country!='Saudi Arabia' and leave_type='Annual Leave - اجازة اعتيادية' and total_leave_days >=15 and 
            to_date between '{1}' and '{2}' and docstatus=1 and name != '{3}' and employee_ticket_price > 0 """.format(doc.employee, from_date, to_date, doc.name))

        emp = frappe.get_doc("Employee", doc.employee)
        # number_of_ticket = 1

        # for family in doc.family_details:
        #     if family.select:
        #         number_of_ticket = 2

        # if existing_leaves >= 1:
        #     frappe.throw(_("Employee already has applied for leave application etitlement"))
        if not existing_leaves and doc.country != 'Saudi Arabia' and doc.leave_type=='Annual Leave - اجازة اعتيادية' and flt(doc.employee_ticket_price) > 0:
            if doc.total_leave_days>=15 and doc.total_leave_days<30:
                exp_claim = frappe.get_doc({
                    "doctype":"Expense Claim",
                    "employee": doc.employee,
                    "remark": doc.description,
                    "approval_status": 'Approved'
                })

                if doc.employee_ticket_price:
                    exp_claim.append("expenses", {
                        "expense_date": doc.from_date,
                        "description": _("Employee Ticket Price"),
                        "expense_type": 'Ticket',
                        "amount": doc.employee_ticket_price,
                        "sanctioned_amount": doc.employee_ticket_price
                    })
                if doc.family_member_ticket_price:
                    exp_claim.append("expenses", {
                        "expense_date": doc.from_date,
                        "description": _("Wife Hasband Ticket Price"),
                        "expense_type": 'Ticket',
                        "amount": doc.family_member_ticket_price,
                        "sanctioned_amount": doc.family_member_ticket_price
                    })

                exp_claim.insert(ignore_permissions=True)
                frappe.db.commit()
                # update_salary_structure_status(doc.employee)
                

                frappe.msgprint("Expense Claim <b><a href='#Form/Expense Claim/{0}'>{0}</a></b> is created".format(exp_claim.name))

            elif doc.total_leave_days>=30 and getdate(doc.from_date).day-1==0:
                exp_claim = frappe.get_doc({
                    "doctype":"Expense Claim",
                    "employee": doc.employee,
                    "remark": doc.description,
                    "expenses": [
                          {
                            "doctype": "Expense Claim Detail",
                            "expense_date": doc.from_date,
                            "expense_type": 'Month Salary',
                            "amount": get_salary(doc.employee),
                            "sanctioned_amount": get_salary(doc.employee)
                          }
                    ],
                    "approval_status": 'Approved'
                })
                if doc.employee_ticket_price:
                    exp_claim.append("expenses", {
                        "expense_date": doc.from_date,
                        "description": _("Employee Ticket Price"),
                        "expense_type": 'Ticket',
                        "amount": doc.employee_ticket_price,
                        "sanctioned_amount": doc.employee_ticket_price
                    })
                if doc.family_member_ticket_price:
                    exp_claim.append("expenses", {
                        "expense_date": doc.from_date,
                        "description": _("Wife Hasband Ticket Price"),
                        "expense_type": 'Ticket',
                        "amount": doc.family_member_ticket_price,
                        "sanctioned_amount": doc.family_member_ticket_price
                    })
                exp_claim.insert(ignore_permissions=True)
                frappe.db.commit()
                # update_salary_structure_status(doc.employee)
                frappe.msgprint("Expense Claim <b><a href='#Form/Expense Claim/{0}'>{0}</a></b> is created".format(exp_claim.name))

                frappe.get_doc({
                    "doctype":"Additional Salary",
                    "payroll_date": doc.from_date,
                    "employee": doc.employee,
                    "salary_component": 'Additional Deduct',
                    "amount": get_salary_all(doc.employee, doc.from_date),
                    "docstatus": 1
                }).insert(ignore_permissions=True)


            elif doc.total_leave_days>=30 and getdate(doc.from_date).day-1!=0:
                exp_claim = frappe.get_doc({
                    "doctype":"Expense Claim",
                    "employee": doc.employee,
                    "remark": doc.description,
                    "expenses": [
                          {
                            "doctype": "Expense Claim Detail",
                            "expense_date": doc.from_date,
                            "expense_type": 'Month Salary',
                            "amount": get_salary(doc.employee),
                            "sanctioned_amount": get_salary(doc.employee)
                          },
                          {
                            "doctype": "Expense Claim Detail",
                            "expense_date": doc.from_date,
                            "expense_type": 'Month Salary',
                            "description": "Salary of {0} working days".format(getdate(doc.from_date).day-1),
                            "amount": (get_salary(doc.employee)/30)*(getdate(doc.from_date).day-1),
                            "sanctioned_amount": (get_salary(doc.employee)/30)*(getdate(doc.from_date).day-1)
                          }
                    ],
                    "approval_status": 'Approved'
                })
                if doc.employee_ticket_price:
                    exp_claim.append("expenses", {
                        "expense_date": doc.from_date,
                        "description": _("Employee Ticket Price"),
                        "expense_type": 'Ticket',
                        "amount": doc.employee_ticket_price,
                        "sanctioned_amount": doc.employee_ticket_price
                    })
                if doc.family_member_ticket_price:
                    exp_claim.append("expenses", {
                        "expense_date": doc.from_date,
                        "description": _("Wife Ticket Price"),
                        "expense_type": 'Ticket',
                        "amount": doc.family_member_ticket_price,
                        "sanctioned_amount": doc.family_member_ticket_price
                    })
                exp_claim.insert(ignore_permissions=True)
                frappe.db.commit()
                frappe.msgprint("Expense Claim <b><a href='#Form/Expense Claim/{0}'>{0}</a></b> is created".format(exp_claim.name))
                # update_salary_structure_status(doc.employee)

                frappe.get_doc({
                    "doctype":"Additional Salary",
                    "payroll_date": doc.from_date,
                    "employee": doc.employee,
                    "salary_component": 'Additional Deduct',
                    "amount": get_salary_all(doc.employee, doc.from_date),
                    "docstatus": 1
                }).insert(ignore_permissions=True)

def update_salary_structure_status(employee):
    ss_doc = frappe.get_doc("Salary Structure", {"employee": employee})
    ss_doc.db_set("is_active", "No")

def update_employment_status(doc, method):
    emp_doc = frappe.get_doc("Employee", doc.employee)
    emp_doc.db_set("employment_status", "Vacation")

@frappe.whitelist()
def enable_employee_salary(docname):
    ss_doc = frappe.get_doc("Salary Structure", {"name": docname})
    ss_doc.db_set("is_active", "Yes")

@frappe.whitelist()
def disable_employee_salary(docname):
    ss_doc = frappe.get_doc("Salary Structure", {"name": docname})
    ss_doc.db_set("is_active", "No")

def add_return_from_leave():
    # doc = frappe.get_doc("Leave Application", "HR-LAP-2020-00002")
    leaves = frappe.db.sql("select name from `tabLeave Application` where to_date = '{0}' and leave_type = '{1}' ".format(nowdate(), 'Annual Leave - اجازة اعتيادية'), as_dict=True)
    for leave in leaves:
        doc = frappe.get_doc("Leave Application", leave.name)
        rfl = frappe.new_doc("Return From Leave")
        emp = frappe.get_doc("Employee", doc.employee)
        rfl.employee = doc.employee
        rfl.employee_name = emp.employee_name
        rfl.department = emp.department
        rfl.branch = emp.branch
        rfl.from_date = doc.from_date
        rfl.to_date = doc.to_date
        rfl.leave_application = doc.name
        rfl.total_leave_days = doc.total_leave_days
        rfl.flags.ignore_mandatory = True
        rfl.flags.ignore_validate = True
        rfl.insert(ignore_permissions = True)

def add_leave_entitlement(doc, method):
    if doc.employee_ticket_price > 0:
        le = frappe.new_doc("Leave Entitlement")
        le.leave_application = doc.name
        le.from_date = doc.from_date
        le.to_date = doc.to_date
        le.employee = doc.employee
        le.employee_english_name = doc.employee_name
        # le.employee_arabic_name = frappe.get_value("Employee", doc.employee, "full_name_arabic")
        le.department = doc.department
        # le.branch = doc.branch
        le.total_leave_days = doc.total_leave_days
        le.employee_ticket_price = doc.employee_ticket_price
        le.family_member_ticket_price = doc.family_member_ticket_price
        le.insert(ignore_permissions = True)
        frappe.msgprint("Leave Entitlement <b><a href='#Form/Leave Entitlement/{0}'>{0}</a></b> is created".format(le.name))



def get_salary(employee):
    salary_amount = 0

    salary_slip_name = frappe.db.sql("select name from `tabSalary Slip` where employee='{0}' order by creation desc limit 1".format(employee))
    if salary_slip_name:
        doc = frappe.get_doc('Salary Slip', salary_slip_name[0][0])

        for earning in doc.earnings:
            if earning.salary_component =='Basic':
                salary_amount = earning.amount+(earning.amount/4)

    else:
        doc = frappe.new_doc("Salary Slip")
        doc.payroll_frequency= "Monthly"
        doc.start_date=get_first_day(getdate(nowdate()))
        doc.end_date=get_last_day(getdate(nowdate()))
        doc.employee= str(employee)
        doc.posting_date= nowdate()
        doc.insert(ignore_permissions=True)


        if doc.name:
            for earning in doc.earnings:
                if earning.salary_component =='Basic':
                    salary_amount = earning.amount+(earning.amount/4)

            doc.delete()

    return round(salary_amount)




def get_salary_all(employee,salary_date):
    salary_amount = 0

    salary_slip_name = frappe.db.sql("select name from `tabSalary Slip` where employee='{0}' order by creation desc limit 1".format(employee))
    if salary_slip_name:
        doc = frappe.get_doc('Salary Slip', salary_slip_name[0][0])

        salary_amount = doc.gross_pay

    else:
        doc = frappe.new_doc("Salary Slip")
        doc.payroll_frequency= "Monthly"
        doc.start_date=get_first_day(getdate(salary_date))
        doc.end_date=get_last_day(getdate(salary_date))
        doc.employee= str(employee)
        doc.posting_date= nowdate()
        doc.insert(ignore_permissions=True)


        if doc.name:
            salary_amount = doc.gross_pay

            doc.delete()

    return round(salary_amount)

def get_leave_allocation_records(date, employee=None, leave_type=None):
    conditions = (" and employee='%s'" % employee) if employee else ""
    conditions += (" and leave_type='%s'" % leave_type) if leave_type else ""
    leave_allocation_records = frappe.db.sql("""
        select employee, leave_type, total_leaves_allocated, from_date, to_date
        from `tabLeave Allocation`
        where %s between from_date and to_date and docstatus=1 {0}""".format(conditions), (date), as_dict=1)

    allocated_leaves = frappe._dict()
    for d in leave_allocation_records:
        allocated_leaves.setdefault(d.employee, frappe._dict()).setdefault(d.leave_type, frappe._dict({
            "from_date": d.from_date,
            "to_date": d.to_date,
            "total_leaves_allocated": d.total_leaves_allocated
        }))

    return allocated_leaves

def delete_attendance(doc, method):
    atts = frappe.db.sql("select name from `tabAttendance` where leave_application = '{0}' ".format(doc.name), as_dict = True)
    for att in atts:
        frappe.delete_doc("Attendance", att.name, force=1)
        
        


def get_item_details(self, args=None, for_update=False):
    from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
    from erpnext.setup.doctype.brand.brand import get_brand_defaults
    from erpnext.stock.get_item_details import get_bin_details, get_default_cost_center, get_conversion_factor, get_reserved_qty_for_so

    # ~ frappe.throw(self.stock_entry_reason)
    item = frappe.db.sql("""select i.name, i.stock_uom, i.description, i.image, i.item_name, i.item_group,
            i.has_batch_no, i.sample_quantity, i.has_serial_no, i.allow_alternative_item,
            id.expense_account, id.buying_cost_center
        from `tabItem` i LEFT JOIN `tabItem Default` id ON i.name=id.parent and id.company=%s
        where i.name=%s
            and i.disabled=0
            and (i.end_of_life is null or i.end_of_life='0000-00-00' or i.end_of_life > %s)""",
        (self.company, args.get('item_code'), nowdate()), as_dict = 1)

    if not item:
        frappe.throw(_("Item {0} is not active or end of life has been reached").format(args.get("item_code")))

    item = item[0]
    item_group_defaults = get_item_group_defaults(item.name, self.company)
    brand_defaults = get_brand_defaults(item.name, self.company)

    ret = frappe._dict({
        'uom'			      	: item.stock_uom,
        'stock_uom'				: item.stock_uom,
        'description'		  	: item.description,
        'image'					: item.image,
        'item_name' 		  	: item.item_name,
        'cost_center'			: get_default_cost_center(args, item, item_group_defaults, brand_defaults, self.company),
        'qty'					: args.get("qty"),
        'transfer_qty'			: args.get('qty'),
        'conversion_factor'		: 1,
        'batch_no'				: '',
        'actual_qty'			: 0,
        'basic_rate'			: 0,
        'serial_no'				: '',
        'has_serial_no'			: item.has_serial_no,
        'has_batch_no'			: item.has_batch_no,
        'sample_quantity'		: item.sample_quantity
    })

    if self.purpose == 'Send to Subcontractor':
        ret["allow_alternative_item"] = item.allow_alternative_item

    # update uom
    if args.get("uom") and for_update:
        ret.update(get_uom_details(args.get('item_code'), args.get('uom'), args.get('qty')))

    if self.purpose == 'Material Issue':
        ret["expense_account"] = (item.get("expense_account") or
            item_group_defaults.get("expense_account") or
            frappe.get_cached_value('Company',  self.company,  "default_expense_account"))
        
        if self.stock_entry_reason:
            expense_account = frappe.db.get_value('Stock Entry Reason', self.stock_entry_reason, 'stock_adjustment_account')
            if expense_account:
                ret["expense_account"] = expense_account

    for company_field, field in {'stock_adjustment_account': 'expense_account',
        'cost_center': 'cost_center'}.items():
        if not ret.get(field):
            ret[field] = frappe.get_cached_value('Company',  self.company,  company_field)

    args['posting_date'] = self.posting_date
    args['posting_time'] = self.posting_time

    stock_and_rate = get_warehouse_details(args) if args.get('warehouse') else {}
    ret.update(stock_and_rate)

    # automatically select batch for outgoing item
    if (args.get('s_warehouse', None) and args.get('qty') and
        ret.get('has_batch_no') and not args.get('batch_no')):
        args.batch_no = get_batch_no(args['item_code'], args['s_warehouse'], args['qty'])

    return ret

@frappe.whitelist()
def customize_stock_entry(doc =None,method= None):
	from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
	StockEntry.get_item_details = get_item_details

@frappe.whitelist()
def get_expired_batch_items():
	return frappe.db.sql("""select b.item, sum(sle.actual_qty) as qty, sle.batch_no, sle.warehouse, sle.stock_uom\
	from `tabBatch` b, `tabStock Ledger Entry` sle
	where b.expiry_date <= %s
	and b.expiry_date is not NULL
	and b.batch_id = sle.batch_no
	group by sle.warehouse, sle.item_code, sle.batch_no""",(nowdate()), as_dict=1)

@frappe.whitelist()
def get_warehouse_details(args):
	if isinstance(args, string_types):
		args = json.loads(args)

	args = frappe._dict(args)

	ret = {}
	if args.warehouse and args.item_code:
		args.update({
			"posting_date": args.posting_date,
			"posting_time": args.posting_time,
		})
		ret = {
			"actual_qty" : get_previous_sle(args).get("qty_after_transaction") or 0,
			"basic_rate" : get_incoming_rate(args)
		}
	return ret

@frappe.whitelist()
def validate_sample_quantity(item_code, sample_quantity, qty, batch_no = None):
	if cint(qty) < cint(sample_quantity):
		frappe.throw(_("Sample quantity {0} cannot be more than received quantity {1}").format(sample_quantity, qty))
	retention_warehouse = frappe.db.get_single_value('Stock Settings', 'sample_retention_warehouse')
	retainted_qty = 0
	if batch_no:
		retainted_qty = get_batch_qty(batch_no, retention_warehouse, item_code)
	max_retain_qty = frappe.get_value('Item', item_code, 'sample_quantity')
	if retainted_qty >= max_retain_qty:
		frappe.msgprint(_("Maximum Samples - {0} have already been retained for Batch {1} and Item {2} in Batch {3}.").
			format(retainted_qty, batch_no, item_code, batch_no), alert=True)
		sample_quantity = 0
	qty_diff = max_retain_qty-retainted_qty
	if cint(sample_quantity) > cint(qty_diff):
		frappe.msgprint(_("Maximum Samples - {0} can be retained for Batch {1} and Item {2}.").
			format(max_retain_qty, batch_no, item_code), alert=True)
		sample_quantity = qty_diff
	return sample_quantity

@frappe.whitelist()
def get_uom_details(item_code, uom, qty):
	"""Returns dict `{"conversion_factor": [value], "transfer_qty": qty * [value]}`
	:param args: dict with `item_code`, `uom` and `qty`"""
	conversion_factor = get_conversion_factor(item_code, uom).get("conversion_factor")

	if not conversion_factor:
		frappe.msgprint(_("UOM coversion factor required for UOM: {0} in Item: {1}")
			.format(uom, item_code))
		ret = {'uom' : ''}
	else:
		ret = {
			'conversion_factor'		: flt(conversion_factor),
			'transfer_qty'			: flt(qty) * flt(conversion_factor)
		}
	return ret

@frappe.whitelist()
def edit_is_batch1():
    name = "8009632039510"
    from erpnext.stock.stock_ledger import get_previous_sle
    from datetime import date,datetime
    # ~ doc = frappe.get_doc("Item", name)
    # ~ doc.has_batch_no = 1
    # ~ doc.save()
    frappe.db.sql("update `tabItem` set has_batch_no=1 where name='{0}'".format(name))
    frappe.db.commit()
    
    # ~ check for default batch 
    batch_list = frappe.db.get_list("Batch",{'name':name+"-batch"})
    if not batch_list:
        batch = frappe.new_doc("Batch")
        batch.batch_id = name+"-batch"
        batch.item = name
        batch.save()
    
        frappe.db.sql("update `tabStock Ledger Entry` set batch_no='{0}' where item_code='{1}'".format(name+"-batch",name))
        frappe.db.commit()    
        
        res =  frappe.db.sql("select distinct warehouse from `tabStock Ledger Entry` where  batch_no='{0}' and item_code='{1}'".format(name+"-batch",name),as_list=1)
        print (res)
        
        for r in res :
            get_batches(name, r[0])
            
@frappe.whitelist()
def edit_is_batch(name):
    from erpnext.stock.stock_ledger import get_previous_sle
    from datetime import date,datetime
    # ~ doc = frappe.get_doc("Item", name)
    # ~ doc.has_batch_no = 1
    # ~ doc.save()
    frappe.db.sql("update `tabItem` set has_batch_no=1 where name='{0}'".format(name))
    frappe.db.commit()
    
    # ~ check for default batch 
    batch_list = frappe.db.get_list("Batch",{'name':name+"-batch"})
    if not batch_list:
        batch = frappe.new_doc("Batch")
        batch.batch_id = name+"-batch"
        batch.item = name
        batch.save()
    
        frappe.db.sql("update `tabStock Ledger Entry` set batch_no='{0}' where item_code='{1}'".format(name+"-batch",name))
        frappe.db.commit()    
        
        res =  frappe.db.sql("select distinct warehouse from `tabStock Ledger Entry` where  batch_no='{0}' and item_code='{1}'".format(name+"-batch",name),as_list=1)
        print (res)
        
        for r in res :
            get_batches(name, r[0])
            # ~ previous_sle = get_previous_sle({
                            # ~ "item_code": name,
                            # ~ "warehouse": r[0],
                            # ~ "posting_date": date.today(),
                            # ~ "posting_time": "12:00"
                        # ~ })

            # ~ doc = frappe.get_doc("Stock Ledger Entry",previous_sle.name)
            # ~ new_sle = frappe.copy_doc(doc)
            # ~ from pprint import pprint
            # ~ pprint(vars(new_sle))
            # ~ if new_sle.qty_after_transaction >0:
                # ~ new_sle.actual_qty = new_sle.qty_after_transaction
                # ~ new_sle.posting_date = date.today()
                # ~ new_sle.posting_time = "12:00"
                # ~ new_sle.warehouse = r[0]
                # ~ new_sle.voucher_type = "Batch"
                # ~ new_sle.voucher_no = name+"-batch"
                # ~ new_sle.voucher_detail_no = ""
                # ~ print(new_sle.warehouse)
                # ~ new_sle.insert(ignore_permissions=True)
                # ~ frappe.db.commit()
    
        
    return 'True'

def get_batches(item_code, warehouse, free_batch=True, throw=False):
    from customizer.tool import get_previous_sle
    from datetime import date,datetime
    cond = ''
    q ="""
        select batch_id, sum(`tabStock Ledger Entry`.actual_qty) as qty
        from `tabBatch`
			join `tabStock Ledger Entry` ignore index (item_code, warehouse)
				on (`tabBatch`.batch_id = `tabStock Ledger Entry`.batch_no )
		where `tabStock Ledger Entry`.item_code = %s and `tabStock Ledger Entry`.warehouse = %s
			and (`tabBatch`.expiry_date >= CURDATE() or `tabBatch`.expiry_date IS NULL) {0}
		group by batch_id
		{1}
	"""
    order_by = """order by `tabBatch`.expiry_date ASC,`tabBatch`.free_batch Desc ,`tabBatch`.manufacturing_date ASC, `tabBatch`.creation ASC"""
    if not free_batch :
        order_by = """order by `tabBatch`.expiry_date ASC,`tabBatch`.free_batch ASC ,`tabBatch`.manufacturing_date ASC, `tabBatch`.creation ASC"""
        # ~ cond += "and `tabBatch`.free_batch = 0"
    
    batches = frappe.db.sql(q.format(cond,order_by), (item_code, warehouse), as_dict=True)
    for b in batches :
        print(b)      
        previous_sle = get_previous_sle({
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "posting_date": date.today(),
                    "batch_no": b.batch_id,
                    "posting_time": "23:00"
                })
        
        doc = frappe.get_doc("Stock Ledger Entry",previous_sle.name)
        new_sle = frappe.copy_doc(doc)
        from pprint import pprint
        print ("qqqqqqqqqqqqqqqqqqqqqqq")
        print ("qqqqqqqqqqqqqqqqqqqqqqq")
        print ("qqqqqqqqqqqqqqqqqqqqqqq")
        print (warehouse)
        print (new_sle.actual_qty)
        print (new_sle.qty_after_transaction)
        print ("qqqqqqqqqqqqqqqqqqqqqqq")
        print ("qqqqqqqqqqqqqqqqqqqqqqq")
        print ("qqqqqqqqqqqqqqqqqqqqqqq")
        try :
            if new_sle.qty_after_transaction >0:
                new_sle.actual_qty = (b.qty*-1) + new_sle.qty_after_transaction
                new_sle.posting_date = date.today()
                new_sle.posting_time = "12:00"
                new_sle.warehouse = warehouse
                new_sle.voucher_type = "Batch"
                new_sle.voucher_no = item_code+"-batch"
                print(new_sle.warehouse)
                new_sle.insert(ignore_permissions=True)
                frappe.db.commit()
        except Exception as e: 
            pass
            
    return batches
    
@frappe.whitelist()
def edit_is_stock_item(name):
	frappe.db.sql("update `tabItem` set is_stock_item=1 where name='{0}'".format(name))
	frappe.db.commit()
    
    
def submit_stockre():
    doc=frappe.get_doc("Review Stock Reconciliation","REV-RECO-2020-00021")
    doc.submit()

@frappe.whitelist(allow_guest=True)
def edit_journal_entry(journal_name):
    doc = frappe.get_doc("Journal Entry", journal_name)
    doc.cancel()

    frappe.db.sql("update `tabJournal Entry` set docstatus=0 where name='{0}'".format(journal_name))
    return 'True'
    
@frappe.whitelist(allow_guest=True)
def edit_purchase_recipt(name):
    doc = frappe.get_doc("Purchase Receipt", name)
    doc.cancel()

    frappe.db.sql("update `tabPurchase Receipt` set docstatus=0 where name='{0}'".format(name))
    frappe.db.sql("update `tabPurchase Receipt Item` set docstatus=0 where parent='{0}'".format(name))
    frappe.db.sql("update `tabPurchase Taxes and Charges` set docstatus=0 where parent='{0}'".format(name))
    return 'True'


def set_pos_si_cost_center():
    si_list = frappe.db.get_list("Sales Invoice",filters={'is_pos':1,'docstatus':1},fields ={'name','pos_profile'})
    print (len(si_list))
    for si in si_list :
        pos_cost_center = frappe.db.get_value('POS Profile',si["pos_profile"], 'cost_center')
        print(si["pos_profile"])
        print(pos_cost_center)

        if pos_cost_center:
            gl_list = frappe.db.get_list("GL Entry",filters={'voucher_no':si["name"]},fields={'name','cost_center'})
            for g in gl_list:
                if g["cost_center"]:
                    print(g)
                    frappe.db.set_value('GL Entry',g["name"], 'cost_center', pos_cost_center)
                    frappe.db.commit()
            items_list = frappe.db.get_list("Sales Invoice Item",filters={'parent':si["name"]},fields={'name','cost_center'})
            for i in items_list :
                frappe.db.set_value('Sales Invoice Item',i["name"], 'cost_center', pos_cost_center)
                frappe.db.commit() 

            print("1111111111111111111111")
            print(si)
            print(len(gl_list))
            print("1111111111111111111111")
        
        
@frappe.whitelist()
def check_free_item_eligibility(sales_invoice_name, is_pos=0):
    sales_invoice = frappe.get_doc('Sales Invoice', sales_invoice_name)
    free_items_map = {}  
    show_message = True  

    for item in sales_invoice.items:
        free_item = frappe.get_all('Free Items', filters={'item_code': item.item_code, 'enabled': 1})

        if not free_item:
            continue

        free_item_doc = frappe.get_doc('Free Items', free_item[0].name)
        item.total_qty = item.qty  

        if free_item_doc.item_code in free_items_map:
            free_items_map[free_item_doc.item_code] += item.qty
        else:
            free_items_map[free_item_doc.item_code] = item.qty

        item.is_free_items = 1 

    for item_code, total_qty in free_items_map.items():
        customer_free_items = frappe.get_all(
            'Customers Free Items',
            filters={'customer': sales_invoice.customer, 'item_code': item_code}
        )

        if customer_free_items:
            customer_free_item = frappe.get_doc('Customers Free Items', customer_free_items[0].name)

            if customer_free_item.status != 'Completed':
                matching_item = next(
                    (fci for fci in customer_free_item.free_customer_items if fci.ref_invoice == sales_invoice.name),
                    None
                )

                if matching_item:
                    matching_item.total_qty = total_qty
                    matching_item.ref_invoice = sales_invoice.name
                else:
                    customer_free_item.append('free_customer_items', {
                        'posting_date': sales_invoice.posting_date,
                        'item_code': item_code,
                        'total_qty': total_qty,
                        'ref_invoice': sales_invoice.name
                    })

                customer_free_item.save()
             
                # Check if it's a free invoice or discount applied and disable showing the message
                if sales_invoice.is_return == 1 or sales_invoice.additional_discount_percentage > 0 or is_pos:
                    show_message = False
        else:
            customer_free_items = frappe.new_doc('Customers Free Items')
            customer_free_items.customer = sales_invoice.customer
            customer_free_items.status = 'Pending'
            customer_free_items.append('free_customer_items', {
                'posting_date': sales_invoice.posting_date,
                'item_code': item_code,
                'total_qty': total_qty,
                'ref_invoice': sales_invoice.name
            })
            customer_free_items.insert()

    # Query to check if total_qty in Customers Free Items matches total_qty in Free Items
    query = '''
        SELECT fci.item_code, SUM(fci.total_qty) AS total_qty, cfi.status
        FROM `tabCustomers Free Items` AS cfi
        LEFT JOIN `tabFree Customer Items` AS fci ON cfi.name = fci.parent
        WHERE cfi.customer = %(customer)s
        GROUP BY fci.item_code
    '''

    customer_free_items = frappe.db.sql(query, {'customer': sales_invoice.customer}, as_dict=True)
    
    for cfi in customer_free_items:
        free_item = frappe.get_doc('Free Items', {'item_code': cfi.item_code, 'enabled': 1})
        if free_item and cfi.total_qty >= free_item.total_qty and cfi.status != "Completed":
            customer_name = frappe.get_value('Customer', sales_invoice.customer, 'customer_name')
            frappe.msgprint(f"Customer {customer_name} has free items for {cfi.item_code}")

    return None
  



@frappe.whitelist()
def fetch_conversion_factor(item_code, uom):
    conversion_factor = None

    # Get database connection
    db = get_db()

    # Fetch data from the Item's child table based on the selected UOM using SQL query with join
    query = """
        SELECT uoms.conversion_factor
        FROM `tabItem` items
        JOIN `tabUOM Conversion Detail` uoms ON items.name = uoms.parent
        WHERE items.item_code = %s AND uoms.uom = %s
        LIMIT 1
    """
    result = db.sql(query, (item_code, uom))

    if result:
        conversion_factor = result[0][0]

    return {"conversion_factor": conversion_factor}



def reset_bin():
    items = [
        "3336024827123", "3336024827727", "3336024827741", "3336024827772", "3336025821533",
        "4002064400167", "4002064400693", "4002064400716", "4002064400723", "4002064400730",
        "4002064400747", "4002064406756", "4002064409139", "4002064413099-old", "4002064413143",
        "4002064418285", "4002064419367", "4002064419435", "4002064420523", "4002064420530",
        "4002064420561", "4002064420578", "4002064420707", "4002064420721", "4002064420745",
        "4002064500119", "4002064500126", "4002064500188", "4002064507859", "4002064507873",
        "4002064507897", "4002064514444", "4002064514468", "4002064514482", "4002064514604",
        "4002064514611", "4002064514628", "4002064514635", "4002064514642", "4002064514666",
        "4002064541747", "4008239108692", "4008239209917-oldba", "4008239212375", "4008239240033",
        "4008239241900", "4008239241924", "4008239288073-old", "4008239288080-old", "4008239288219",
        "4008239288226", "4008239313348", "4008239313362", "4008239313379", "4008239315311",
        "4008239366627", "4008239366641", "4008239366658", "4008239366672", "4008239366689",
        "4008239366696", "5023861000809", "5023861111512", "5023861112311", "5023861115589",
        "5023861116418", "5023861116777", "5023861118498", "5023861118511", "5023861118535",
        "6970569710235", "8007520011105", "8009632015712", "8009632015736", "8034105420991",
        "8034105424067", "8595602503223", "9557193060294", "9557193060355", "98371"
    ]
    
    for item_code in items:
        try:
            item = frappe.get_doc("Item", item_code)
            item.recalculate_bin_qty(item.name)
            print(f"Done recalculating for item: {item_code}")
        except Exception as e:
            print(f"Error processing item {item_code}: {e}")


import frappe

def reset_bin2():
    items = [
        "067714102222", "067714102239", "067714102253", "067714102307", "067714102338", "067714102376",
        "067714102413", "067714102420", "067714102451", "067714102499", "067714102505", "067714102536",
        "067714102543", "067714102550", "067714102567", "067714102598", "067714102604", "067714102611",
        "067714102628", "067714102635", "067714102697", "067714102703", "067714102727", "067714102734",
        "067714102741", "067714102758", "067714102772", "067714102789", "067714102819", "067714102826",
        "067714102833", "067714102840", "3182550702423", "3182550702973", "3182550707312", "3182550721745",
        "4002064205069", "4002064205090", "4002064205113", "4002064205151", "4002064205168", "4002064400174",
        "4002064400693", "4002064400716", "4002064400723", "4002064400747", "4002064401065", "4002064401362",
        "4002064401393", "4002064401423", "4002064401874", "4002064401881", "4002064402109", "4002064406213",
        "4002064406268", "4002064406282", "4002064406527", "4002064406787", "4002064407364", "4002064407517",
        "4002064407630", "4002064409139", "4002064409436", "4002064412887", "4002064412900", "4002064412917",
        "4002064412948", "4002064412962", "4002064412979", "4002064413082", "4002064413099", "4002064413105",
        "4002064413112", "4002064413129", "4002064413143", "4002064413266", "4002064413273", "4002064414508",
        "4002064414515", "4002064418742", "4002064418759", "4002064419374", "4002064419435", "4002064420448",
        "4002064420530", "4002064420707", "4002064421353", "4002064421698", "4002064426174", "4002064427065",
        "4002064500126", "4002064507873", "4002064507897", "4002064513003", "4002064513041", "4002064513065",
        "4002064514482", "4002064541747", "4008239113467", "4008239207807", "4008239210036", "4008239210470",
        "4008239212375", "4008239212450", "4008239212887", "4008239212948", "4008239212962", "4008239214508",
        "4008239216410", "4008239216434", "4008239223050", "4008239223067", "4008239240033", "4008239241900",
        "4008239241924", "4008239250377", "4008239252272", "4008239255426", "4008239255846", "4008239288073-old",
        "4008239288080-old", "4008239292193", "4008239366627", "4008239366658", "4008239366689", "5011792007653",
        "5023861000403", "5023861000809", "5023861001905", "5023861114926", "5023861118474", "5023861118498",
        "5023861118535", "5023861118559", "5023861119945", "5023861120163", "5400274984139", "5411290164634",
        "5904479711007", "5904479711021", "5904479712073", "5904479712615", "5904479722003", "5904479722027",
        "5904479725004", "5904479726025", "6281000015056", "6287005810016", "653945454652", "653945454676",
        "653945454683", "653945454713", "6938104000814", "6938104040469", "6938104040575", "6953182743316",
        "6953182743323", "6970569710235", "8023222044074", "8023222050242", "8023222060876", "8023222060890",
        "8023222129863", "8034105420700", "8034105420953", "8034105420991", "8034105422506", "8034105422520",
        "8034105422599", "8034105422704", "8034105422902", "8034105424067", "8437017247364", "8437017247449",
        "8437021952063", "8595602503223", "8595602526338", "8906074443557", "9003579000410", "9003579308943",
        "9003579311301"
    ]
    
    for item_code in items:
        try:
            item = frappe.get_doc("Item", item_code)
            item.recalculate_bin_qty(item.name)
            print(f"Done recalculating for item: {item_code}")
        except Exception as e:
            print(f"Error processing item {item_code}: {e}")

# Run the function
reset_bin()
