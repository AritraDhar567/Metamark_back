from models.database import Database
import re

class EntityTracker:
    def __init__(self):
        self.entity_types = ['manufacturer', 'importer', 'packer']
    
    def refresh_all_entities(self):
        """Scan all products and update entity statistics"""
        
        # Clear existing entities
        Database.execute_update("DELETE FROM entities", ())
        
        # Track manufacturers
        self._track_entities('manufacturer')
        
        # Track importers
        self._track_entities('importer')
        
        # Track packers
        self._track_entities('packer')
        
        entity_count = Database.execute_one("SELECT COUNT(*) as count FROM entities", ())
        
        return {
            'success': True,
            'message': f'Refreshed {entity_count["count"]} entities',
            'total_entities': entity_count['count']
        }
    
    def _track_entities(self, entity_type):
        """Track entities of a specific type"""
        
        # Get all unique entities from products
        field_name = entity_type
        
        # Build query based on entity type
        if entity_type == 'importer':
            products = Database.execute_query(
                f"""SELECT product_id, {field_name}, compliance_score, compliance_grade, 
                        importer_email as email, importer_phone as phone
                    FROM products 
                    WHERE {field_name} IS NOT NULL AND {field_name} != ''""",
                ()
            )
        else:
            # Manufacturer and packer don't have separate email/phone fields
            products = Database.execute_query(
                f"""SELECT product_id, {field_name}, compliance_score, compliance_grade
                    FROM products 
                    WHERE {field_name} IS NOT NULL AND {field_name} != ''""",
                ()
            )
        
        # Group by entity name
        entity_stats = {}
        
        for product in products:
            entity_name = product.get(field_name)
            if not entity_name:
                continue
            
            # Clean entity name
            entity_name = self._clean_entity_name(entity_name)
            
            if entity_name not in entity_stats:
                entity_stats[entity_name] = {
                    'name': entity_name,
                    'type': entity_type,
                    'email': product.get('email') if entity_type == 'importer' else None,
                    'phone': product.get('phone') if entity_type == 'importer' else None,
                    'scores': [],
                    'grades': [],
                    'total': 0,
                    'compliant': 0,
                    'non_compliant': 0
                }
            
            stats = entity_stats[entity_name]
            stats['total'] += 1
            
            if product.get('compliance_score'):
                stats['scores'].append(float(product['compliance_score']))
            
            if product.get('compliance_grade'):
                stats['grades'].append(product['compliance_grade'])
                
                # Count compliant vs non-compliant
                grade = product['compliance_grade']
                if grade in ['A+', 'A', 'A-', 'B+', 'B']:
                    stats['compliant'] += 1
                else:
                    stats['non_compliant'] += 1
        
        # Insert entities
        for entity_name, stats in entity_stats.items():
            avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else None
            
            # Calculate most common grade
            if stats['grades']:
                avg_grade = max(set(stats['grades']), key=stats['grades'].count)
            else:
                avg_grade = None
            
            # Extract address from name (if present)
            address = self._extract_address(stats['name'])
            
            insert_query = """
                INSERT INTO entities (entity_type, name, address, email, phone, 
                                    avg_compliance_score, avg_compliance_grade, 
                                    total_products, compliant_products, non_compliant_products)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            Database.execute_insert(insert_query, (
                entity_type,
                stats['name'][:500],
                address[:1000] if address else None,
                stats['email'],
                stats['phone'],
                avg_score,
                avg_grade,
                stats['total'],
                stats['compliant'],
                stats['non_compliant']
            ))

    
    def _clean_entity_name(self, name):
        """Clean and normalize entity name"""
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove common suffixes for grouping
        name = re.sub(r'\s*(Pvt\.?|Ltd\.?|Limited|Inc\.?|Corp\.?)\s*$', '', name, flags=re.IGNORECASE)
        
        return name
    
    def _extract_address(self, text):
        """Extract address from entity name if present"""
        # If text contains comma-separated parts, consider it an address
        if ',' in text:
            parts = text.split(',')
            if len(parts) > 2:
                return text
        return None
