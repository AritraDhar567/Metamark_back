import pymysql
from config import Config
from contextlib import contextmanager

class Database:
    @staticmethod
    def get_connection():
        """Get MySQL database connection"""
        return pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
    
    @staticmethod
    @contextmanager
    def get_cursor():
        """Context manager for database cursor"""
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()
    
    @staticmethod
    def execute_query(query, params=None):
        """Execute SELECT query and return results"""
        with Database.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    @staticmethod
    def execute_one(query, params=None):
        """Execute SELECT query and return one result"""
        with Database.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
    
    @staticmethod
    def execute_insert(query, params=None):
        """Execute INSERT query and return last insert id"""
        with Database.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.lastrowid
    
    @staticmethod
    def execute_update(query, params=None):
        """Execute UPDATE/DELETE query and return affected rows"""
        with Database.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount
    
    @staticmethod
    def execute_update(query, params=None):
        """Execute UPDATE query"""
        conn = Database.get_connection()
        cursor = conn.cursor()  # Remove dictionary=True
        try:
            cursor.execute(query, params)
            conn.commit()
            rows_affected = cursor.rowcount
            return rows_affected
        except Exception as e:
            conn.rollback()
            print(f"Update error: {e}")
            raise
        finally:
            cursor.close()



def init_db():
    """Initialize database tables - matches your existing schema"""
    
    # Check if database exists, create if not
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database creation check: {e}")
    
    with Database.get_cursor() as cursor:
        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id VARCHAR(255) UNIQUE NOT NULL,
                url TEXT NOT NULL,
                title VARCHAR(500),
                listed_price DECIMAL(10, 2),
                currency VARCHAR(10) DEFAULT 'INR',
                seller VARCHAR(255),
                category VARCHAR(100),
                marketplace VARCHAR(100),
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_product_id (product_id),
                INDEX idx_marketplace (marketplace)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id VARCHAR(255) NOT NULL,
                image_url TEXT,
                storage_path VARCHAR(500),
                image_type VARCHAR(50) DEFAULT 'product',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
                INDEX idx_product_id (product_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # OCR Results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ocr_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                image_id INT NOT NULL,
                crop_type VARCHAR(50),
                ocr_text TEXT,
                extracted JSON,
                confidence FLOAT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                INDEX idx_image_id (image_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Validations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id VARCHAR(255) NOT NULL,
                ocr_id INT,
                rule_id VARCHAR(50) NOT NULL,
                rule_desc VARCHAR(255),
                passed BOOLEAN NOT NULL,
                severity VARCHAR(20) DEFAULT 'medium',
                details TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
                FOREIGN KEY (ocr_id) REFERENCES ocr_results(id) ON DELETE CASCADE,
                INDEX idx_product_id (product_id),
                INDEX idx_passed (passed),
                INDEX idx_severity (severity)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        print("✓ Database tables created successfully")
