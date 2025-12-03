import sys
import os

# Add the current directory to sys.path so we can import modules
sys.path.append(os.getcwd())

from data import model
from app import app
from data.database import User

# Need to ensure we are in the right directory or PYTHONPATH is set, 
# but since this runs in the container where /quay-registry is the WORKDIR, 
# and . is in PYTHONPATH (usually), it should work.

with app.app_context():
    username = 'testadmin'
    password = 'password123'
    email = 'testadmin@example.com'

    try:
        # Check if user exists
        existing = model.user.get_nonrobot_user(username)
        if existing:
            print(f"User {username} already exists.")
        else:
            print(f"Attempting to create user {username}...")
            user = model.user.create_user(username, password, email, auto_verify=True)
            print(f"User {username} created with ID {user.id}")
            
            # Make superuser if needed (though usually manual DB update or config is needed for SUPER_USERS list)
            # But for now just having a user is enough to log in.
            # To verify if it's a superuser, we usually check config['SUPER_USERS']
            
    except Exception as e:
        print(f"Error creating user: {e}")

