from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .. import db
from ..models import Employee, Department
from ..utils import send_email, logout_required
from . import auth
from .forms import(LoginForm, SignUpForm, PasswordResetForm, PasswordResetRequestForm, 
                   ChangePasswordForm, ChangeEmailForm)

@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint \
            and request.blueprint != 'auth' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/login', methods=['GET', 'POST'])
@logout_required
def login():
    form = LoginForm()
    if form.validate_on_submit():
        employee = Employee.query.filter_by(employee_number=form.employeeID.data.upper()).first()
        if employee is not None and employee.verify_password(form.password.data):
            login_user(employee, form.rememberMe.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('Invalid email or password.', "warning")
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', "success")
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
@logout_required
def register():
    form = SignUpForm()
    if form.validate_on_submit():
        d=Department.query.filter_by(name=form.deptName.data.upper()).first()
        if d:
            employee = Employee(dept=d, email=form.email.data.lower(),
                        username=form.username.data,
                        password=form.password.data)
            db.session.add(employee)
            db.session.commit()
            token = employee.generate_confirmation_token()
            send_email(employee.email, 'Confirm Your Account',
                    'auth/email/confirm', employee=employee, token=token)
            flash('A confirmation email has been sent to you by email.', 'info')
        else:
            flash('Invalid Department Name', 'warning')
            return redirect(url_for('auth.register'))
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.', "error")
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', employee=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.', "info")
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.', "warning")
    return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        employee = Employee.query.filter_by(email=form.email.data.lower()).first()
        if employee:
            token = employee.generate_reset_token()
            send_email(employee.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       employee=employee, token=token)
        flash('An email with instructions to reset your password has been '
              'sent to you.', "info")
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        if Employee.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.', "success")
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data.lower()
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/change_email',
                       employee=current_user, token=token)
            flash('An email with instructions to confirm your new email '
                  'address has been sent to you.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.index'))