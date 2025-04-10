import os
from flask import Blueprint
from .hr import hr as hr_blueprint
from .manager import mg as manager_blueprint

template_basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

main = Blueprint('main', __name__, template_folder=f"{template_basedir}\\templates\\dashboard\\employee")

from . import views, errors
from ..models import Task

main.register_blueprint(hr_blueprint)
main.register_blueprint(manager_blueprint)

@main.app_context_processor
def inject_permissions():
   return dict(Task=Task)


