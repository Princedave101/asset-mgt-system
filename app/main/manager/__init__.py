import os
from datetime import datetime
from flask import Blueprint, render_template, url_for, flash, redirect
from ...models import AssetRequest, AssetAssignment
from app import db

template_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

mg = Blueprint('mg', __name__, template_folder=template_path+"/templates/dashboard/employee", url_prefix="/manager")

from . import views
