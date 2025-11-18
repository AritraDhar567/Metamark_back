from services.google_vision_service import GoogleVisionService
from services.gemini_validator import GeminiValidator
from models.database import Database
from config import Config
import json

class ComplianceEngine:
    def __init__(self):
        self.vision = GoogleVisionService()
        self.gemini = GeminiValidator()
    
    def validate_product(self, product_id):
        """Two-step validation: Vision OCR + Gemini Text Analysis"""
        
        # Step 1: Get product data
        product = Database.execute_one(
            "SELECT * FROM products WHERE product_id = %s",
            (product_id,)
        )
        
        if not product:
            return {'error': 'Product not found'}
        
        # Step 2: Get ALL images from the latest upload batch (within 1 minute window)
        images = Database.execute_query("""
            SELECT * FROM images
            WHERE product_id = %s 
            AND uploaded_at >= (
                SELECT DATE_SUB(MAX(uploaded_at), INTERVAL 1 MINUTE)
                FROM images 
                WHERE product_id = %s
            )
            ORDER BY uploaded_at DESC, id
        """, (product_id, product_id))
        
        # Debug: Log how many images were retrieved
        print(f"DEBUG: Retrieved {len(images)} images for product {product_id}")
        for img in images:
            print(f"  - Image ID: {img.get('id')}, uploaded_at: {img.get('uploaded_at')}, storage_path: {img.get('storage_path')}")
        
        if not images:
            return {'error': 'No images found for product'}
        
        all_ocr_results = []
        combined_ocr_text = ""
        vision_analysis = []
        
        # Step 3: Process each image with Google Vision
        for image in images:
            print(f"DEBUG: Processing image ID {image['id']}")
            
            if not image['storage_path']:
                print(f"  - SKIPPED: No storage_path for image {image['id']}")
                continue
            
            print(f"  - Storage path exists: {image['storage_path']}")
            ocr_result = self.vision.extract_text_from_image(image['storage_path'])
            print(f"  - OCR result: {len(ocr_result.get('full_text', ''))} characters extracted")
            
            if ocr_result['full_text']:
                combined_ocr_text += ocr_result['full_text'] + "\n\n"
                label_result = self.vision.detect_labels(image['storage_path'])
                
                ocr_query = """
                    INSERT INTO ocr_results (image_id, crop_type, ocr_text, extracted, confidence)
                    VALUES (%s, %s, %s, %s, %s)
                """
                ocr_id = Database.execute_insert(ocr_query, (
                    image['id'],
                    'full_image',
                    ocr_result['full_text'],
                    json.dumps(label_result),
                    ocr_result['confidence']
                ))
                
                print(f"  - SUCCESS: Image {image['id']} processed, OCR ID: {ocr_id}")
                
                all_ocr_results.append({
                    'image_id': image['id'],
                    'ocr_id': ocr_id,
                    'image_url': image['image_url'],
                    'uploaded_at': str(image['uploaded_at']),  # Include timestamp for reference
                    'text': ocr_result['full_text'],
                    'labels': label_result['labels'],
                    'objects': label_result['objects']
                })
                vision_analysis.append({
                    'image_id': image['id'],
                    'image_url': image['image_url'],
                    'uploaded_at': str(image['uploaded_at']),  # Include timestamp for reference
                    'labels': label_result['labels'][:5],
                    'objects': label_result['objects'][:5]
                })
            else:
                print(f"  - SKIPPED: No text extracted from image {image['id']}")

        
        # Step 4: Validate with Gemini AI
        gemini_result = self.gemini.validate_product_text(
            product,
            {'full_text': combined_ocr_text}
        )
        
        # Step 5: Combine Vision + Gemini results
        validation_results = []
        
        # Add Gemini violations
        for violation in gemini_result.get('violations', []):
            validation_results.append({
                'rule_id': f"GEMINI_{violation['rule'].upper().replace(' ', '_')}",
                'rule_desc': violation['rule'],
                'passed': False,
                'severity': violation['severity'],
                'details': violation['description'],
                'recommendation': violation['recommendation'],
                'source': 'Gemini AI'
            })
        
        # Add Gemini passed checks
        for check in gemini_result.get('passed_checks', []):
            validation_results.append({
                'rule_id': f"GEMINI_{check['rule'].upper().replace(' ', '_')}",
                'rule_desc': check['rule'],
                'passed': True,
                'severity': 'low',
                'details': check['detail'],
                'recommendation': 'Compliant',
                'source': 'Gemini AI'
            })
        
        # Additional Vision-based checks
        has_product_labels = any(
            any(label['description'].lower() in ['product', 'package', 'label', 'text', 'font'] 
                for label in img['labels'])
            for img in vision_analysis
        )
        
        if has_product_labels:
            validation_results.append({
                'rule_id': 'VISION_LABEL_PRESENT',
                'rule_desc': 'Product label detected in images',
                'passed': True,
                'severity': 'low',
                'details': 'Google Vision detected product labeling in images',
                'recommendation': 'Good',
                'source': 'Google Vision'
            })
        else:
            validation_results.append({
                'rule_id': 'VISION_LABEL_MISSING',
                'rule_desc': 'Product label not clearly visible',
                'passed': False,
                'severity': 'medium',
                'details': 'Could not detect clear product labels in images',
                'recommendation': 'Ensure product labels are clearly visible in images',
                'source': 'Google Vision'
            })
        
        # Step 6: Save all validations to database
        for val in validation_results:
            val_query = """
                INSERT INTO validations (product_id, ocr_id, rule_id, rule_desc, passed, severity, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            Database.execute_insert(val_query, (
                product_id,
                all_ocr_results[0]['ocr_id'] if all_ocr_results else None,
                val['rule_id'],
                val['rule_desc'],
                val['passed'],
                val['severity'],
                f"{val['details']} | Recommendation: {val.get('recommendation', 'N/A')}"
            ))
        
        # Step 7: Calculate final compliance
        total_checks = len(validation_results)
        passed_checks = sum(1 for v in validation_results if v['passed'])
        compliance_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        final_score = gemini_result.get('compliance_score', compliance_rate)
        final_status = 'COMPLIANT' if final_score >= Config.COMPLIANCE_THRESHOLD else 'NON_COMPLIANT'
        final_grade = gemini_result.get('final_grade', 'N/A')
        
        # Step 8: Update product table with compliance score and grade
        update_product_query = """
            UPDATE products 
            SET compliance_grade = %s,
                compliance_score = %s,
                last_validated_at = NOW()
            WHERE product_id = %s
        """
        Database.execute_update(update_product_query, (final_grade, final_score, product_id))
        
        return {
            'product_id': product_id,
            'compliance_score': final_score,
            'status': final_status,
            'final_grade': final_grade,
            'grade_explanation': gemini_result.get('grade_explanation', ''),
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': total_checks - passed_checks,
            'images_processed': len(images),  # Added for clarity
            'gemini_analysis': {
                'score': gemini_result.get('compliance_score'),
                'status': gemini_result.get('status'),
                'assessment': gemini_result.get('overall_assessment'),
                'extracted_from_ocr': gemini_result.get('extracted_from_ocr'),
                'final_grade': gemini_result.get('final_grade'),
                'grade_explanation': gemini_result.get('grade_explanation')
            },
            'vision_analysis': vision_analysis,
            'ocr_results': all_ocr_results,
            'validations': validation_results
        }