import re
from datetime import datetime
from dateutil import parser as date_parser

class RuleEngine:
    def __init__(self):
        self.rules = self._init_rules()
    
    def _init_rules(self):
        """Initialize validation rules"""
        return [
            {
                'rule_id': 'R001',
                'name': 'MRP Presence',
                'description': 'MRP must be present on packaging',
                'category': 'mrp',
                'severity': 'critical',
                'validator': self._validate_mrp_presence
            },
            {
                'rule_id': 'R002',
                'name': 'MRP Format',
                'description': 'MRP must include currency symbol and be valid',
                'category': 'mrp',
                'severity': 'high',
                'validator': self._validate_mrp_format
            },
            {
                'rule_id': 'R003',
                'name': 'Net Quantity Presence',
                'description': 'Net quantity must be declared',
                'category': 'quantity',
                'severity': 'critical',
                'validator': self._validate_quantity_presence
            },
            {
                'rule_id': 'R004',
                'name': 'Net Quantity Unit',
                'description': 'Net quantity must use standard units',
                'category': 'quantity',
                'severity': 'high',
                'validator': self._validate_quantity_unit
            },
            {
                'rule_id': 'R005',
                'name': 'Manufacturer Name',
                'description': 'Manufacturer name and address must be present',
                'category': 'manufacturer',
                'severity': 'critical',
                'validator': self._validate_manufacturer
            },
            {
                'rule_id': 'R006',
                'name': 'Country of Origin',
                'description': 'Country of origin must be declared for imported goods',
                'category': 'country',
                'severity': 'high',
                'validator': self._validate_country
            },
            {
                'rule_id': 'R007',
                'name': 'Manufacturing Date',
                'description': 'Manufacturing or packing date should be present',
                'category': 'date',
                'severity': 'medium',
                'validator': self._validate_mfg_date
            },
            {
                'rule_id': 'R008',
                'name': 'Date Format',
                'description': 'Dates must be in valid format',
                'category': 'date',
                'severity': 'medium',
                'validator': self._validate_date_format
            },
            {
                'rule_id': 'R009',
                'name': 'Consumer Care',
                'description': 'Consumer care details should be present',
                'category': 'consumer_care',
                'severity': 'low',
                'validator': self._validate_consumer_care
            },
            {
                'rule_id': 'R010',
                'name': 'FSSAI License',
                'description': 'FSSAI license number required for food products',
                'category': 'fssai',
                'severity': 'high',
                'validator': self._validate_fssai
            },
        ]
    
    def validate_all(self, extracted_fields, product_category=None):
        """Run all validation rules"""
        results = []
        
        for rule in self.rules:
            if rule['rule_id'] == 'R010' and product_category and 'food' not in product_category.lower():
                continue
            
            passed, details = rule['validator'](extracted_fields)
            
            results.append({
                'rule_id': rule['rule_id'],
                'rule_name': rule['name'],
                'rule_desc': rule['description'],
                'category': rule['category'],
                'severity': rule['severity'],
                'passed': passed,
                'details': details
            })
        
        return results
    
    def _validate_mrp_presence(self, fields):
        """Check if MRP is present"""
        has_mrp = 'mrp' in fields and fields['mrp']
        details = "MRP found" if has_mrp else "MRP not found on packaging"
        return has_mrp, details
    
    def _validate_mrp_format(self, fields):
        """Validate MRP format"""
        if 'mrp' not in fields or not fields['mrp']:
            return False, "MRP not found"
        
        mrp = fields['mrp']
        has_currency = '₹' in mrp or 'INR' in mrp.upper() or 'RS' in mrp.upper()
        
        numeric = re.sub(r'[^\d.]', '', mrp)
        try:
            value = float(numeric)
            is_valid = value > 0
        except:
            is_valid = False
        
        passed = has_currency and is_valid
        details = "Valid MRP format" if passed else "MRP format invalid or missing currency"
        
        return passed, details
    
    def _validate_quantity_presence(self, fields):
        """Check if net quantity is present"""
        has_qty = 'net_quantity' in fields and fields['net_quantity']
        details = "Net quantity declared" if has_qty else "Net quantity not found"
        return has_qty, details
    
    def _validate_quantity_unit(self, fields):
        """Validate quantity uses standard units"""
        if 'net_quantity' not in fields or not fields['net_quantity']:
            return False, "Net quantity not found"
        
        qty = fields['net_quantity'].lower()
        standard_units = ['g', 'kg', 'ml', 'l', 'nos', 'pcs']
        
        has_standard_unit = any(unit in qty for unit in standard_units)
        has_valid_format = bool(re.search(r'\d+(?:\.\d+)?\s*(?:g|kg|ml|l|nos|pcs)', qty))
        
        passed = has_standard_unit and has_valid_format
        details = "Standard unit used" if passed else f"Non-standard unit or format: {qty}"
        
        return passed, details
    
    def _validate_manufacturer(self, fields):
        """Check manufacturer info"""
        has_mfg = 'manufacturer' in fields and fields['manufacturer']
        
        if has_mfg:
            is_complete = len(fields['manufacturer']) > 10
            passed = is_complete
            details = "Manufacturer info present" if passed else "Manufacturer info incomplete"
        else:
            passed = False
            details = "Manufacturer information not found"
        
        return passed, details
    
    def _validate_country(self, fields):
        """Validate country of origin"""
        has_country = 'country' in fields and fields['country']
        
        if has_country:
            country = fields['country'].strip()
            is_valid = len(country) >= 3 and country.replace(' ', '').isalpha()
            passed = is_valid
            details = f"Country: {country}" if passed else "Invalid country format"
        else:
            passed = True
            details = "Country of origin not specified (may be required for imported goods)"
        
        return passed, details
    
    def _validate_mfg_date(self, fields):
        """Check manufacturing date presence"""
        has_mfg_date = 'mfg_date' in fields and fields['mfg_date']
        has_exp_date = 'exp_date' in fields and fields['exp_date']
        
        passed = has_mfg_date or has_exp_date
        details = "Date information present" if passed else "No manufacturing or expiry date found"
        
        return passed, details
    
    def _validate_date_format(self, fields):
        """Validate date formats"""
        dates_to_check = []
        
        if 'mfg_date' in fields and fields['mfg_date']:
            dates_to_check.append(('Manufacturing', fields['mfg_date']))
        
        if 'exp_date' in fields and fields['exp_date']:
            dates_to_check.append(('Expiry', fields['exp_date']))
        
        if not dates_to_check:
            return True, "No dates to validate"
        
        invalid_dates = []
        for date_type, date_str in dates_to_check:
            try:
                parsed = date_parser.parse(date_str, dayfirst=True)
                current_year = datetime.now().year
                if parsed.year < 2000 or parsed.year > current_year + 10:
                    invalid_dates.append(f"{date_type}: {date_str}")
            except:
                invalid_dates.append(f"{date_type}: {date_str}")
        
        passed = len(invalid_dates) == 0
        details = "Valid date formats" if passed else f"Invalid dates: {', '.join(invalid_dates)}"
        
        return passed, details
    
    def _validate_consumer_care(self, fields):
        """Check consumer care details"""
        has_consumer_care = 'consumer_care' in fields and fields['consumer_care']
        
        if has_consumer_care:
            has_contact = bool(re.search(r'\d{10}|\d{3}-\d{3}-\d{4}|@', fields['consumer_care']))
            passed = has_contact
            details = "Consumer care details present" if passed else "Consumer care incomplete"
        else:
            passed = False
            details = "Consumer care details not found"
        
        return passed, details
    
    def _validate_fssai(self, fields):
        """Validate FSSAI license number"""
        has_fssai = 'fssai' in fields and fields['fssai']
        
        if has_fssai:
            fssai = re.sub(r'\D', '', fields['fssai'])
            is_valid = len(fssai) == 14 and fssai.isdigit()
            passed = is_valid
            details = f"FSSAI: {fssai}" if passed else f"Invalid FSSAI format: {fields['fssai']}"
        else:
            passed = False
            details = "FSSAI license not found"
        
        return passed, details
