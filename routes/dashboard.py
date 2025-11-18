from flask import Blueprint, jsonify, send_file
from models.database import Database
import pandas as pd
import io

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/summary', methods=['GET'])
def dashboard_summary():
    """Dashboard summary"""
    total_products = Database.execute_one(
        "SELECT COUNT(*) as count FROM products"
    )['count']
    
    products_with_violations = Database.execute_one(
        "SELECT COUNT(DISTINCT product_id) as count FROM validations WHERE passed = FALSE"
    )['count']
    
    recent_violations = Database.execute_query(
        "SELECT * FROM validations WHERE passed = FALSE ORDER BY checked_at DESC LIMIT 10"
    )
    
    return jsonify({
        'total_products_scanned': total_products,
        'compliant_products': total_products - products_with_violations,
        'non_compliant_products': products_with_violations,
        'compliance_rate': round((1 - products_with_violations / total_products) * 100, 2) if total_products > 0 else 0,
        'recent_violations': recent_violations
    })

@dashboard_bp.route('/export/violations', methods=['GET'])
def export_violations():
    """Export violations as CSV"""
    violations = Database.execute_query("""
        SELECT p.product_id, p.title, p.seller, p.marketplace,
               v.rule_id, v.rule_desc, v.severity, v.details, v.checked_at
        FROM validations v
        JOIN products p ON v.product_id = p.product_id
        WHERE v.passed = FALSE
    """)
    
    df = pd.DataFrame(violations)
    
    output = io.BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='violations_report.csv')
