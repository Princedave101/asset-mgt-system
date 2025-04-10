from datetime import datetime
from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from app import db
from . import mg
from ...models import AssetRequest,Employee, StockInventory, AssetAssignment
from ...utils import send_email, manager_required

@mg.route("/dashboard")
@login_required
@manager_required
def manager_dashboard():
    pending_requests = AssetRequest.query.filter_by(status="Pending", forwarded=True).order_by(AssetRequest.request_date).all()
    return render_template("manager/managerdashboard.html", pending_requests=pending_requests)

@mg.route("/approve_request/<int:request_id>")
@login_required
@manager_required
def approve_request(request_id):
    """Manager approves the request."""
    asset_request = AssetRequest.query.get_or_404(request_id)
    stock = StockInventory.query.filter_by(item=asset_request.item).first()

    if stock.can_assign_item(asset_request.quantity):
        asset=AssetAssignment(
            employee=asset_request.employee,
            quantity=asset_request.quantity,
            item=asset_request.item
        ) 
        asset_request.status = "Approved"
        db.session.add_all([asset_request, asset, stock])
        db.session.commit()

        send_email(asset_request.employee.email, "Request Approved",
                   "mail/request_status", asset_request=asset_request, employee=asset_request.employee)
        flash("Request approved.", "success")
    else:
        flash("Available item stock is less than request")
    return redirect(url_for("main.mg.manager_dashboard"))

@mg.route("/reject_request/<int:request_id>")
@login_required
@manager_required
def decline_request(request_id):
    """Manager rejects asset request."""
    asset_request = AssetRequest.query.get_or_404(request_id)
    asset_request.status = "Declined"
    asset_request.decision_date = datetime.now()
    db.session.add(asset_request)
    db.session.commit()

    employee = asset_request.employee
    send_email(employee.email, "Request Declined",
                   "mail/request_status", asset_request=asset_request, employee=employee)
    flash("Request Rejected.", "danger")
    return redirect(url_for("main.mg.manager_dashboard"))

@mg.route("/inventory")
@login_required
@manager_required
def asset_inventory():
    stocks = StockInventory.query.all()
    return render_template("manager/inventory.html", stocks=stocks)
