import os
import requests
import base64
from PIL import Image
import io
from config import Config

class GoogleVisionService:
    def __init__(self):
        self.api_key = Config.GOOGLE_VISION_API_KEY
        self.endpoint = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
    
    def extract_text_from_image(self, image_path):
        """Extract text from image using Google Vision API with API key"""
        try:
            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_content = image_file.read()
            
            encoded_image = base64.b64encode(image_content).decode('utf-8')
            
            # Prepare request
            request_body = {
                "requests": [
                    {
                        "image": {
                            "content": encoded_image
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 50
                            }
                        ]
                    }
                ]
            }
            
            # Make API call
            response = requests.post(self.endpoint, json=request_body)
            result = response.json()
            
            if 'error' in result:
                raise Exception(f"Vision API error: {result['error']}")
            
            responses = result.get('responses', [])
            if not responses or 'textAnnotations' not in responses[0]:
                return {
                    'full_text': '',
                    'confidence': 0,
                    'blocks': []
                }
            
            text_annotations = responses[0]['textAnnotations']
            
            # First annotation contains full text
            full_text = text_annotations[0]['description'] if text_annotations else ''
            
            # Extract individual blocks
            blocks = []
            for annotation in text_annotations[1:]:
                vertices = annotation.get('boundingPoly', {}).get('vertices', [])
                if len(vertices) >= 4:
                    blocks.append({
                        'text': annotation['description'],
                        'confidence': 0.95,
                        'bbox': {
                            'x': vertices[0].get('x', 0),
                            'y': vertices[0].get('y', 0),
                            'width': vertices[2].get('x', 0) - vertices[0].get('x', 0),
                            'height': vertices[2].get('y', 0) - vertices[0].get('y', 0)
                        }
                    })
            
            return {
                'full_text': full_text,
                'confidence': 0.95,
                'blocks': blocks
            }
        
        except Exception as e:
            print(f"Error in Google Vision OCR: {e}")
            return {
                'full_text': '',
                'confidence': 0,
                'blocks': []
            }
    
    def detect_labels(self, image_path):
        """Detect labels and objects in image"""
        try:
            with open(image_path, 'rb') as image_file:
                image_content = image_file.read()
            
            encoded_image = base64.b64encode(image_content).decode('utf-8')
            
            request_body = {
                "requests": [
                    {
                        "image": {"content": encoded_image},
                        "features": [
                            {"type": "LABEL_DETECTION", "maxResults": 10},
                            {"type": "OBJECT_LOCALIZATION", "maxResults": 10}
                        ]
                    }
                ]
            }
            
            response = requests.post(self.endpoint, json=request_body)
            result = response.json()
            
            responses = result.get('responses', [])
            if not responses:
                return {'labels': [], 'objects': []}
            
            labels = []
            if 'labelAnnotations' in responses[0]:
                for label in responses[0]['labelAnnotations']:
                    labels.append({
                        'description': label['description'],
                        'score': label['score']
                    })
            
            objects = []
            if 'localizedObjectAnnotations' in responses[0]:
                for obj in responses[0]['localizedObjectAnnotations']:
                    objects.append({
                        'name': obj['name'],
                        'score': obj['score']
                    })
            
            return {
                'labels': labels,
                'objects': objects
            }
        
        except Exception as e:
            print(f"Error in label detection: {e}")
            return {'labels': [], 'objects': []}
