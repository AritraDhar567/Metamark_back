from flask import Blueprint, request, jsonify
from models.database import Database

entities_bp = Blueprint('entities', __name__)

@entities_bp.route('/', methods=['GET'])
def get_all_entities():
    """Get all entities with their compliance stats"""
    entity_type = request.args.get('type')  # manufacturer, importer, packer
    
    if entity_type:
        entities = Database.execute_query(
            """SELECT * FROM entities 
               WHERE entity_type = %s 
               ORDER BY avg_compliance_score DESC""",
            (entity_type,)
        )
    else:
        entities = Database.execute_query(
            "SELECT * FROM entities ORDER BY avg_compliance_score DESC"
        )
    
    return jsonify(entities)

@entities_bp.route('/<int:entity_id>', methods=['GET'])
def get_entity_details(entity_id):
    """Get entity details with all associated products"""
    entity = Database.execute_one(
        "SELECT * FROM entities WHERE id = %s",
        (entity_id,)
    )
    
    if not entity:
        return jsonify({'error': 'Entity not found'}), 404
    
    # Get products based on entity type
    entity_type = entity['entity_type']
    
    if entity_type == 'manufacturer':
        products = Database.execute_query(
            """SELECT product_id, title, compliance_grade, compliance_score, 
                      listed_price, marketplace, last_validated_at
               FROM products 
               WHERE manufacturer LIKE %s
               ORDER BY last_validated_at DESC""",
            (f"%{entity['name']}%",)
        )
    elif entity_type == 'importer':
        products = Database.execute_query(
            """SELECT product_id, title, compliance_grade, compliance_score, 
                      listed_price, marketplace, last_validated_at
               FROM products 
               WHERE importer LIKE %s
               ORDER BY last_validated_at DESC""",
            (f"%{entity['name']}%",)
        )
    else:  # packer
        products = Database.execute_query(
            """SELECT product_id, title, compliance_grade, compliance_score, 
                      listed_price, marketplace, last_validated_at
               FROM products 
               WHERE packer LIKE %s
               ORDER BY last_validated_at DESC""",
            (f"%{entity['name']}%",)
        )
    
    return jsonify({
        'entity': entity,
        'products': products,
        'total_products': len(products)
    })

@entities_bp.route('/search', methods=['GET'])
def search_entities():
    """Search entities by name"""
    query = request.args.get('q', '')
    entity_type = request.args.get('type')
    
    if entity_type:
        entities = Database.execute_query(
            """SELECT * FROM entities 
               WHERE name LIKE %s AND entity_type = %s
               ORDER BY avg_compliance_score DESC""",
            (f"%{query}%", entity_type)
        )
    else:
        entities = Database.execute_query(
            """SELECT * FROM entities 
               WHERE name LIKE %s
               ORDER BY avg_compliance_score DESC""",
            (f"%{query}%",)
        )
    
    return jsonify(entities)

@entities_bp.route('/refresh', methods=['POST'])
def refresh_entity_stats():
    """Recalculate compliance stats for all entities"""
    from services.entity_tracker import EntityTracker
    
    tracker = EntityTracker()
    result = tracker.refresh_all_entities()
    
    return jsonify(result)
