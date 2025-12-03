import sys
import os
sys.path.append(os.getcwd())
from data import model
from app import app

with app.app_context():
    user = model.user.get_nonrobot_user('testadmin')
    if user:
        print("User testadmin exists")
    else:
        print("User testadmin DOES NOT exist")

