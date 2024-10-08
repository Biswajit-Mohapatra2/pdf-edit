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
        writer = PdfWriter()
        
        # Handle page deletion
        pages_to_delete = request.form.getlist('delete_pages')
        pages_to_keep = [i for i in range(num_pages) if str(i+1) not in pages_to_delete]
        
        # Handle new page insertions
        new_pages = request.files.getlist('new_pages')
        insert_positions = request.form.getlist('insert_positions')
        
        # Create a list of (position, page) tuples for insertion
        insertions = []
        for i, new_page in enumerate(new_pages):
            if new_page and allowed_file(new_page.filename):
                position = int(insert_positions[i]) - 1 if i < len(insert_positions) else num_pages
                insertions.append((position, new_page))
        
        # Sort insertions by position (descending) to maintain correct order
        insertions.sort(key=lambda x: x[0], reverse=True)
        
        # Get the size of the first page for resizing new pages
        first_page = pdf.pages[0]
        target_width = first_page.mediabox.width
        target_height = first_page.mediabox.height
        
        # Add pages to the new PDF
        current_page = 0
        for i in range(num_pages):
            if i in pages_to_keep:
                while insertions and insertions[-1][0] == current_page:
                    _, new_page = insertions.pop()
                    add_new_page(writer, new_page, target_width, target_height)
                    current_page += 1
                writer.add_page(pdf.pages[i])
                current_page += 1
        
        # Add any remaining new pages at the end
        while insertions:
            _, new_page = insertions.pop()
            add_new_page(writer, new_page, target_width, target_height)
        
        if writer.pages:
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            return send_file(output, download_name='edited_' + filename, as_attachment=True)
        else:
            flash('No changes were made to the PDF')
    
    return render_template('edit.html', filename=filename, num_pages=num_pages)

def add_new_page(writer, new_page_file, target_width, target_height):
    if new_page_file.filename.lower().endswith('.pdf'):
        new_pdf = PdfReader(new_page_file)
        new_page = new_pdf.pages[0]
        new_page.scale_to(target_width, target_height)
        writer.add_page(new_page)
    else:
        # Convert image to PDF and resize
        image = Image.open(new_page_file)
        image = image.convert('RGB')
        image = image.resize((int(target_width), int(target_height)), Image.LANCZOS)
        pdf_bytes = io.BytesIO()
        image.save(pdf_bytes, format='PDF')
        pdf_bytes.seek(0)
        new_pdf = PdfReader(pdf_bytes)
        writer.add_page(new_pdf.pages[0])

if __name__ == '__main__':
    app.run(debug=True)