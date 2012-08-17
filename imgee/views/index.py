# -*- coding: utf-8 -*-

from flask import render_template, request
from imgee import app, uploadedfiles
from imgee.forms import UploadForm


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=('GET', 'POST'))
def upload_images():
    form = UploadForm(request.form)
    if form.validate_on_submit():
        filename = uploadedfiles(request.files['uploaded_file'])
        filename.store()
        flash("File saved.")
    return render_template('form.html', form=form)

