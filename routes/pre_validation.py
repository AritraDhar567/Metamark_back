from flask import Blueprint, request, jsonify
from services.pre_upload_validator import PreUploadValidator
from werkzeug.utils import secure_filename
import os
import uuid

pre_validation_bp = Blueprint('pre_validation', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@pre_validation_bp.route('/validate', methods=['POST'])
def validate_before_upload():
    """Validate product data before listing"""
    
    # Get form data
    product_data = {
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'listed_price': request.form.get('listed_price'),
        'category': request.form.get('category'),
        'manufacturer': request.form.get('manufacturer'),
        'country_of_origin': request.form.get('country_of_origin'),
        'importer': request.form.get('importer'),
        'importer_email': request.form.get('importer_email'),
        'importer_phone': request.form.get('importer_phone'),
        'packer': request.form.get('packer'),
        'generic_name': request.form.get('generic_name'),
        'weight': request.form.get('weight'),
        'dimensions': request.form.get('dimensions'),
        'net_quantity': request.form.get('net_quantity')
    }
    
    # Get uploaded images
    images = request.files.getlist('images')
    
    if not images:
        return jsonify({'error': 'At least one product image is required'}), 400
    
    # Save images temporarily
    temp_dir = os.path.join('uploads', 'temp', str(uuid.uuid4()))
    os.makedirs(temp_dir, exist_ok=True)
    
    image_paths = []
    for image in images:
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(temp_dir, filename)
            image.save(filepath)
            image_paths.append(filepath)
    
    # Validate
    validator = PreUploadValidator()
    result = validator.validate_product_listing(product_data, image_paths)
    
    # Clean up temp files
    for path in image_paths:
        try:
            os.remove(path)
        except:
            pass
    try:
        os.rmdir(temp_dir)
    except:
        pass
    
    return jsonify(result)
