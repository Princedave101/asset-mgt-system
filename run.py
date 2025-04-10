import os
import click
from flask_migrate import Migrate
from app import create_app, db
from app.models import Role, Employee, Department, Asset, AssetAssignment, AssetRequest, Item, StockInventory

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Emp=Employee, Role=Role, Dept=Department, Asset=Asset, AR=AssetRequest, AA=AssetAssignment, Item=Item,StockInventory=StockInventory,
                r=Role(name="Admin"),
                d=Department(name="IT", location="Old yaba"),
                e1=Employee(email="dpokeke@gmail.com", password="jesus", username="david"),
                e2=Employee(email="pdokeke07@gmail.com", password="jesus", username="Alex", confirmed=True))

@app.cli.command()
@click.argument('test_names', nargs=-1)
def test(test_names):
    """Run the unit tests."""
    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)