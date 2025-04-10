from datetime import datetime
import random
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from sqlalchemy import event
from flask_login import UserMixin
from . import db, loginManager


class AssetRequest(db.Model):
    __tablename__ = "AssetRequest"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('Employee.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50), default="Pending")  # Pending, Canceled, Approved, Declined
    decision_date = db.Column(db.DateTime)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    forwarded = db.Column(db.Boolean, nullable=False, default=False) # forwarded yes , or no
    item_id = db.Column(db.Integer, db.ForeignKey("Item.id"), nullable=True)


class AssetAssignment(db.Model):
    __tablename__ = "AssetAssignment"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('Employee.id'), nullable=False) 
    quantity = db.Column(db.Integer, nullable=False, default=1)
    assigned_date = db.Column(db.DateTime, default=datetime.now)
    return_date = db.Column(db.DateTime, nullable=True)  # If employee resigns
    status = db.Column(db.String(50), default="Active")  # Active, Returned
    item_id = db.Column(db.Integer, db.ForeignKey('Item.id'), nullable=False)


class Asset(db.Model):
    __tablename__ = "Asset"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)  # IT Equipment, Furniture, etc.
    description = db.Column(db.Text)
    
    # Relationship to items
    items = db.relationship('Item', backref='asset', lazy="dynamic")

    @staticmethod
    def insert_assets():
        options = ["Electrical and Electronics Devices", "IT Equipment", "Furnitures", "Transportation"]

        for asset_name in options:
            asset = Asset.query.filter_by(name=asset_name).first()
            if not asset:
                asset = Asset(name=asset_name)
                db.session.add(asset)
        db.session.commit()
    
    def __repr__(self):
        return '<Asset %r>' % self.name


class Item(db.Model):
    __tablename__ = "Item"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Laptop, Scanner, Chair, etc.
    serial_number = db.Column(db.String(100), unique=True)
    purchase_date = db.Column(db.Date)
    status = db.Column(db.String(50), default="Available")  # Available, Assigned, Retired
    condition = db.Column(db.String(50), default="Good")  # Good, Needs Repair, Bad
    asset_id = db.Column(db.Integer, db.ForeignKey('Asset.id'), nullable=False)

    requests = db.relationship("AssetRequest", backref="item", lazy=True)  # One item can have many requests
    asset_assignments = db.relationship("AssetAssignment", backref="item", lazy=True)  # Corrected

    @staticmethod
    def generate_serial_number(mapper, connection, target):
        """Generates a unique serial number before inserting into the database."""
        if not target.serial_number:
            date_str = datetime.now().strftime("%Y%m%d")  # Get current date as YYYYMMDD
            last_item = db.session.query(Item).filter_by(asset_id=target.asset_id).order_by(Item.id.desc()).first()
            last_count = int(last_item.serial_number.split("-")[-1]) + 1 if last_item else 1
            asset_type_code = target.name.upper().replace(" ", "")[:6]  # First 6 letters of asset name
            target.serial_number = f"{asset_type_code}-{date_str}-{last_count:03d}"  # Format: TYPE-YYYYMMDD-XXX


    @staticmethod
    def insert_items():
        options = {"Electrical and Electronics Devices":["Telephone", "Projectors", "Air Conditioners", "CCTV Cameras"],
                   "IT Equipment":["Laptop", "Monitors", "Keyboards", "Routers", "Harddisk", "Printer"], 
                   "Furnitures":["Conference Tables", "Office Chairs", "Cabinets", "Cubicles"], 
                   "Transportation":["Company Cars", "Delivery Vans", "Bicycles"]
                   }

        for asset_type in options:
            asset = Asset.query.filter_by(name=asset_type).first()
            if asset:
                for items_name in options[asset_type]:
                    items = Item(name=items_name, asset=asset)
                    db.session.add(items)
                db.session.add(asset)
        db.session.commit()
    
    def __repr__(self):
        return '<Item %r>' % self.name
event.listen(Item, "before_insert", Item.generate_serial_number)

class StockInventory(db.Model):
    __tablename__ = "stock_inventory"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("Item.id"), nullable=False, unique=True)
    total_quantity = db.Column(db.Integer, nullable=False, default=0)  # Total items purchased
    available_quantity = db.Column(db.Integer, nullable=False, default=0)  # Items left for assignment

    # Relationship
    item = db.relationship("Item", backref=db.backref("stock", uselist=False))

    @staticmethod
    def stock_inventory():
        items=Item.query.all()
        for item in items:
            total_available = random.randint(1, 30)
            stock=StockInventory(total_quantity=total_available, 
                           available_quantity=total_available,
                           item = item
                           )
            db.session.add(stock)
        db.session.commit()
    
    def can_assign_item(self, quantity):
        if self.available_quantity >= quantity:
            self.available_quantity-=quantity
            return True
        return False
        

    def __repr__(self):
        return f'<StockInventory {self.item.name} - {self.available_quantity} left>'


class Task:
    REQUEST_ASSET=1  
    TRACK_REQUEST=2
    TRACK_ASSIGNMENT=4
    MANAGE_EMPLOYEE=8
    SET_REQUEST_STATUS=16 


class Employee(UserMixin, db.Model):
    __tablename__ = 'Employee'
    id = db.Column(db.Integer, primary_key=True)
    employee_number = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, index=True, nullable=False)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime, default=datetime.now)
    fullname = db.Column(db.String(64))
    location = db.Column(db.String(64))
    job_description = db.Column(db.Text())
    last_seen = db.Column(db.DateTime(), default=datetime.now)
    avatar_hash = db.Column(db.String(32))
    role_id = db.Column(db.Integer, db.ForeignKey('Role.id'))
    dept_id = db.Column(db.Integer, db.ForeignKey('Department.id'))
    requests = db.relationship('AssetRequest', foreign_keys=[AssetRequest.employee_id], backref='employee', lazy=True)
    assets = db.relationship('AssetAssignment', foreign_keys=[AssetAssignment.employee_id], backref='employee', lazy=True)

    def __init__(self, **kwargs):
        super(Employee, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['APP_MANAGER']:
                self.role = Role.query.filter_by(name='Manager').first()
                self.confirmed=True
            elif self.email == current_app.config['APP_HR']:
                self.role = Role.query.filter_by(name='HR').first()
                self.confirmed=True
            else:
                self.role = Role.query.filter_by(name='Employee').first()

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

        
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'confirm': self.id})

    def confirm(self, token, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expiration)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'reset': self.id})

    @staticmethod
    def reset_password(token, new_password, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expiration)
        except:
            return False
        user = Employee.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True
    
    def generate_email_change_token(self, new_email):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email})
    
    def change_email(self, token, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, max_age=expiration)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True
    
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_hr(self):
        return self.can(14)
    
    def is_manager(self):
        return self.can(16)

    def ping(self):
        self.last_seen = datetime.now()
        db.session.add(self)

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @staticmethod
    def generate_employee_number(mapper, connection, target):
        if not target.employee_number:
            date_str = datetime.now().strftime("%Y")
            last_employee_id = 0 if len(db.session.query(Employee).filter_by(dept=target.dept).all())==0 else db.session.query(Employee).filter_by(dept=target.dept).all()[-1].id
            last_employee_count = last_employee_id + 1
            target.employee_number = f"{target.dept.name}-{date_str}-{last_employee_count:03d}"

    def __repr__(self):
        return '<Employee %r>' % self.username

event.listen(Employee, "before_insert", Employee.generate_employee_number)


class Role(db.Model):
    __tablename__ = 'Role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, default="Employee")
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('Employee', foreign_keys=[Employee.role_id], backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'Employee': [Task.REQUEST_ASSET],
            'HR': [Task.REQUEST_ASSET, Task.TRACK_REQUEST, Task.TRACK_ASSIGNMENT,Task.MANAGE_EMPLOYEE],
            'Manager': [Task.REQUEST_ASSET, Task.SET_REQUEST_STATUS],
        }

        default_role = 'Employee'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return (self.permissions & perm) == perm
    
    def __repr__(self):
        return '<Role %r>' % self.name


class Department(db.Model):
    __tablename__ = 'Department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    location = db.Column(db.String(64), nullable=False)
    users = db.relationship('Employee', foreign_keys=[Employee.dept_id], backref='dept', lazy='dynamic')

    @staticmethod
    def insert_depts():
        depts = [
            ['IT', "Unilag Road, Yaba" ],
            ['CSC', "Unilag, after education, bariga"],
            ['FIN', "Unilag Road, Yaba" ],
            ['ENGR', "Unilag, after education, bariga"],
            ['SCS', "Unilag Road, Yaba" ],
            ]
        for d in depts:
            dept = Department.query.filter_by(name=d[0]).first()
            if dept is None:
                dept = Department(name=d[0], location=d[1])
                db.session.add(dept)
        db.session.commit()

    def __repr__(self):
        return '<Dept %r>' % self.name

event.listen(Item, "before_insert", Item.generate_serial_number)

@loginManager.user_loader
def load_user(id):
    return Employee.query.get(int(id))