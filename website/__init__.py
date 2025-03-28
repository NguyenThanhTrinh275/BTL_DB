from flask import Flask

app = Flask(__name__, 
            template_folder='templates', 
            static_folder='static')

# Import routes từ views.py
from website import views