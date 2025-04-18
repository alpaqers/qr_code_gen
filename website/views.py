from flask import Blueprint, render_template, request, flash, send_file, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Note, QRCode
from . import db
import json
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image
import io
import base64
import os
from datetime import datetime

views = Blueprint('views', __name__)

@views.route('/initdb')
def init_db():
    from . import db
    db.create_all()
    return "Baza danych zainicjalizowana!"

@views.route('/generate_qr', methods=['GET', 'POST'])
def generate_qr():
    if request.method == 'POST':
        data = request.form.get('data')
        size = int(request.form.get('size', 10))
        color_fg = request.form.get('color_fg', '#000000')
        color_bg = request.form.get('color_bg', '#FFFFFF')
        logo = request.files.get('logo')

        if not data:
            flash('Please enter some data.', 'error')
            return redirect(url_for('generate_qr'))

        logo_filename = None
        if logo and logo.filename:
            logo_filename = os.path.join(app.config['UPLOAD_FOLDER'], logo.filename)
            logo.save(logo_filename)

        # Save to DB
        new_code = QRCode(
            data=data,
            size=size,
            color_fg=color_fg,
            color_bg=color_bg,
            logo_filename=logo_filename,
            user_id=current_user.id
        )
        db.session.add(new_code)
        db.session.commit()

        # Generate QR image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=color_fg, back_color=color_bg).convert('RGB')

        if logo_filename:
            try:
                logo_img = Image.open(logo_filename)
                logo_size = int(img.size[0] * 0.25)
                logo_img = logo_img.resize((logo_size, logo_size))
                pos = ((img.size[0] - logo_size) // 2, (img.size[1] - logo_size) // 2)
                img.paste(logo_img, pos, mask=logo_img.convert("RGBA"))
            except Exception as e:
                flash(f"Error adding logo: {e}", 'error')

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        img_url = f"data:image/png;base64,{img_b64}"

        return render_template("generate_qr.html", qr_code_url=img_url)

    return render_template("generate_qr.html")

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note=Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    
    return jsonify({})