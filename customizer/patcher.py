import frappe
from frappe.desk.doctype.notification_settings.notification_settings import create_notification_settings

def create_notification_settings_for_all_users():
    # Fetch all user emails
    users = frappe.get_all('User', filters={'enabled': 1}, fields=['name'])
    
    for user in users:
        user_email = user['name']
        try:
            # Create notification settings for each user
            create_notification_settings(user_email)
            frappe.db.commit()
            print(f"Notification settings created for user: {user_email}")
        except Exception as e:
            print(f"Failed to create notification settings for user: {user_email} - {e}")
