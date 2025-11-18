from flask import Blueprint, jsonify
from models.database import Database

validation_bp = Blueprint('validation', __name__)

@validation_bp.route('/product/<product_id>', methods=['GET'])
def get_product_validations(product_id):
    """Get all validations for a product"""
    validations = Database.execute_query(
        "SELECT * FROM validations WHERE product_id = %s",
        (product_id,)
    )
    return jsonify(validations)

@validation_bp.route('/violations', methods=['GET'])
def get_violations():
    """Get all violations"""
    violations = Database.execute_query(
        "SELECT * FROM validations WHERE passed = FALSE ORDER BY checked_at DESC"
    )
    return jsonify(violations)

@validation_bp.route('/stats', methods=['GET'])
def get_validation_stats():
    """Get validation statistics"""
    stats = {}
    
    stats['total_products'] = Database.execute_one(
        "SELECT COUNT(*) as count FROM products"
    )['count']
    
    stats['total_validations'] = Database.execute_one(
        "SELECT COUNT(*) as count FROM validations"
    )['count']
    
    stats['total_violations'] = Database.execute_one(
        "SELECT COUNT(*) as count FROM validations WHERE passed = FALSE"
    )['count']
    
    if stats['total_validations'] > 0:
        stats['pass_rate'] = round((1 - stats['total_violations'] / stats['total_validations']) * 100, 2)
    else:
        stats['pass_rate'] = 0
    
    stats['violations_by_category'] = Database.execute_query("""
        SELECT rule_id, rule_desc, COUNT(*) as count
        FROM validations
        WHERE passed = FALSE
        GROUP BY rule_id, rule_desc
    """)
    
    stats['violations_by_severity'] = Database.execute_query("""
        SELECT severity, COUNT(*) as count
        FROM validations
        WHERE passed = FALSE
        GROUP BY severity
    """)
    
    return jsonify(stats)
