import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
from config import Config

class ProductScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': Config.CRAWLER_USER_AGENT
        })
    
    def scrape_amazon_product(self, url):
        """Enhanced Amazon scraper using Selenium with debug"""
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        time.sleep(Config.CRAWLER_DELAY)
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={Config.CRAWLER_USER_AGENT}')
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.ID, 'productTitle')))
            
            # Try multiple ways to click read more
            try:
                # Method 1: Find and click all expander buttons
                read_more_elements = driver.find_elements(By.CSS_SELECTOR, 
                    '.a-expander-prompt, #bookDescription_feature_div .a-expander-prompt, #productDescription .a-expander-prompt')
                for elem in read_more_elements:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView();", elem)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", elem)
                        time.sleep(1)
                        print(f"Clicked read more button")
                    except Exception as e:
                        print(f"Could not click button: {e}")
            except Exception as e:
                print(f"No read more buttons found: {e}")
            
            # Scroll multiple times
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # SAVE HTML FOR DEBUGGING
            with open('amazon_debug.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("Saved amazon_debug.html for inspection")
            
            product_data = {
                'url': url,
                'product_id': self._extract_amazon_product_id(url),
                'title': self._get_text(soup, '#productTitle'),
                'description': self._extract_amazon_description_full(soup),
                'listed_price': self._extract_price(soup),
                'currency': 'INR',
                'seller': self._get_text(soup, '#sellerProfileTriggerId') or 'Amazon',
                'category': self._extract_amazon_category(soup),
                'marketplace': 'Amazon',
                'image_urls': self._extract_amazon_images(soup),
                'publisher': self._extract_amazon_detail(soup, 'Publisher'),
                'language': self._extract_amazon_detail(soup, 'Language'),
                'isbn_10': self._extract_amazon_detail(soup, 'ISBN-10'),
                'isbn_13': self._extract_amazon_detail(soup, 'ISBN-13'),
                'dimensions': self._extract_amazon_detail(soup, 'Dimensions'),
                'weight': self._extract_amazon_detail(soup, 'Item Weight'),
                'page_count': self._extract_page_count(soup),
                'country_of_origin': self._extract_amazon_detail(soup, 'Country of Origin'),
                'manufacturer': self._extract_amazon_detail(soup, 'Manufacturer'),
                'packer': self._extract_amazon_detail(soup, 'Packer'),
                'importer': self._extract_amazon_importer(soup),
                'importer_email': self._extract_importer_email(soup),
                'importer_phone': self._extract_importer_phone(soup),
                'generic_name': self._extract_amazon_detail(soup, 'Generic Name'),
                'rating': self._extract_amazon_rating(soup),
                'review_count': self._extract_amazon_review_count(soup)
            }
            
            # Debug print
            print(f"Extracted data:")
            print(f"  Publisher: {product_data['publisher']}")
            print(f"  Language: {product_data['language']}")
            print(f"  ISBN-10: {product_data['isbn_10']}")
            print(f"  ISBN-13: {product_data['isbn_13']}")
            print(f"  Country: {product_data['country_of_origin']}")
            print(f"  Importer: {product_data['importer']}")
            
            driver.quit()
            return product_data
            
        except Exception as e:
            print(f"Error scraping Amazon: {e}")
            import traceback
            traceback.print_exc()
            if 'driver' in locals():
                driver.quit()
            return None

    
    def scrape_flipkart_product(self, url):
        """Fixed Flipkart scraper with correct selectors"""
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        time.sleep(Config.CRAWLER_DELAY)
        
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={Config.CRAWLER_USER_AGENT}')
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.VU-ZEz, .B_NuCI, h1')))
            
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title - use correct selector
            title = None
            title_elem = soup.select_one('span.VU-ZEz')
            if title_elem:
                title = title_elem.get_text(strip=True)
            if not title:
                title_elem = soup.select_one('h1 span')
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            # Extract price - correct class
            price = None
            price_elem = soup.select_one('.Nx9bqj')
            if price_elem:
                price_text = price_elem.get_text(strip=True).replace('₹', '').replace(',', '')
                try:
                    price = float(price_text)
                except:
                    pass
            
            # Extract rating
            rating = None
            rating_elem = soup.select_one('.XQDdHH')
            if rating_elem:
                try:
                    rating = float(rating_elem.get_text(strip=True))
                except:
                    pass
            
            # Extract reviews
            reviews = None
            review_elem = soup.select_one('.Wphh3N')
            if review_elem:
                review_text = review_elem.get_text().replace(',', '')
                match = re.search(r'(\d+)', review_text)
                if match:
                    reviews = int(match.group(1))
            
            # Extract specs from Product Details section
            specs = {}
            spec_rows = soup.find_all('div', class_=lambda x: x and '1IKDg' in str(x))
            for row in spec_rows:
                cols = row.find_all('div', class_='col')
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True).lower()
                    value = cols[1].get_text(strip=True)
                    if key and value:
                        specs[key] = value
            
            print(f"Extracted specs: {specs}")
            
            # Get seller
            seller = 'Flipkart'
            seller_elem = soup.find('span', string=lambda x: x and 'Enterprise' in str(x))
            if not seller_elem:
                seller_elem = soup.find('div', class_=lambda x: x and 'yeLeBc' in str(x))
            if seller_elem:
                seller = seller_elem.get_text(strip=True)
            
            # Get images - fix selector
            images = []
            img_elems = soup.find_all('img', class_=lambda x: x and '53J4C-' in str(x))
            if not img_elems:
                img_elems = soup.find_all('img', class_=lambda x: x and ('0DkuPH' in str(x) or 'utBuJY' in str(x)))

            for img in img_elems[:Config.MAX_IMAGES_PER_PRODUCT]:
                src = img.get('src')
                if src and 'http' in src:
                    images.append(src.replace('/128/', '/832/').replace('/180/', '/832/'))
            
            product_data = {
                'url': url,
                'product_id': self._extract_flipkart_product_id(url),
                'title': title or 'Unknown',
                'description': None,  # Flipkart doesn't show description in HTML
                'listed_price': price,
                'currency': 'INR',
                'seller': seller,
                'category': specs.get('ideal for', 'Fashion'),
                'marketplace': 'Flipkart',
                'image_urls': images,
                'country_of_origin': None,  # Not in specs for fashion
                'manufacturer': specs.get('brand'),
                'packer': None,
                'importer': None,
                'generic_name': specs.get('style code'),
                'dimensions': specs.get('other dimensions'),
                'weight': None,
                'rating': rating,
                'review_count': reviews
            }
            
            print(f"Final product: {product_data['title']}, price={product_data['listed_price']}")
            
            driver.quit()
            return product_data
            
        except Exception as e:
            print(f"Error scraping Flipkart: {e}")
            import traceback
            traceback.print_exc()
            if 'driver' in locals():
                driver.quit()
            return None


    
    def scrape_generic_product(self, url):
        """Generic scraper"""
        time.sleep(Config.CRAWLER_DELAY)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product_data = {
                'url': url,
                'product_id': self._generate_product_id(url),
                'title': self._extract_generic_title(soup),
                'description': self._extract_generic_description(soup),
                'listed_price': self._extract_generic_price(soup),
                'currency': 'INR',
                'seller': self._extract_domain(url),
                'category': 'General',
                'marketplace': self._extract_domain(url),
                'image_urls': self._extract_generic_images(soup, url)
            }
            
            return product_data
            
        except Exception as e:
            print(f"Error scraping generic product: {e}")
            return None
    
    # Amazon extraction methods
    def _extract_amazon_description_full(self, soup):
        """Extract full description"""
        desc_parts = []
        
        # Product description
        desc_divs = soup.select('#bookDescription_feature_div, #productDescription, #feature-bullets')
        for div in desc_divs:
            for unwanted in div.select('.a-expander-prompt, script, style, .a-popover-trigger'):
                unwanted.decompose()
            text = div.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            if len(text) > 50:
                desc_parts.append(text)
        
        return ' '.join(desc_parts)[:3000] if desc_parts else None
    
    def _extract_amazon_detail(self, soup, label):
        """Extract detail by label - FIXED with cleaning"""
        
        # Method 1: Rich Product Information Carousel
        carousel_items = soup.select('.rpi-attribute-value span')
        carousel_labels = soup.select('.rpi-attribute-label span')
        
        for i, label_elem in enumerate(carousel_labels):
            if label.lower() in label_elem.get_text().lower():
                if i < len(carousel_items):
                    value = carousel_items[i].get_text(strip=True)
                    # CLEAN UNICODE CONTROL CHARACTERS
                    value = re.sub(r'[\u200e\u200f\u202a-\u202e]+', '', value)
                    value = value.strip().lstrip(':').strip()
                    return value[:500] if value else None
        
        # Method 2: Detail bullets
        bullets = soup.select('#detailBulletsWrapper_feature_div li')
        for li in bullets:
            text = li.get_text()
            if label.lower() in text.lower():
                parts = re.split(r'[:\u200f]+', text, 1)
                if len(parts) > 1:
                    value = parts[1].strip()
                    value = re.sub(r'[\u200e\u200f\u202a-\u202e\s]+', ' ', value)
                    value = value.strip()
                    if label.lower() == 'publisher':
                        value = re.sub(r'\([^)]*\d{4}[^)]*\)', '', value).strip()
                    return value[:500] if value else None
        
        # Method 3: Tables
        tables = soup.select('#productDetails_detailBullets_sections1, #prodDetails')
        for table in tables:
            rows = table.select('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2 and label.lower() in cells[0].get_text().lower():
                    value = cells[1].get_text(strip=True)
                    value = re.sub(r'[\u200e\u200f\u202a-\u202e]+', '', value)
                    return value.strip()[:500] if value else None
        
        return None


    
    def _extract_page_count(self, soup):
        """Extract page count"""
        for term in ['Hardcover', 'Paperback', 'pages']:
            detail = self._extract_amazon_detail(soup, term)
            if detail:
                match = re.search(r'(\d+)\s*pages?', detail, re.IGNORECASE)
                if match:
                    return int(match.group(1))
        return None
    
    def _extract_amazon_importer(self, soup):
        """Extract importer - CLEANED"""
        importer = self._extract_amazon_detail(soup, 'Importer')
        if importer:
            # Remove email and phone
            importer = re.sub(r'Email[:\s–\-]+[^\s,]+', '', importer, flags=re.IGNORECASE)
            importer = re.sub(r',\s*Ph[:\s–\-]+[\d\s\-]+', '', importer, flags=re.IGNORECASE)
            importer = re.sub(r'\s+', ' ', importer).strip()
            return importer[:500] if importer else None
        return None

    def _extract_importer_email(self, soup):
        """Extract email - CLEANED"""
        importer = self._extract_amazon_detail(soup, 'Importer')
        if importer:
            match = re.search(r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', importer)
            if match:
                return match.group(1)
        return None

    def _extract_importer_phone(self, soup):
        """Extract phone - CLEANED"""
        importer = self._extract_amazon_detail(soup, 'Importer')
        if importer:
            match = re.search(r'Ph[:\s–\-]+([\d\s\-]+)', importer, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    
    def _extract_amazon_rating(self, soup):
        """Extract rating"""
        rating = soup.select_one('[data-hook="rating-out-of-text"], .a-icon-alt')
        if rating:
            match = re.search(r'([\d.]+)', rating.get_text())
            if match:
                return float(match.group(1))
        return None
    
    def _extract_amazon_review_count(self, soup):
        """Extract review count"""
        reviews = soup.select_one('[data-hook="total-review-count"], #acrCustomerReviewText')
        if reviews:
            match = re.search(r'([\d,]+)', reviews.get_text().replace(',', ''))
            if match:
                return int(match.group(1))
        return None
    
    def _extract_amazon_category(self, soup):
        """Extract category"""
        breadcrumbs = soup.select('#wayfinding-breadcrumbs_feature_div a, .a-breadcrumb a')
        if breadcrumbs:
            return breadcrumbs[-1].get_text(strip=True)
        return 'Books'
    
    # Flipkart extraction methods
    def _get_flipkart_description(self, soup):
        """Extract description"""
        desc = soup.find('div', class_=lambda x: x and any(c in str(x) for c in ['yNeNk', 'w9jEaj']))
        return desc.get_text(strip=True)[:2000] if desc else None
    
    def _get_flipkart_seller(self, soup):
        """Extract seller"""
        seller = soup.select_one('#sellerName')
        if not seller:
            seller = soup.find('div', class_=lambda x: x and 'yeLeBc' in str(x))
        return seller.get_text(strip=True) if seller else 'Flipkart'
    
    def _extract_flipkart_rating(self, soup):
        """Extract rating"""
        rating = soup.find('div', class_=lambda x: x and 'XQDdHH' in str(x))
        if rating:
            match = re.search(r'([\d.]+)', rating.get_text())
            if match:
                return float(match.group(1))
        return None
    
    def _extract_flipkart_review_count(self, soup):
        """Extract reviews"""
        reviews = soup.find('span', class_=lambda x: x and 'Wphh3N' in str(x))
        if reviews:
            match = re.search(r'([\d,]+)', reviews.get_text().replace(',', ''))
            if match:
                return int(match.group(1))
        return None
    
    def _classify_from_title(self, title):
        """Classify category"""
        if not title:
            return 'General'
        title_lower = title.lower()
        if any(w in title_lower for w in ['bluetooth', 'earphone', 'headphone', 'earbuds', 'tws']):
            return 'Audio'
        elif any(w in title_lower for w in ['laptop', 'computer']):
            return 'Electronics'
        elif 'mobile' in title_lower or 'phone' in title_lower:
            return 'Mobile'
        return 'General'
    
    # Common helpers
    def _get_text(self, soup, selector):
        """Extract text"""
        elem = soup.select_one(selector)
        return elem.get_text(strip=True) if elem else None
    
    def _extract_price(self, soup):
        """Extract Amazon price"""
        selectors = ['.a-price-whole', '.a-price .a-offscreen', '#priceblock_ourprice', '.priceToPay .a-price-whole']
        for sel in selectors:
            elem = soup.select_one(sel)
            if elem:
                match = re.search(r'[\d,]+\.?\d*', elem.get_text().replace(',', ''))
                if match:
                    try:
                        price = float(match.group())
                        if price > 0:
                            return price
                    except:
                        continue
        return None
    
    def _extract_flipkart_price(self, soup):
        """Extract Flipkart price"""
        for sel in ['._30jeq3', '._1_WHN1', '.Nx9bqj']:
            elem = soup.select_one(sel)
            if elem:
                match = re.search(r'[\d]+', elem.get_text().replace(',', ''))
                if match:
                    return float(match.group())
        return None
    
    def _extract_generic_price(self, soup):
        """Extract generic price"""
        patterns = [r'₹\s*([\d,]+\.?\d*)', r'INR\s*([\d,]+\.?\d*)', r'Rs\.?\s*([\d,]+\.?\d*)']
        text = soup.get_text()
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1).replace(',', ''))
        return None
    
    def _extract_amazon_images(self, soup):
        """Extract Amazon images"""
        images = []
        main = soup.select_one('#landingImage')
        if main and main.get('data-old-hires'):
            images.append(main['data-old-hires'])
        
        thumbs = soup.select('.imageThumbnail img')
        for thumb in thumbs[:Config.MAX_IMAGES_PER_PRODUCT]:
            src = thumb.get('src', '').replace('_AC_US40_', '_AC_SL1500_')
            if src and src not in images:
                images.append(src)
        
        return images[:Config.MAX_IMAGES_PER_PRODUCT]
    
    def _extract_flipkart_images(self, soup):
        """Extract Flipkart images"""
        images = []
        for sel in ['._396cs4 img', '._2r_T1I img', 'img[loading="eager"]']:
            imgs = soup.select(sel)
            for img in imgs[:Config.MAX_IMAGES_PER_PRODUCT]:
                src = img.get('src') or img.get('data-src')
                if src and 'http' in src:
                    src = src.replace('/128/128/', '/832/832/')
                    if src not in images:
                        images.append(src)
            if images:
                break
        return images[:Config.MAX_IMAGES_PER_PRODUCT]
    
    def _extract_generic_images(self, soup, base_url):
        """Extract generic images"""
        images = []
        imgs = soup.select('img[src*="product"], .product-image img')
        for img in imgs[:Config.MAX_IMAGES_PER_PRODUCT]:
            src = img.get('src') or img.get('data-src')
            if src:
                images.append(urljoin(base_url, src))
        return images
    
    def _extract_generic_description(self, soup):
        """Extract generic description"""
        for sel in ['[itemprop="description"]', '.product-description', '#description']:
            desc = soup.select_one(sel)
            if desc:
                return desc.get_text(strip=True)[:2000]
        return None
    
    def _extract_amazon_product_id(self, url):
        """Extract ASIN"""
        match = re.search(r'/dp/([A-Z0-9]{10})', url)
        return match.group(1) if match else self._generate_product_id(url)
    
    def _extract_flipkart_product_id(self, url):
        """Extract Flipkart ID"""
        match = re.search(r'pid=([A-Z0-9]+)', url)
        if match:
            return match.group(1)
        match = re.search(r'/p/itm([a-z0-9]+)', url)
        return match.group(1) if match else self._generate_product_id(url)
    
    def _generate_product_id(self, url):
        """Generate ID from URL"""
        return str(abs(hash(url)))[:12]
    
    def _extract_domain(self, url):
        """Extract domain"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain.split('.')[0].capitalize()
    
    def _extract_generic_title(self, soup):
        """Extract generic title"""
        for sel in ['h1', '.product-title', '[itemprop="name"]', 'title']:
            elem = soup.select_one(sel)
            if elem:
                return elem.get_text(strip=True)[:500]
        return "Unknown Product"
