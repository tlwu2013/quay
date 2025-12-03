import sys
import os

sys.path.append(os.getcwd())

from data import model
from app import app

with app.app_context():
    orgname = 'testorg'
    robot_shortname = 'mirrorbot'

    try:
        org = model.organization.get_organization(orgname)
        if not org:
             print(f"Org {orgname} not found")
             exit(1)
        
        # Check if robot exists
        robot_username = f"{orgname}+{robot_shortname}"
        try:
            existing = model.user.lookup_robot(robot_username)
            print(f"Robot {robot_username} already exists.")
        except:
            print(f"Creating robot {robot_shortname} for {orgname}...")
            robot, password = model.user.create_robot(robot_shortname, org)
            print(f"Robot {robot.username} created with password: {password}")

    except Exception as e:
        print(f"Error creating robot: {e}")

