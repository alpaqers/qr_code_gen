from flask import Blueprint, render_template, request, flash, send_file, redirect, url_for
from flask_login import login_required, current_user
from .models import QRCode
from . import db
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image
import io
import base64
import os

views = Blueprint('views', __name__)

@views.route('/', methods=['GET'])
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/generate_qr', methods=['GET', 'POST'])
@login_required
def generate_qr():
    if request.method == 'POST':
        data = request.form.get('data')
        size = int(request.form.get('size', 10))
        color_fg = request.form.get('color', '#000000')
        color_bg = request.form.get('color_bg', '#FFFFFF')
        logo = request.files.get('logo')

        if not data:
            flash('Please enter some data.', 'error')
            return redirect(url_for('views.generate_qr'))

        logo_filename = None
        if logo:
            print("logo istnieje")
        else:
            print("logo nie istnieje")

        if logo and logo.filename:
            os.makedirs('static', exist_ok=True)
            logo_filename = os.path.join('static', logo.filename)
            logo.save(logo_filename)
            print("Zapisano logo do:", logo_filename)
            print("Plik istnieje?", os.path.exists(logo_filename))


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

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=2,
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
