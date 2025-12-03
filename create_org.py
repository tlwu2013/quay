import sys
import os

sys.path.append(os.getcwd())

from data import model
from app import app

with app.app_context():
    username = 'testadmin'
    orgname = 'testorg'
    email = 'testorg@example.com'

    try:
        user = model.user.get_nonrobot_user(username)
        if not user:
            print(f"User {username} not found. Please run create_user.py first.")
            exit(1)

        # Check if org exists
        existing = model.user.get_nonrobot_user(orgname)
        if existing:
            print(f"Organization {orgname} already exists.")
        else:
            print(f"Creating organization {orgname}...")
            org = model.organization.create_organization(orgname, email, user)
            print(f"Organization {orgname} created with ID {org.id}")

    except Exception as e:
        print(f"Error creating org: {e}")

