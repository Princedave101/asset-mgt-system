import os
from flask import Blueprint

template_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

hr = Blueprint('hr', __name__, template_folder=template_path+"\\templates\\dashboard", url_prefix="/hr")

from . import views