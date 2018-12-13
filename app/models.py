from app import db
from flask_security import UserMixin, RoleMixin


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice = db.Column(db.String(64))
    invoice_num = db.Column(db.Integer)
    tracking_number = db.Column(db.String(128))
    light_type = db.Column(db.String(64))
    status = db.Column(db.String(64))
    correct_to_invoice = db.Column(db.Boolean)
    replacement_available = db.Column(db.Boolean)
    replacement_comments = db.Column(db.String(128))
    induction_employee_code = db.Column(db.String(32))
    approval_employee_code = db.Column(db.String(32))
    side = db.Column(db.String(32))
    have_repair = db.Column(db.Boolean)
    repair_comments = db.Column(db.String(128))
    light_approved = db.Column(db.String(10))
    approval_comments = db.Column(db.String(128))
    notes = db.Column(db.String(128))
    stickered_engraved = db.Column(db.Boolean)
    approval_type = db.Column(db.String(32))
    light_noted = db.Column(db.Boolean)
    induction_date = db.Column(db.DateTime)
    approval_date = db.Column(db.DateTime)
    light_type_comments = db.Column(db.String(128))
    images = db.relationship('Image', cascade="all, delete-orphan")


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(128))
    s3_bucket = db.Column(db.String(32))
    approval_date = db.Column(db.DateTime)
    parent_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(24))
    name = db.Column(db.String(128))


roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Role %r>' % (self.name)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
