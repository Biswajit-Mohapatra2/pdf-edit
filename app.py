from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import os
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a real secret key

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)
            return redirect(url_for('edit_pdf', filename=file.filename))
        else:
            flash('Please upload a PDF or image file (PNG, JPG, JPEG)')
    return render_template('index.html')

@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit_pdf(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    pdf = PdfReader(filepath)
    num_pages = len(pdf.pages)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_page':
            new_page_file = request.files.get('new_page')
            if new_page_file and allowed_file(new_page_file.filename):
                writer = PdfWriter()
                
                # Add existing pages
                for i in range(num_pages):
                    writer.add_page(pdf.pages[i])
                
                # Add the new page
                if new_page_file.filename.lower().endswith('.pdf'):
                    new_pdf = PdfReader(new_page_file)
                    writer.add_page(new_pdf.pages[0])
                else:
                    # Convert image to PDF
                    image = Image.open(new_page_file)
                    pdf_bytes = io.BytesIO()
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')
                    image.save(pdf_bytes, format='PDF')
                    pdf_bytes.seek(0)
                    new_pdf = PdfReader(pdf_bytes)
                    writer.add_page(new_pdf.pages[0])
                    image.close()
                
                output = io.BytesIO()
                writer.write(output)
                output.seek(0)
                
                return send_file(output, download_name='edited_' + filename, as_attachment=True)
            else:
                flash('Please upload a valid PDF or image file (PNG, JPG, JPEG)')
    
    return render_template('edit.html', filename=filename, num_pages=num_pages)

if __name__ == '__main__':
    app.run(debug=True)
