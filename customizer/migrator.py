import frappe

def fetch_and_dump_doctypes_with_children_into_one_file(module_name=None):
    filters = {'istable': 0, 'issingle': 0}  # Focus on parent Doctypes that are not Single
    if module_name:
        filters['module'] = module_name

    all_doctypes = frappe.get_all('DocType', filters=filters, fields=['name', 'module'])
    table_names_set = set()  # Use a set to store unique table names

    for doctype in all_doctypes:
        # Add parent doctype with 'tab' prefix to the set
        table_names_set.add('tab' + doctype['name'])
        # Fetch child tables and add them with 'tab' prefix to the set
        child_tables = frappe.get_all('DocField', filters={'parent': doctype['name'], 'fieldtype': 'Table'}, fields=['options'])
        for child in child_tables:
            table_names_set.add('tab' + child['options'])

    # Convert the set of table names into a string, each name quoted
    table_names_str = ' '.join([f"'{name}'" for name in table_names_set])

    # Prepare the mysqldump command
    command = f"mysqldump --no-defaults -u root -p --no-create-info _109f4b3c50d7b0df {table_names_str} > 'data/{module_name if module_name else 'all_modules'}_backup.sql'"

    # Print the generated command; sensitive information like passwords should be handled securely
    print(f"Command generated for module: {module_name if module_name else 'all_modules'}")
    # Uncomment the next line if you want to see the command or execute it manually.
    # Be cautious with sensitive data.
    print(command)

# Example call to the function
# fetch_and_dump_doctypes_with_children_into_one_file('Accounts')

