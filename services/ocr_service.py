import easyocr
import re
from config import Config
from dateutil import parser as date_parser
from datetime import datetime

class OCREngine:
    def __init__(self):
        self.reader = easyocr.Reader(Config.OCR_LANGUAGES, gpu=False)
    
    def extract_text(self, image):
        """Extract text from image using EasyOCR"""
        try:
            results = self.reader.readtext(image, detail=1, paragraph=False)
            
            full_text = []
            details = []
            
            for (bbox, text, confidence) in results:
                if confidence >= Config.OCR_CONFIDENCE_THRESHOLD:
                    full_text.append(text)
                    details.append({
                        'text': text,
                        'confidence': float(confidence),
                        'bbox': bbox
                    })
            
            return {
                'full_text': ' '.join(full_text),
                'details': details,
                'avg_confidence': sum(d['confidence'] for d in details) / len(details) if details else 0
            }
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return {
                'full_text': '',
                'details': [],
                'avg_confidence': 0
            }
    
    def clean_text(self, text):
        """Clean and normalize OCR text"""
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('|', 'I')
        text = text.replace('0', 'O') if re.search(r'[A-Z]0[A-Z]', text) else text
        return text.strip()


class FieldExtractor:
    def __init__(self):
        self.patterns = self._init_patterns()
    
    def _init_patterns(self):
        """Initialize regex patterns for field extraction"""
        return {
            'mrp': [
                r'MRP[:\s]*₹?\s?([\d,]+(?:\.\d{2})?)',
                r'M\.?R\.?P\.?[:\s]*₹?\s?([\d,]+(?:\.\d{2})?)',
                r'Maximum Retail Price[:\s]*₹?\s?([\d,]+(?:\.\d{2})?)',
                r'₹\s?([\d,]+(?:\.\d{2})?)',
            ],
            'net_quantity': [
                r'Net (?:Wt\.?|Weight|Quantity|Qty\.?|Content)[:\s]*(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|nos|pcs|pieces))',
                r'Net[:\s]*(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|nos|pcs))',
                r'(\d+(?:\.\d+)?\s*(?:grams?|kilograms?|milliliters?|liters?))',
            ],
            'manufacturer': [
                r'Manufactured by[:\s]*([^\n]+)',
                r'Mfg\.? by[:\s]*([^\n]+)',
                r'Manufacturer[:\s]*([^\n]+)',
                r'Packed by[:\s]*([^\n]+)',
            ],
            'mfg_date': [
                r'Mfg\.? Date[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
                r'Manufacturing Date[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
                r'Date of Mfg\.?[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
                r'DOM[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
            ],
            'exp_date': [
                r'Exp\.? Date[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
                r'Expiry Date[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
                r'Best Before[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
                r'Use By[:\s]*(\d{2}[-/]\d{2}[-/]\d{4})',
            ],
            'country': [
                r'Country of Origin[:\s]*([A-Za-z\s]+)',
                r'Made in[:\s]*([A-Za-z\s]+)',
                r'Product of[:\s]*([A-Za-z\s]+)',
                r'Imported from[:\s]*([A-Za-z\s]+)',
            ],
            'consumer_care': [
                r'Consumer Care[:\s]*([^\n]+)',
                r'Customer Care[:\s]*([^\n]+)',
                r'For Complaints Contact[:\s]*([^\n]+)',
            ],
            'fssai': [
                r'FSSAI Lic\.? No\.?[:\s]*(\d+)',
                r'FSSAI[:\s]*(\d+)',
                r'Lic\.? No\.?[:\s]*(\d{14})',
            ],
        }
    
    def extract_fields(self, ocr_text):
        """Extract all fields from OCR text"""
        fields = {}
        
        text = self._clean_text(ocr_text)
        
        for field_name, patterns in self.patterns.items():
            value = self._extract_field(text, patterns)
            if value:
                fields[field_name] = value
        
        fields = self._postprocess_fields(fields)
        
        return fields
    
    def _extract_field(self, text, patterns):
        """Extract field using list of patterns"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        return None
    
    def _clean_text(self, text):
        """Clean OCR text"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s₹\-/.:,()]', '', text)
        return text
    
    def _postprocess_fields(self, fields):
        """Post-process and normalize extracted fields"""
        if 'mrp' in fields:
            fields['mrp'] = self._normalize_mrp(fields['mrp'])
        
        if 'net_quantity' in fields:
            fields['net_quantity'] = self._normalize_quantity(fields['net_quantity'])
        
        if 'mfg_date' in fields:
            fields['mfg_date'] = self._normalize_date(fields['mfg_date'])
        
        if 'exp_date' in fields:
            fields['exp_date'] = self._normalize_date(fields['exp_date'])
        
        if 'country' in fields:
            fields['country'] = fields['country'].strip().title()
        
        if 'manufacturer' in fields:
            fields['manufacturer'] = fields['manufacturer'][:200]
        
        return fields
    
    def _normalize_mrp(self, mrp_text):
        """Normalize MRP value"""
        mrp = re.sub(r'[^\d.]', '', mrp_text)
        try:
            return f"₹{float(mrp):.2f}"
        except:
            return mrp_text
    
    def _normalize_quantity(self, qty_text):
        """Normalize net quantity"""
        qty = qty_text.lower()
        qty = re.sub(r'\s+', '', qty)
        
        qty = re.sub(r'grams?', 'g', qty)
        qty = re.sub(r'kilograms?', 'kg', qty)
        qty = re.sub(r'milliliters?', 'ml', qty)
        qty = re.sub(r'liters?', 'l', qty)
        qty = re.sub(r'pieces?', 'pcs', qty)
        
        return qty
    
    def _normalize_date(self, date_text):
        """Normalize date format"""
        try:
            parsed_date = date_parser.parse(date_text, dayfirst=True)
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return date_text
