from datetime import datetime
from flask import render_template, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from ...models import db, Employee, Department, Role, AssetRequest, AssetAssignment, StockInventory
from ...utils import send_email, hr_required
from ..forms import EmployeeForm, EditProfileHRForm
from . import hr

@hr.route("/dashboard")
@login_required
@hr_required
def hr_dashboard():
    """HR Dashboard: View all asset requests"""
    pending_requests = AssetRequest.query.filter_by(status="Pending", forwarded=False).all()
    requests_count = AssetRequest.query.count()
    assigned_asset_count = AssetAssignment.query.count()
    employee_count = Employee.query.count()
    return render_template("hr/hrdashboard.html", 
                            pending_requests=pending_requests, pending_requests_count=len(pending_requests),
                            requests_count=requests_count,
                            assigned_asset_count=assigned_asset_count,
                            employee_count = employee_count
                           )

@hr.route("/forward_request/<int:id>")
@login_required
@hr_required
def forward_request(id):
    """Forward request to manager """
    asset_request = AssetRequest.query.get_or_404(id)
    if asset_request.status == "Pending":
        asset_request.forwarded = True
        db.session.add(asset_request)
        db.session.commit()
        send_email(current_app.config["APP_MANAGER"], "AssetRequest Pending Approval",
                   "mail/forward_request", asset_request=asset_request)

        flash("Request forwarded to the manager.", "success")
    return redirect(url_for("main.hr.hr_dashboard"))


@hr.route("/delete-request/<int:id>")
@login_required
@hr_required
def delete_request(id):
    if current_user.role.name != "HR" and not current_user.is_authenticated:
        abort(403)
    request = AssetRequest.query.get_or_404(id)
    db.session.delete(request)
    db.session.commit()
    flash("Request Deleted")
    return redirect(url_for("main.index"))


@hr.route("/add_employee", methods=["GET", "POST"])
@login_required
@hr_required
def add_employee():
    """HR: Add a new employee."""
    form = EmployeeForm()
    if form.validate_on_submit():
        new_employee = Employee(
            email=form.email.data,
            username=form.username.data,
            dept=Department.query.filter_by(name=form.dept.data).first(),
            role=Role.query.filter_by(name=form.role.data).first(),
            password=form.password.data,
            confirmed=form.confirmed.data)
        db.session.add(new_employee)
        db.session.commit()
        flash("Employee added successfully.", "success")
        return redirect(url_for("main.hr.view_employees"))
    return render_template("hr/addEmployee.html", form=form)

@hr.route("/employees")
@login_required
@hr_required
def view_employees():
    """HR: view all employee."""
    employees = Employee.query.all()
    return render_template("hr/hrEmployeeMgt.html", employees=employees)

@hr.route("/assets")
@login_required
@hr_required
def view_all_assigned_assets():
    """Show all assigned assets for all specific employee."""
    assigned_assets = AssetAssignment.query.filter_by(status="Active").all()
    return render_template('hr/hrAssignedAssets.html', assigned_assets=assigned_assets)

@hr.route("/requests")
@hr_required
def view_all_requests():
    requests = AssetRequest.query.all()
    return render_template("request_history.html", requests=requests)

@hr.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@hr_required
def edit_profile_hr(id):
    employee = Employee.query.get_or_404(id)
    form = EditProfileHRForm(employee=employee)
    if form.validate_on_submit():
        employee.email = form.email.data
        employee.username = form.username.data
        employee.role = Role.query.get(form.role.data)
        employee.dept = Department.query.get(form.dept.data)
        employee.fullname = form.fullname.data
        employee.location = form.location.data
        employee.job_description = form.job_description.data
        employee.confirmed = form.confirmed.data
        # employee.is_active = form.is_active.data
        db.session.add(employee)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.view_employees'))
    form.email.data = employee.email
    form.username.data = employee.username
    form.confirmed.data = employee.confirmed
    form.is_active.data = employee.is_active
    form.role.data = employee.role_id
    form.dept.data = employee.dept_id
    form.fullname.data = employee.fullname
    form.location.data = employee.location
    form.job_description.data = employee.job_description
    return render_template('edit_profile.html', form=form, employee=employee)

@hr.route("/delete-employee/<string:employee_number>", methods=['POST'])
@login_required
@hr_required
def delete_account(employee_number):
    employee = Employee.query.filter_by(employee_number=employee_number).first_or_404()
    db.session.delete(employee)
    db.session.commit()
    flash("Account Deleted", "success")
    return redirect(url_for('main.hr.view_employees'))