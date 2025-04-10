from datetime import datetime
from flask import render_template, redirect, url_for, flash, abort, current_app
from flask_login import current_user, login_required
from .. import db
from . import main
from .forms import AssetRequestForm, EditProfileForm
from ..models import AssetRequest, AssetAssignment, Employee, Item, StockInventory
from ..utils import send_email, employee_required



@main.route("/dashboard")
@main.route('/')
@login_required
def index():
    if current_user.role.name == "Manager":
        return redirect(url_for('main.mg.manager_dashboard'))
    elif current_user.role.name == "HR":
        return redirect(url_for('main.hr.hr_dashboard'))
    else:
        pending_requests=AssetRequest.query.filter_by(employee=current_user, status="Pending").all()
        requests = AssetRequest.query.filter_by(employee=current_user).all()
        assigned_asset_count = AssetAssignment.query.filter_by(employee=current_user, status="Active").count()
        return render_template('employeedashboard.html', pending_requests=pending_requests, 
                            pending_requests_count=len(pending_requests),
                            request_count=len(requests), assigned_asset_count=assigned_asset_count)

@main.route('/user/<string:employee_number>')
@login_required
def profile(employee_number):
    employee = Employee.query.filter_by(employee_number=employee_number).first_or_404()
    return render_template('user.html', employee=employee)


@main.route('/request-asset', methods=["GET", "POST"])
@login_required
def request_asset():
    form = AssetRequestForm()
    
    if form.validate_on_submit():
        item = Item.query.filter_by(name=form.item.data).first() 
        new_request = AssetRequest(
            employee_id=current_user.id,
            reason=form.reason.data,
            quantity=form.quantity.data,
            item=item,
            request_date=datetime.now(),
            status="Pending",
        )
        db.session.add(new_request)
        db.session.commit()
        send_email(current_app.config["APP_HR"], "Asset Request Made",
                   "mail/created_request", asset_request=new_request)
        flash("Asset request submitted successfully!", "success")
        return redirect(url_for("main.index"))  # Ensure this route exists
    return render_template('newRequest.html', form=form)


@main.route("/requests")
@login_required
def requests():
    """Show all pending asset requests for a specific employee."""
    requests = AssetRequest.query.filter_by(employee=current_user._get_current_object()).all()
    return render_template("request_history.html", requests=requests)

@main.route("/assets/<string:employee_number>")
@login_required
def view_assets(employee_number):
    """Show all assigned assets for a specific employee."""
    employee = Employee.query.filter_by(employee_number=employee_number).first_or_404()
    assigned_assets = AssetAssignment.query.filter_by(employee=employee, status="Active").all()
    return render_template('employeeAssets.html', assigned_assets=assigned_assets)

@main.route("/relenquish-asset/<int:id>")
@login_required
def relenquish_asset(id):
    if current_user.role.name != "HR" and not current_user.is_authenticated:
        abort(403)
    assigned_asset =  AssetAssignment.query.filter_by(
        status="Active", item_id=id
    ).first_or_404()
    assigned_asset.status = "Returned"
    assigned_asset.return_date = datetime.now()

    stock = StockInventory.query.filter_by(item_id=id).first()
    if stock:
        stock.available_quantity += assigned_asset.quantity  # Increase stock quantity
    
    send_email(assigned_asset.employee.email, "Asset Returned",
                   "mail/return_asset", assigned_asset=assigned_asset)
    db.session.delete(assigned_asset)
    db.session.add(stock)
    db.session.commit()
    flash("Asset Returned", "success")
    return redirect(url_for("main.index"))

@main.route("/cancel-request/<int:id>")
@login_required
def cancel_request(id):
    if current_user.role.name != "HR" and not current_user.is_authenticated:
        abort(403)
    request = AssetRequest.query.get_or_404(id)
    request.status = "Canceled"
    db.session.add(request)
    db.session.commit()
    flash("Request Canceled", "success")
    send_email(request.employee.email, "Request Canceled", 'mail/canceled', employee=request.employee, request=request)
    return redirect(url_for("main.index"))

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.fullname = form.name.data
        current_user.location = form.location.data
        current_user.job_description = form.job_description.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.', "success")
        return redirect(url_for('main.profile', employee_number=current_user.employee_number))
    form.name.data = current_user.fullname
    form.location.data = current_user.location
    form.job_description.data = current_user.job_description
    return render_template('edit_profile.html', form=form)



