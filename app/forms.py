from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, RadioField, TextAreaField, TextField
from wtforms.validators import DataRequired, Optional, ValidationError
from wtforms.widgets.html5 import NumberInput

from .models import Employee, Order, Image
from flask import render_template
from wtforms.fields import Field
from app import db
import boto3


def is_valid_employee(form, field):
    e = Employee.query.filter_by(code=field.data).first()
    if e is None:
        raise ValidationError('Not a valid employee code.')


def is_valid_invoice(form, field):
    e = Order.query.filter_by(invoice_num=field.data).first()
    if e is None:
        raise ValidationError('This invoice number does not exist in the system.')


class InductionForm(FlaskForm):
    invoice_num = IntegerField('Invoice Number', validators=[DataRequired()], widget=NumberInput())
    correct_to_invoice = RadioField('Correct to Invoice?', choices=[('y', 'Yes'), ('n', 'No')], validators=[Optional()])
    replacement_available = RadioField('Do we have a replacement available?', choices=[('y', 'Yes'), ('n', 'No')],
                                       validators=[Optional()])
    induction_employee_code = StringField('Induction Employee Code', description='Employee Code',
                                          validators=[DataRequired(), is_valid_employee])
    replacement_comments = StringField('Replacement Comments')
    light_noted = RadioField('Noted Correctly?', choices=[('y', 'Yes'), ('n', 'No')], validators=[Optional()])
    light_type = RadioField('Light Type', choices=[('HID', 'HID'), ('LED', 'LED'), ('Halogen', 'Halogen')],
                            validators=[Optional()])
    light_type_comments = StringField('Replacement Comments')
    side = RadioField('Side', choices=[('LH', 'LH'), ('RH', 'RH')], validators=[Optional()])

    def validate(self):
        validated = False
        if FlaskForm.validate(self):
            validated = True

        if self.light_type.data == 'HID' or self.light_type.data == 'LED':
            print("HID")
            if self.light_type_comments.data is None or self.light_type_comments.data == '':
                print("Comments blank")
                self.light_type_comments.errors.append('Please add comments about light type.')
                validated = False

        return validated


class ApprovalForm(FlaskForm):
    invoice_num = IntegerField('Invoice Number', validators=[DataRequired()], widget=NumberInput())
    tracking_number = StringField('Tracking Number', validators=[DataRequired()])
    approval_employee_code = StringField('Approval Employee Code', description='Employee Code',
                                         validators=[DataRequired(), None])
    have_repair = RadioField('Have Repair?', choices=[('y', 'Yes'), ('n', 'No')])
    stickered_engraved = RadioField('Stickered and Engraved?', choices=[('y', 'Yes'), ('n', 'No')],
                                    validators=[DataRequired()])
    repair_comments = StringField('Repair Comments')
    light_approved = RadioField('Final Approved', choices=[('Yes', 'Yes'), ('No', 'No'), ('Other', 'Other')],
                                validators=[DataRequired()])
    approval_comments = StringField('Approval Comments')
    notes = TextAreaField('Notes')
    approval_type = RadioField('Final Approved', choices=[('Recon', 'Recon Light'), ('New', 'New Light')],
                               default='Recon', validators=[DataRequired()])
    image_list = TextField('Image List')

    def validate(self):
        validated = False
        if self.approval_type.data == 'New':
            self.have_repair.data = 'y'
        if FlaskForm.validate(self):
            validated = True
        if self.approval_type.data == 'Recon':
            e = Order.query.filter_by(invoice_num=self.invoice_num.data).first()
            if e is None:
                self.invoice_num.errors.append('This invoice number does not exist in the system.')
                validated = False
            if not self.have_repair.data:
                self.invoice_num.errors.append('Does this light have a repair?')
                validated = False
        else:
            e = Order.query.filter_by(invoice_num=self.invoice_num.data).first()
            if e is not None:
                self.invoice_num.errors.append(
                    'This invoice already exists in the system. Please enter a unique invoice number.')
                validated = False
        return validated


def render_image(data, cls, **kwargs):
    resource = boto3.resource('s3')
    ids = []
    images = []
    for image in data.data:
        ids.append(str(image.id))
        i = {'id': str(image.id)}
        i['url'] = "https://s3.us-east-1.amazonaws.com/{}/{}".format(image.s3_bucket, image.file_name)
        images.append(i)
    return render_template('admin/image.html', ids=ids, images=images)


class ImageField(Field):
    widget = render_image

    def process_formdata(self, valuelist):
        form_id_list = [int(x.strip()) for x in valuelist[0].split('|')] if valuelist[0] else []
        s3 = boto3.resource('s3')
        remaining = []
        for image in self.data[::-1]:
            if image.id not in form_id_list:
                bucket = image.s3_bucket
                file_name = image.file_name
                s3.Bucket(bucket).delete_objects(Delete={'Objects': [{'Key': file_name}]})
                Image.query.filter(Image.id == image.id).delete()
            else:
                remaining.append(image)
        db.session.commit()
        self.data = remaining
