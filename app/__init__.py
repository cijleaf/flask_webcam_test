import os, boto3
from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, expose, AdminIndexView, BaseView
from flask_admin.form import rules
from flask_security import Security, SQLAlchemyUserDatastore, current_user
from flask_admin.menu import MenuLink

from flask_admin.contrib.sqla import fields
from flask_admin._compat import text_type
from sqlalchemy.orm.util import identity_key
from sqlalchemy.event import listens_for

app = Flask(__name__)

app.config.from_object('config.DevelopmentConfig')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from app import views, models

from .models import Order, Employee, User, Role, Image
from .forms import ImageField


class OrderView(ModelView):
	can_delete = False
	can_export = True
	column_filters = ('invoice_num', 'approval_type','status','induction_date','induction_employee_code','approval_date','approval_employee_code')
	form_choices = { 'side': [('LH','LH'),('RH','RH')],
					'light_type': [('HID','HID'),('LED','LED'),('Halogen','Halogen')],
					'status': [('Pending','Pending'),('Approved','Approved'),('Rejected','Rejected')] }
	column_list = ('invoice_num', 'approval_type','status','side','light_type','induction_date','induction_employee_code','approval_date','approval_employee_code')

	column_searchable_list = ['invoice_num','tracking_number']

	form_edit_rules = (
		rules.FieldSet(('invoice_num', 'approval_type', 'status'), ''),
		rules.FieldSet(('induction_date','induction_employee_code','side','light_type','light_type_comments','correct_to_invoice','light_noted','replacement_available','replacement_comments'), 'Induction'),
		rules.FieldSet(('approval_date','approval_employee_code', 'tracking_number','have_repair','repair_comments','light_approved','approval_comments','stickered_engraved','notes','images'), 'Final Approval'),
		)

	def _induction_date_formatter(view, context, model, name):
		if model.induction_date is not None:
			return model.induction_date.strftime("%b %d, %Y")
		else:
			return ""

	def _approval_date_formatter(view, context, model, name):
		if model.approval_date is not None:
			return model.approval_date.strftime("%b %d, %Y") 
		else:
			return ""

	def _induction_employee_formatter(view,context,model,name):
		e = Employee.query.filter_by(code=model.induction_employee_code).first()
		if e is not None:
			return e.name + " (" + model.induction_employee_code + ")"
		else:
			return ""

	def _approval_employee_formatter(view,context,model,name):
		e = Employee.query.filter_by(code=model.approval_employee_code).first()
		if e is not None:
			return e.name + " (" + model.approval_employee_code + ")"
		else:
			return ""

	column_formatters = {
		'induction_date': _induction_date_formatter,
		'approval_date': _approval_date_formatter,
		'induction_employee_code': _induction_employee_formatter,
		'approval_employee_code': _approval_employee_formatter
	}

	form_extra_fields = {
		'images': ImageField()
	}

	extra_js = ['/static/admin.js','/static/lightbox.js']

	def is_accessible(self):
		return current_user.has_role('admin')

		
class PendingView(OrderView):
	column_sortable_list = ('induction_date', 'induction_employee_code', 'invoice_num','side', 'light_type')
	column_list = ('induction_date', 'induction_employee_code', 'invoice_num', 'side', 'light_type')

	def get_query(self):
		return Order.query.filter_by(status='Pending').order_by(models.Order.induction_date.desc())

class ApprovedView(OrderView):
	column_sortable_list = ('approval_date', 'approval_type','approval_employee_code', 'invoice_num','side', 'light_type')
	column_list = ('approval_date', 'approval_type','approval_employee_code', 'invoice_num', 'side', 'light_type','light_noted','have_repair','stickered_engraved')

	def get_query(self):
		return Order.query.filter_by(status='Approved').order_by(models.Order.approval_date.desc())

class RejectedView(OrderView):
	column_sortable_list = ('induction_date', 'induction_employee_code', 'invoice_num','side', 'light_type')
	column_list = ('induction_date', 'induction_employee_code', 'invoice_num', 'side', 'light_type')

	def get_query(self):
		return Order.query.filter_by(status='Rejected').order_by(models.Order.induction_date.desc())


class EmployeeView(ModelView):
	can_delete = True

	def is_accessible(self):
		return current_user.has_role('admin')



class HomeView(AdminIndexView):
	@expose("/")
	def index(self):
		return self.render('admin/home.html')



admin = Admin(app, name="flaskwebcam", template_mode='bootstrap3', index_view=HomeView())
admin.add_view(PendingView(Order, db.session,name='Pending', endpoint='pending'))
admin.add_view(ApprovedView(Order, db.session,name='Approved', endpoint='approved'))
admin.add_view(RejectedView(Order, db.session,name='Rejected', endpoint='rejected'))
admin.add_view(OrderView(Order, db.session, name='Browse Orders'))
admin.add_view(EmployeeView(Employee, db.session, name='Employees'))


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)



class LoginMenuLink(MenuLink):

	def is_accessible(self):
		return not current_user.is_authenticated 

class LogoutMenuLink(MenuLink):

	def is_accessible(self):
		return current_user.is_authenticated             

admin.add_link(LogoutMenuLink(name='Logout', category='', url="/logout"))
admin.add_link(LoginMenuLink(name='Login', category='', url="/login"))


@app.before_first_request
def create_user():
	if user_datastore.find_role('admin') == None:
		user_datastore.create_role(name='admin')
	if user_datastore.find_user(email='admin@gmail.com') is None:
		user_datastore.create_user(email='admin@gmail.com', password='password', roles=['admin'])
	db.session.commit()

@app.context_processor
def override_url_for():
	return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
	if endpoint == 'static':
		filename = values.get('filename', None)
		if filename:
			file_path = os.path.join(app.root_path,
								 endpoint, filename)
			values['q'] = int(os.stat(file_path).st_mtime)
	return url_for(endpoint, **values)
	
def get_pk_from_identity(obj):
	res = identity_key(instance=obj)
	cls, key = res[0], res[1]
	return u':'.join(text_type(x) for x in key)

fields.get_pk_from_identity = get_pk_from_identity


@listens_for(Image, 'after_delete')
def del_image(mapper, connection, target):
	bucket = target.s3_bucket
	file_name = target.file_name
	s3 = boto3.resource('s3')
	s3.Bucket(bucket).delete_objects(Delete={'Objects':[{'Key':file_name}]})

