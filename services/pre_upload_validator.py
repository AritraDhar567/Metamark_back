from services.google_vision_service import GoogleVisionService
from services.gemini_validator import GeminiValidator
from config import Config

class PreUploadValidator:
    def __init__(self):
        self.vision = GoogleVisionService()
        self.gemini = GeminiValidator()
    
    def validate_product_listing(self, product_data, image_paths):
        """Validate product before upload"""
        
        # Step 1: Run OCR on all images
        all_ocr_text = ""
        ocr_results = []
        vision_analysis = []
        
        for image_path in image_paths:
            ocr_result = self.vision.extract_text_from_image(image_path)
            label_result = self.vision.detect_labels(image_path)
            
            if ocr_result['full_text']:
                all_ocr_text += ocr_result['full_text'] + "\n\n"
            
            ocr_results.append({
                'image': image_path,
                'text': ocr_result['full_text'],
                'confidence': ocr_result['confidence']
            })
            
            vision_analysis.append({
                'image': image_path,
                'labels': label_result['labels'][:5],
                'objects': label_result['objects'][:5]
            })
        
        # Step 2: Validate with Gemini
        gemini_result = self.gemini.validate_product_text(
            product_data,
            {'full_text': all_ocr_text}
        )
        
        # Step 3: Additional checks
        issues = []
        warnings = []
        suggestions = []
        
        # Check for missing critical fields
        critical_fields = ['title', 'listed_price', 'manufacturer', 'country_of_origin']
        for field in critical_fields:
            if not product_data.get(field):
                issues.append({
                    'field': field,
                    'severity': 'high',
                    'message': f'{field.replace("_", " ").title()} is required',
                    'recommendation': f'Please provide {field.replace("_", " ")}'
                })
        
        # Check image quality
        if len(image_paths) < 3:
            warnings.append({
                'type': 'image_count',
                'severity': 'medium',
                'message': 'Consider uploading at least 3 images',
                'recommendation': 'Add more product images showing different angles'
            })
        
        # Check if labels are visible in images
        has_labels = any(
            any(label['description'].lower() in ['label', 'text', 'package'] 
                for label in img['labels'])
            for img in vision_analysis
        )
        
        if not has_labels:
            warnings.append({
                'type': 'label_visibility',
                'severity': 'high',
                'message': 'Product labels not clearly visible in images',
                'recommendation': 'Include clear photos of product labels showing MRP, manufacturer details'
            })
        
        # Compile suggestions from Gemini
        for violation in gemini_result.get('violations', []):
            suggestions.append({
                'rule': violation['rule'],
                'severity': violation['severity'],
                'issue': violation['description'],
                'fix': violation['recommendation']
            })
        
        # Calculate readiness score
        total_checks = len(critical_fields) + 3  # Critical fields + 3 quality checks
        passed_checks = sum(1 for field in critical_fields if product_data.get(field))
        passed_checks += len(image_paths) >= 3
        passed_checks += has_labels
        passed_checks += gemini_result.get('compliance_score', 0) >= 70
        
        readiness_score = (passed_checks / total_checks * 100)
        
        can_upload = (
            readiness_score >= 60 and
            len(issues) == 0 and
            gemini_result.get('compliance_score', 0) >= Config.COMPLIANCE_THRESHOLD
        )
        
        return {
            'can_upload': can_upload,
            'readiness_score': round(readiness_score, 2),
            'estimated_grade': gemini_result.get('final_grade', 'N/A'),
            'compliance_score': gemini_result.get('compliance_score'),
            'status': gemini_result.get('status'),
            'issues': issues,
            'warnings': warnings,
            'suggestions': suggestions,
            'gemini_analysis': {
                'assessment': gemini_result.get('overall_assessment'),
                'extracted_from_ocr': gemini_result.get('extracted_from_ocr'),
                'grade_explanation': gemini_result.get('grade_explanation')
            },
            'vision_analysis': vision_analysis,
            'ocr_summary': {
                'total_text_extracted': len(all_ocr_text),
                'images_processed': len(image_paths)
            }
        }
