import requests
import os
from PIL import Image
from io import BytesIO
from config import Config
import hashlib

class ImageDownloader:
    def __init__(self, storage_path=None):
        self.storage_path = storage_path or Config.UPLOAD_FOLDER
        os.makedirs(self.storage_path, exist_ok=True)
    
    def download_image(self, url, product_id):
        """Download image from URL and save locally"""
        try:
            response = requests.get(url, timeout=10, stream=True)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{product_id}_{url_hash}.jpg"
            filepath = os.path.join(self.storage_path, filename)
            
            img.save(filepath, 'JPEG', quality=95)
            
            return filepath
            
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
            return None
    
    def download_images_batch(self, image_urls, product_id):
        """Download multiple images for a product"""
        saved_paths = []
        
        for idx, url in enumerate(image_urls):
            if idx >= Config.MAX_IMAGES_PER_PRODUCT:
                break
            
            filepath = self.download_image(url, f"{product_id}_{idx}")
            if filepath:
                saved_paths.append(filepath)
        
        return saved_paths
