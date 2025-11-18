import json
from datetime import datetime, date
from decimal import Decimal

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def format_response(data, message="Success", status_code=200):
    return {
        'status': 'success' if status_code < 400 else 'error',
        'message': message,
        'data': data
    }, status_code

def format_error(message, status_code=400):
    return {
        'status': 'error',
        'message': message,
        'data': None
    }, status_code
