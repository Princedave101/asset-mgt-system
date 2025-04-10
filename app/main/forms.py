from flask_wtf import FlaskForm
from wtforms import (SelectField, IntegerField,TextAreaField, 
                     SubmitField, StringField, EmailField, PasswordField, BooleanField)
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from ..models import Department, Employee, Role


class EmployeeForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64)])
    role = SelectField("Role", choices=[('Employee', 'Employee'),
                                        ('HR', 'HR'),
                                        ('Manager', 'Manager')], validators=[DataRequired()])
    dept = SelectField("Department", choices=[('IT', 'IT'),
                                        ('CSC', 'CSC'),
                                        ('FIN', 'FIN'),
                                        ('ENGR', 'ENGR'),
                                        ('SCS', 'SCS')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('confirmPassword', message='Passwords must match.')])
    confirmPassword = PasswordField('Confirm password', validators=[DataRequired()])
    confirmed = BooleanField("Confirm Account")
    submit = SubmitField('Create')

    def validate_email(self, field):
        if Employee.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if Employee.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')



class AssetRequestForm(FlaskForm):
    item = SelectField(
    "Items", choices=[("Telephone", "Telephone"),
                      ("Projectors", "Projectors"),
                      ("Laptop", "Laptop"), 
                      ("Monitors", "Monitors"), 
                      ("Bicycles", "Bicycles"),
                      ("Conference Tables", "Conference Tables"),
                      ("Harddisk", "Harddisk"),
                      ("Printer", "Printer"),
                      ("Company Cars", "Company Cars"),
                      ("Routers", "Routers"),
                      ("Office Chairs", "Office Chairs"),
                      ("Keyboards", "Keyboards"), 
                      ("CCTV Cameras", "CCTV Cameras"), 
                      ("Delivery Vans", "Delivery Vans"), 
                      ("Air Conditioners", "Air Conditioners"),
                      ("Cubicles", "Cubicles"), 
                      ("Cabinets", "Cabinets")], validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[DataRequired()])
    reason = TextAreaField("Reason for Request", validators=[DataRequired()])
    submit = SubmitField("Submit Request")


class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    job_description = TextAreaField('Job Description')
    submit = SubmitField('Submit')
 

class EditProfileHRForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64)])
    role = SelectField('Role', coerce=int)
    dept = SelectField('dept', coerce=int)
    fullname = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    job_description = TextAreaField('Job Description')
    confirmed = BooleanField('Confirmed')
    is_active = BooleanField('Active')
    submit = SubmitField('Submit')

    def __init__(self, employee, *args, **kwargs):
        super(EditProfileHRForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.dept.choices = [(dept.id, dept.name)
                             for dept in Department.query.order_by(Department.name).all()]
        self.employee = employee

    def validate_email(self, field):
        if field.data != self.employee.email and \
                Employee.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.employee.username and \
                Employee.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')