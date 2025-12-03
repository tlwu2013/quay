import sys
import os
sys.path.append(os.getcwd())
from data import model
from app import app
from data.database import User

with app.app_context():
    print([(u.username, u.organization, u.robot) for u in User.select()])

