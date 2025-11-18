from flask import Blueprint, request, jsonify
from models.database import Database
from services.crawler import ProductScraper
from services.storage import ImageDownloader
from services.compliance_engine import ComplianceEngine
import json

products_bp = Blueprint('products', __name__)

@products_bp.route('/scrape', methods=['POST'])
def scrape_product():
    """Scrape product from URL"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    scraper = ProductScraper()
    
    if 'amazon' in url.lower():
        product_data = scraper.scrape_amazon_product(url)
    elif 'flipkart' in url.lower():
        product_data = scraper.scrape_flipkart_product(url)
    else:
        product_data = scraper.scrape_generic_product(url)
    
    if not product_data:
        return jsonify({'error': 'Failed to scrape product'}), 500
    
    # Save product with ALL fields updated
    query = """
        INSERT INTO products (
            product_id, url, title, description, listed_price, currency, seller, 
            category, marketplace, publisher, language, isbn_10, isbn_13, 
            dimensions, weight, page_count, country_of_origin, manufacturer, 
            packer, importer, importer_email, importer_phone, generic_name, 
            rating, review_count
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            listed_price = VALUES(listed_price),
            publisher = VALUES(publisher),
            language = VALUES(language),
            isbn_10 = VALUES(isbn_10),
            isbn_13 = VALUES(isbn_13),
            dimensions = VALUES(dimensions),
            weight = VALUES(weight),
            page_count = VALUES(page_count),
            country_of_origin = VALUES(country_of_origin),
            manufacturer = VALUES(manufacturer),
            packer = VALUES(packer),
            importer = VALUES(importer),
            importer_email = VALUES(importer_email),
            importer_phone = VALUES(importer_phone),
            generic_name = VALUES(generic_name),
            rating = VALUES(rating),
            review_count = VALUES(review_count)
    """

    
    Database.execute_insert(query, (
        product_data['product_id'],
        product_data['url'],
        product_data['title'],
        product_data.get('description'),
        product_data.get('listed_price'),
        product_data.get('currency', 'INR'),
        product_data.get('seller'),
        product_data.get('category'),
        product_data.get('marketplace'),
        product_data.get('publisher'),
        product_data.get('language'),
        product_data.get('isbn_10'),
        product_data.get('isbn_13'),
        product_data.get('dimensions'),
        product_data.get('weight'),
        product_data.get('page_count'),
        product_data.get('country_of_origin'),
        product_data.get('manufacturer'),
        product_data.get('packer'),
        product_data.get('importer'),
        product_data.get('importer_email'),
        product_data.get('importer_phone'),
        product_data.get('generic_name'),
        product_data.get('rating'),
        product_data.get('review_count')
    ))
    
    # Download images
    downloader = ImageDownloader()
    image_urls = product_data.get('image_urls', [])
    
    for img_url in image_urls:
        filepath = downloader.download_image(img_url, product_data['product_id'])
        if filepath:
            img_query = """
                INSERT INTO images (product_id, image_url, storage_path)
                VALUES (%s, %s, %s)
            """
            Database.execute_insert(img_query, (product_data['product_id'], img_url, filepath))
    
    product = Database.execute_one(
        "SELECT * FROM products WHERE product_id = %s",
        (product_data['product_id'],)
    )
    
    return jsonify({
        'success': True,
        'product': product,
        'images_downloaded': len(image_urls)
    })

@products_bp.route('/validate/<product_id>', methods=['POST'])
def validate_product(product_id):
    """Two-step validation: Vision OCR + Gemini AI Analysis"""
    engine = ComplianceEngine()
    result = engine.validate_product(product_id)
    
    if 'error' in result:
        return jsonify(result), 404
    
    return jsonify(result)

@products_bp.route('/', methods=['GET'])
def get_products():
    """Get all products with compliance grade"""
    products = Database.execute_query(
        """SELECT product_id, title, marketplace, category, listed_price, 
           compliance_grade, compliance_score, last_validated_at, crawled_at
           FROM products ORDER BY crawled_at DESC"""
    )
    return jsonify(products)

@products_bp.route('/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details with grade"""
    product = Database.execute_one(
        "SELECT * FROM products WHERE product_id = %s",
        (product_id,)
    )
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    validations = Database.execute_query(
        "SELECT * FROM validations WHERE product_id = %s ORDER BY checked_at DESC",
        (product_id,)
    )
    
    return jsonify({
        'product': product,
        'compliance_grade': product.get('compliance_grade'),
        'compliance_score': product.get('compliance_score'),
        'last_validated': product.get('last_validated_at'),
        'validations': validations
    })


@products_bp.route('/<product_id>/report', methods=['GET'])
def get_compliance_report(product_id):
    """Get detailed compliance report"""
    product = Database.execute_one(
        "SELECT * FROM products WHERE product_id = %s",
        (product_id,)
    )
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    validations = Database.execute_query(
        "SELECT * FROM validations WHERE product_id = %s",
        (product_id,)
    )
    
    ocr_results = Database.execute_query(
        """
        SELECT o.*, i.image_url FROM ocr_results o
        JOIN images i ON o.image_id = i.id
        WHERE i.product_id = %s
        """,
        (product_id,)
    )
    
    total = len(validations)
    passed = sum(1 for v in validations if v['passed'])
    failed = total - passed
    
    high_severity = sum(1 for v in validations if not v['passed'] and v['severity'] == 'high')
    
    return jsonify({
        'product': product,
        'summary': {
            'total_checks': total,
            'passed': passed,
            'failed': failed,
            'compliance_rate': round((passed/total*100) if total > 0 else 0, 2),
            'high_severity_violations': high_severity,
            'status': 'COMPLIANT' if (passed/total*100 if total > 0 else 0) >= 80 else 'NON_COMPLIANT'
        },
        'validations': validations,
        'ocr_results': ocr_results
    })
