import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from config import Config
import os

class ImagePreprocessor:
    def __init__(self):
        self.target_size = (1024, 1024)
    
    def preprocess(self, image_path):
        """Main preprocessing pipeline"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        img = self._resize_image(img)
        img = self._enhance_contrast(img)
        img = self._denoise(img)
        
        return img
    
    def preprocess_for_ocr(self, image):
        """Specific preprocessing for OCR"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        kernel = np.ones((2, 2), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        return opening
    
    def _resize_image(self, img):
        """Resize image maintaining aspect ratio"""
        h, w = img.shape[:2]
        target_h, target_w = self.target_size
        
        scale = min(target_w / w, target_h / h)
        
        if scale < 1:
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return img
    
    def _enhance_contrast(self, img):
        """Enhance image contrast using CLAHE"""
        if len(img.shape) == 2:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            return clahe.apply(img)
        else:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            lab = cv2.merge([l, a, b])
            return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    
    def _denoise(self, img):
        """Apply denoising"""
        if len(img.shape) == 2:
            return cv2.fastNlMeansDenoising(img, None, 10, 7, 21)
        else:
            return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    
    def crop_region(self, image, bbox):
        """Crop image region from bounding box"""
        x1, y1, x2, y2 = map(int, bbox)
        return image[y1:y2, x1:x2]


class LabelDetector:
    def __init__(self, model_path=None):
        self.model_path = model_path or Config.YOLO_MODEL_PATH
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load YOLO model for label detection"""
        if os.path.exists(self.model_path):
            try:
                self.model = YOLO(self.model_path)
                print(f"Loaded YOLO model from {self.model_path}")
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None
        else:
            print(f"Model not found at {self.model_path}, using fallback detection")
            self.model = None
    
    def detect_labels(self, image):
        """Detect label regions in image"""
        if self.model is not None:
            return self._detect_with_yolo(image)
        else:
            return self._fallback_detection(image)
    
    def _detect_with_yolo(self, image):
        """Use YOLO model for detection"""
        results = self.model(image, conf=0.25)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': confidence,
                    'type': self._get_label_type(class_id)
                })
        
        return detections
    
    def _fallback_detection(self, image):
        """Fallback: return full image as single detection"""
        h, w = image.shape[:2]
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY_INV, 11, 2)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > (w * h * 0.05):
                x, y, cw, ch = cv2.boundingRect(contour)
                if cw > 100 and ch > 100:
                    detections.append({
                        'bbox': [x, y, x + cw, y + ch],
                        'confidence': 0.7,
                        'type': 'label'
                    })
        
        if not detections:
            detections.append({
                'bbox': [0, 0, w, h],
                'confidence': 1.0,
                'type': 'full_image'
            })
        
        return detections
    
    def _get_label_type(self, class_id):
        """Map class ID to label type"""
        label_types = {
            0: 'front_label',
            1: 'back_label',
            2: 'nutrition_panel',
            3: 'ingredient_list',
            4: 'barcode_region'
        }
        return label_types.get(class_id, 'label')
