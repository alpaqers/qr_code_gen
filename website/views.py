from flask import Blueprint, render_template, request, flash, send_file, redirect, url_for, session
from flask_login import login_required, current_user
from .models import QRCode
from . import db
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image
import io
import csv
import base64
import os
from zipfile import ZipFile

views = Blueprint('views', __name__)

def save_qr_to_db(data, size, color_fg, color_bg, logo_filename, user_id):
    new_code = QRCode(
        data=data,
        size=size,
        color_fg=color_fg,
        color_bg=color_bg,
        logo_filename=logo_filename,
        user_id=user_id
    )
    db.session.add(new_code)
    db.session.commit()


def generate_qr_image(data, size, color_fg, color_bg, logo_stream=None):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=2
    )

    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=color_fg, back_color=color_bg).convert('RGB')

    if logo_stream:
        try:
            logo_img = Image.open(logo_stream)
            logo_size = int(img.size[0] * 0.20)
            logo_img = logo_img.resize((logo_size, logo_size))
            pad = logo_size // 7
            full_size = logo_size + pad * 2
            img_bg = Image.new("RGBA", (full_size, full_size), color_bg)
            pos = ((img.size[0] - full_size) // 2, (img.size[1] - full_size) // 2)
            img_bg.paste(logo_img, (pad, pad), mask=logo_img.convert("RGBA"))
            img.paste(img_bg, pos, mask=img_bg)
        except Exception as e:
            flash(f"Error adding logo: {e}", 'error')

    return img

@views.route('/', methods=['GET'])
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/generate_qr', methods=['GET', 'POST'])
@login_required
def generate_qr():
    qr_code_url = None
    if request.method == 'GET':

        # ustawiamy wartości domyślne
        data = ""
        size = 10
        color_fg = "#000000"
        color_bg = "#FFFFFF"
        
        return render_template("generate_qr.html",
        qr_code_url=qr_code_url,
        data=data,
        size=size,
        color_fg=color_fg,
        color_bg=color_bg
        )
    if request.method == 'POST':
        data = request.form.get('data')
        size = int(request.form.get('size', 10))
        color_fg = request.form.get('color', '#000000')
        color_bg = request.form.get('color_bg', '#FFFFFF')
        logo = request.files.get('logo')
        file = request.files.get('upload_file')
        mode = request.form.get('mode', 'single')

        #print(f"Mode: {mode}, Data: {data}, Size: {size}, Color FG: {color_fg}, Color BG: {color_bg}")

        #if not file:
        #    print("No file uploaded.")

        if mode == 'bulk' and file:
            stream = io.StringIO(file.stream.read().decode("utf-8"))
            reader = csv.reader(stream)
            zip_buffer = io.BytesIO()

            with ZipFile(zip_buffer, 'w') as zip_file:
                for i, row in enumerate(reader, start=1):
                    if not row:
                        continue
                    data = row[0].strip()

                    save_qr_to_db(data, size, color_fg, color_bg, None, current_user.id)

                    img = generate_qr_image(data, size, color_fg, color_bg, logo.stream if logo else None)

                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    buf.seek(0)

                    zip_file.writestr(f"qr_{i}.png", buf.getvalue())
            zip_buffer.seek(0)
            return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='qr_codes.zip')
        elif data:
            save_qr_to_db(data, size, color_fg, color_bg, None, current_user.id)

            img = generate_qr_image(data, size, color_fg, color_bg, logo.stream if logo else None)

            buf = io.BytesIO()
            img.save(buf, format='PNG')

            # Przesuwamy wskaźnik bufora na początek
            buf.seek(0)

            # 1. Zapisujemy do sesji (do pobrania)
            session['qr_image'] = base64.b64encode(buf.read()).decode('utf-8')

            # 2. Przesuwamy znowu i generujemy URL do podglądu
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode('utf-8')
            img_url = f"data:image/png;base64,{img_b64}"

        else:
            flash('Please enter some data.', 'error')
            return redirect(url_for('views.generate_qr'))

        return render_template("generate_qr.html", qr_code_url=img_url, 
                               data=data, size=size, color_fg=color_fg, color_bg=color_bg)

    return render_template("generate_qr.html")

@views.route('/download_qr')
@login_required
def download_qr():

    if 'qr_image' not in session:
        flash('No QR code found to download.', 'error')
        return redirect(url_for('views.generate_qr'))

    img_data = base64.b64decode(session['qr_image'])
    buf = io.BytesIO(img_data)
    buf.seek(0)
    return send_file(buf, mimetype='image/png', as_attachment=True, download_name='qr_code.png')
