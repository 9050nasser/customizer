# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.utils.nestedset import get_root_of
from frappe.utils import cint,today
from erpnext.accounts.doctype.pos_profile.pos_profile import get_item_groups

from six import string_types

@frappe.whitelist()
def get_coupon_code(coupon_code=None):
	if coupon_code:
		pricing_rule = frappe.db.get_value('Coupon Code', {'name': coupon_code}, ['pricing_rule'], as_dict=True)
		if pricing_rule:
			doc = frappe.get_doc("Pricing Rule",pricing_rule["pricing_rule"])
			return {"discount_percentage":doc.discount_percentage,"apply_discount_on":doc.apply_discount_on}
	
	
@frappe.whitelist()
def get_coupon_code_doc(coupon_code=None):
	if coupon_code:
		cdoc = frappe.db.get_value('Coupon Code', {'coupon_code': coupon_code}, ['name'], as_dict=True)
		if cdoc:
			return {"coupon_code":cdoc["name"]}
		else :
			return {"error":"bad code name"}
	else :
		return {"error":"no code name"}
	
	
	
@frappe.whitelist()
def get_items(start, page_length, price_list, item_group, search_value="", pos_profile=None ,strict =0 ):
	data = dict()
	warehouse = ""
	display_items_in_stock = 0

	if pos_profile:
		warehouse, display_items_in_stock,auto_select_batch = frappe.db.get_value('POS Profile', pos_profile, ['warehouse', 'display_items_in_stock','auto_select_batch'])

	if not frappe.db.exists('Item Group', item_group):
		item_group = get_root_of('Item Group')

	if search_value:
		data = search_serial_or_batch_or_barcode_number(search_value,strict)
	item_code = data.get("item_code") if data.get("item_code") else search_value
	serial_no = data.get("serial_no") if data.get("serial_no") else ""
	if not auto_select_batch:
		batch_no = data.get("batch_no") if data.get("batch_no") else ""
	else:
		batch_no = ""
	barcode = data.get("barcode") if data.get("barcode") else ""

	condition = get_conditions(item_code, serial_no, batch_no, barcode)

	if pos_profile:
		condition += get_item_group_condition(pos_profile)

	lft, rgt = frappe.db.get_value('Item Group', item_group, ['lft', 'rgt'])
	# locate function is used to sort by closest match from the beginning of the value

	result = []

	items_data = frappe.db.sql("""
		SELECT
			name AS item_code,
			item_name,
			stock_uom,
			image AS item_image,
			idx AS idx,
			is_stock_item
		FROM
			`tabItem`
		WHERE
			disabled = 0
				AND has_variants = 0
				AND is_sales_item = 1
				AND item_group in (SELECT name FROM `tabItem Group` WHERE lft >= {lft} AND rgt <= {rgt})
				AND {condition}
		ORDER BY
			idx desc
		LIMIT
			{start}, {page_length}"""
		.format(
			start=start,
			page_length=page_length,
			lft=lft,
			rgt=rgt,
			condition=condition
		), as_dict=1)

	if items_data:
		items = [d.item_code for d in items_data]
		item_prices_data = frappe.get_all("Item Price",
			fields = ["item_code", "price_list_rate", "currency"],
			filters = {'price_list': price_list, 'item_code': ['in', items]})
		
		item_prices, bin_data = {}, {}
		for d in item_prices_data:
			# ~ item_prices[d.item_code] = d
			item_args = {'item_code': d.item_code, 'price_list': price_list,'uom':d.stock_uom, 'transaction_date': today()}
			item_prices[d.item_code] = get_price_list_rate_for(d.item_code, price_list,d.stock_uom, today())

		# prepare filter for bin query
		bin_filters = {'item_code': ['in', items]}
		if warehouse:
			bin_filters['warehouse'] = warehouse
		if display_items_in_stock:
			bin_filters['actual_qty'] = [">", 0]

		# query item bin
		bin_data = frappe.get_all(
			'Bin', fields=['item_code', 'sum(actual_qty) as actual_qty'],
			filters=bin_filters, group_by='item_code'
		)

		# convert list of dict into dict as {item_code: actual_qty}
		bin_dict = {}
		for b in bin_data:
			bin_dict[b.get('item_code')] = b.get('actual_qty')

		for item in items_data:
			item_code = item.item_code
			item_price = item_prices.get(item_code) or {}
			item_stock_qty = bin_dict.get(item_code)

			if display_items_in_stock and not item_stock_qty:
				pass
			else:
				row = {}
				row.update(item)
				row.update({
					'price_list_rate': item_price.get('price_list_rate'),
					'currency': item_price.get('currency'),
					'actual_qty': item_stock_qty,
				})
				result.append(row)

	res = {
		'items': result
	}

	if serial_no:
		res.update({
			'serial_no': serial_no
		})

	if batch_no :
		res.update({
			'batch_no': batch_no
		})

	if barcode:
		res.update({
			'barcode': barcode
		})

	return res

@frappe.whitelist()
def search_serial_or_batch_or_barcode_number(search_value,strict = 0):
	if int(strict) == 1:
		item_code = frappe.db.get_value('Item', {'name': search_value,'has_batch_no':0,	'has_serial_no':0}, [ 'name as barcode','name as item_code'], as_dict=True)
		if item_code:
			return item_code

	# search barcode no
	barcode_data = frappe.db.get_value('Item Barcode', {'barcode': search_value}, ['barcode', 'parent as item_code'], as_dict=True)
	if barcode_data:
		return barcode_data

	# search serial no
	serial_no_data = frappe.db.get_value('Serial No', search_value, ['name as serial_no', 'item_code'], as_dict=True)
	if serial_no_data:
		return serial_no_data

	# search batch no
	batch_no_data = frappe.db.get_value('Batch', search_value, ['name as batch_no', 'item as item_code'], as_dict=True)
	if batch_no_data:
		return batch_no_data

	return {}

def get_conditions(item_code, serial_no, batch_no, barcode):
	if serial_no or batch_no or barcode:
		return "name = {0}".format(frappe.db.escape(item_code))

	return """(name like {item_code}
		or item_name = {item_code})""".format(item_code = frappe.db.escape('%' + item_code + '%'))

def get_item_group_condition(pos_profile):
	cond = "and 1=1"
	item_groups = get_item_groups(pos_profile)
	if item_groups:
		cond = "and item_group in (%s)"%(', '.join(['%s']*len(item_groups)))

	return cond % tuple(item_groups)

def item_group_query(doctype, txt, searchfield, start, page_len, filters):
	item_groups = []
	cond = "1=1"
	pos_profile= filters.get('pos_profile')

	if pos_profile:
		item_groups = get_item_groups(pos_profile)

		if item_groups:
			cond = "name in (%s)"%(', '.join(['%s']*len(item_groups)))
			cond = cond % tuple(item_groups)

	return frappe.db.sql(""" select distinct name from `tabItem Group`
			where {condition} and (name like %(txt)s) limit {start}, {page_len}"""
		.format(condition = cond, start=start, page_len= page_len),
			{'txt': '%%%s%%' % txt})


@frappe.whitelist()
def get_loyalty_program_details(customer, loyalty_program=None, expiry_date=None, company=None, silent=False, include_expired_entry=False):
	from frappe.desk.treeview import get_children
	lp_details = frappe._dict()
	programs = []
	if not loyalty_program:
		loyalty_program = frappe.db.get_value("Customer", customer, "loyalty_program")

		if not (loyalty_program or silent):
			frappe.throw(_("Customer isn't enrolled in any Loyalty Program"))
		elif silent and not loyalty_program:
				loyalty_programs = frappe.get_all("Loyalty Program",
					fields=["name", "customer_group", "customer_territory"],
					filters={"auto_opt_in": 1, "from_date": ["<=", today()],
						"ifnull(to_date, '2500-01-01')": [">=", today()]})
				for loyalty_program in loyalty_programs:
					customer_groups = [d.value for d in get_children("Customer Group", loyalty_program.customer_group)] + [loyalty_program.customer_group]
					customer_territories = [d.value for d in get_children("Territory", loyalty_program.customer_territory)] + [loyalty_program.customer_territory]
					doc = frappe.get_doc("Customer",customer)
					if (not loyalty_program.customer_group or doc.customer_group in customer_groups)\
						and (not loyalty_program.customer_territory or doc.territory in customer_territories):
						programs.append(loyalty_program.name)
				if not programs: return
				if len(programs) == 1:
					loyalty_program= programs[0]
				else:
					frappe.msgprint(_("Multiple Loyalty Program found for the Customer. Please select manually."))
				
			

	if not company:
		company = frappe.db.get_default("company") or frappe.get_all("Company")[0].name

	loyalty_program = frappe.get_doc("Loyalty Program", loyalty_program)
	lp_details.update({"loyalty_program": loyalty_program.name})
	lp_details.update(loyalty_program.as_dict())
	return lp_details


@frappe.whitelist()
def get_loyalty_program_details_with_points(customer, loyalty_program=None, expiry_date=None, company=None, silent=False, include_expired_entry=False, current_transaction_amount=0):
	from frappe.utils import  getdate
	from erpnext.accounts.doctype.loyalty_program.loyalty_program import \
		get_loyalty_program_details_with_points, get_loyalty_details, validate_loyalty_points
	
	lp_details = get_loyalty_program_details(customer, loyalty_program, company=company, silent=silent)
	if lp_details:
		loyalty_program = frappe.get_doc("Loyalty Program", lp_details.loyalty_program)
		loyalty_point_details = frappe._dict(frappe.get_all("Loyalty Point Entry",
				filters={
					'customer': customer,
					'expiry_date': ('>=', getdate()),
					'company': company,
					},
					group_by="company",
					fields=["company", "sum(loyalty_points) as loyalty_points"],
					as_list =1
				))
		loyalty_points = loyalty_point_details.get(company)
		
		lp_details.update(get_loyalty_details(customer, loyalty_program.name, expiry_date, company, include_expired_entry))
		lp_details.update({"loyalty_points":loyalty_points})
		# sort collection rule, first item on list will be lowest min_spent 
		tier_spent_level = sorted(
			[d.as_dict() for d in loyalty_program.collection_rules],
			key=lambda rule: rule.min_spent, reverse=False,
		)

		# looping and apply tier from lowest min_spent
		for i, d in enumerate(tier_spent_level):
			# if cumulative spend more than min_spent then continue to next tier
			if (lp_details.total_spent + current_transaction_amount) >= d.min_spent:
				lp_details.tier_name = d.tier_name
				lp_details.collection_factor = d.collection_factor
			else:
				break
		return lp_details
	return


def get_item_price(args, item_code, ignore_party=True):
	"""
		Get name, price_list_rate from Item Price based on conditions
			Check if the desired qty is within the increment of the packing list.
		:param args: dict (or frappe._dict) with mandatory fields price_list, uom
			optional fields transaction_date, customer, supplier
		:param item_code: str, Item Doctype field item_code
	"""

	args['item_code'] = item_code

	conditions = """where item_code=%(item_code)s
		and price_list=%(price_list)s"""

	if not ignore_party:
		if args.get("customer"):
			conditions += " and customer=%(customer)s"
		elif args.get("supplier"):
			conditions += " and supplier=%(supplier)s"
		else:
			conditions += " and (customer is null or customer = '') and (supplier is null or supplier = '')"

	if args.get('transaction_date'):
		conditions += """ and %(transaction_date)s between
			ifnull(valid_from, '2000-01-01') and ifnull(valid_upto, '2500-12-31')"""
	q = """ select name, price_list_rate, uom
		from `tabItem Price` {conditions}
		order by valid_from desc, uom desc """.format(conditions=conditions)
	
	return frappe.db.sql(q, args)


def get_price_list_rate_for(item_code,price_list,uom,transaction_date):
	"""
		:param customer: link to Customer DocType
		:param supplier: link to Supplier DocType
		:param price_list: str (Standard Buying or Standard Selling)
		:param item_code: str, Item Doctype field item_code
		:param qty: Desired Qty
		:param transaction_date: Date of the price
	"""
	# ~ {'item_code': '1220', 'price_list': 'Standard Selling', 'customer': 'Retail Customer', 'supplier': None, 'uom': 'Nos', 'transaction_date': None}

	item_price_args = {
			"item_code": item_code,
			"price_list": price_list,
			"uom": uom,
			"transaction_date": transaction_date,
	}
	item_price_data = 0
	price_list_rate = get_item_price(item_price_args, item_code)


	general_price_list_rate = get_item_price(item_price_args, item_code,
		ignore_party=True)
	if general_price_list_rate:
		item_price_data = general_price_list_rate

	if item_price_data:
		if item_price_data[0][2] == uom:
			return {'price_list_rate':item_price_data[0][1]}
		else:
			return {'price_list_rate':item_price_data[0][1]}

