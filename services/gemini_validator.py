from google import genai
from config import Config
import json
import re

class GeminiValidator:
    def __init__(self):
        # NOTE: Ensure 'Config.GOOGLE_GEMINI_API_KEY' is correctly defined.
        self.client = genai.Client(api_key=Config.GOOGLE_GEMINI_API_KEY)
    
    def validate_product_text(self, product_data, ocr_data):
        """Validate product data using Gemini AI - LENIENT MODE"""
        
        # --- SAFETY FIX 1: Pre-process and truncate long strings ---
        # This prevents potential f-string parsing issues if the string contents are complex.
        description = product_data.get('description', 'N/A')
        description_snippet = description[:500] if isinstance(description, str) else 'N/A'
        
        ocr_text = ocr_data.get('full_text', 'No text extracted')
        ocr_snippet = ocr_text[:2000] if isinstance(ocr_text, str) else 'No text extracted'

        prompt = f"""
You are a Legal Metrology compliance expert for e-commerce in India. Analyze the product information and provide a BALANCED, FAIR assessment considering the product category and typical industry practices.

PRODUCT INFORMATION:
- Title: {product_data.get('title', 'N/A')}
- Listed Price: ₹{product_data.get('listed_price', 'N/A')}
- Category: {product_data.get('category', 'N/A')}
- Seller: {product_data.get('seller', 'N/A')}
- Marketplace: {product_data.get('marketplace', 'N/A')}
- Description: {description_snippet}
- Country of Origin: {product_data.get('country_of_origin', 'N/A')}
- Manufacturer: {product_data.get('manufacturer', 'N/A')}
- Publisher: {product_data.get('publisher', 'N/A')}
- ISBN-10: {product_data.get('isbn_10', 'N/A')}
- ISBN-13: {product_data.get('isbn_13', 'N/A')}
- Packer: {product_data.get('packer', 'N/A')}
- Importer: {product_data.get('importer', 'N/A')}
- Importer Email: {product_data.get('importer_email', 'N/A')}
- Importer Phone: {product_data.get('importer_phone', 'N/A')}
- Generic Name: {product_data.get('generic_name', 'N/A')}

OCR TEXT FROM PRODUCT IMAGES:
{ocr_snippet}

COMPLIANCE GUIDELINES (Be practical and category-aware):

**For BOOKS:**
- MRP: Should be printed on back cover (check if visible in OCR)
- Required: ISBN, Publisher, Author, Title
- Country of Origin: Recommended but not always mandatory for books
- Importer: Required if imported, with contact details
- Language: Not mandatory to display

**For ELECTRONICS/AUDIO:**
- MRP: Mandatory on packaging
- Required: Manufacturer/Importer with address, Country of Origin, Net Quantity
- Generic Name: Required (e.g., "Bluetooth Earphones")

**For FOOD:**
- MRP: Mandatory
- Required: FSSAI, Manufacturer/Packer, Net Quantity, Best Before, Ingredients

**For FASHION:**
- MRP: Mandatory
- Required: Manufacturer, Country of Origin, Size/Dimensions

IMPORTANT:
- Be lenient if information is present EITHER in product listing OR on packaging
- Consider if the missing information is actually required for this category
- Only flag severe violations (e.g., listed price > MRP)
- Books and digital products have relaxed requirements

Return ONLY valid JSON:
{{
    "compliance_score": <0-100, be generous>,
    "status": "COMPLIANT" or "PARTIAL" or "NON_COMPLIANT",
    "violations": [
        {{
            "rule": "rule name",
            "severity": "high" or "medium" or "low",
            "description": "what is wrong",
            "recommendation": "how to fix",
            "category_specific": true/false
        }}
    ],
    "passed_checks": [
        {{
            "rule": "rule name",
            "detail": "what is correct"
        }}
    ],
    "extracted_from_ocr": {{
        "mrp": "value or null",
        "net_quantity": "value or null",
        "manufacturer": "value or null",
        "country_of_origin": "value or null",
        "isbn": "value or null",
        "publisher": "value or null",
        "fssai": "value or null"
    }},
    "overall_assessment": "1-2 sentence balanced summary",
    "final_grade": "A+/A/A-/B+/B/B-/C+/C/D/F",
    "grade_explanation": "Brief explanation of the grade"
}}
"""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            
            text = response.text.strip()
            
            # --- FIX 2: Corrected and robust regex for removing markdown fences ---
            # Removes leading/trailing code fences (e.g., ```json or ```) and whitespace.
            text = re.sub(r'^\s*```(?:json)?\s*|\s*```\s*$', '', text, flags=re.DOTALL | re.IGNORECASE).strip()
            
            # --- FIX 3: Robust JSON extraction ---
            # Try to find the JSON object first, then try the whole text as a fallback.
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                # If no match is found, try to parse the entire cleaned text
                return json.loads(text)
        
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            # Added back 'text' printing for debugging (must ensure 'text' is defined)
            print(f"Response text: {text[:500] if 'text' in locals() else 'No response'}")
            return {
                'compliance_score': 70,
                'status': 'PARTIAL',
                'violations': [{'rule': 'JSON Parse Error', 'severity': 'medium', 'description': f'AI response could not be parsed as JSON: {e}', 'recommendation': 'Manual review required'}],
                'passed_checks': [],
                'extracted_from_ocr': {},
                'overall_assessment': 'Unable to parse AI response',
                'final_grade': 'C',
                'grade_explanation': 'Analysis completed with errors'
            }
        
        except Exception as e:
            # General exception handling remains the same
            print(f"Error in Gemini validation: {e}")
            import traceback
            traceback.print_exc()
            return {
                'compliance_score': 0,
                'status': 'ERROR',
                'violations': [{'rule': 'API Error', 'severity': 'high', 'description': str(e), 'recommendation': 'Check API'}],
                'passed_checks': [],
                'extracted_from_ocr': {},
                'overall_assessment': f'Error: {str(e)}',
                'final_grade': 'F',
                'grade_explanation': 'System error during analysis'
            }