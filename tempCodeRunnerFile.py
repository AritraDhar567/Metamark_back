from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models.database import init_db
from routes.products import products_bp
from routes.validation import validation_bp
from routes.dashboard import dashboard_bp
from routes.entities import entities_bp
from routes.pre_validation import pre_validation_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    CORS(app)
    JWTManager(app)
    
    # Initialize database
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
    
    # Register blueprints
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(validation_bp, url_prefix='/api/validations')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(entities_bp, url_prefix='/api/entities')
    app.register_blueprint(pre_validation_bp, url_prefix='/api/pre-validation')
    
    @app.route('/')
    def index():
        return jsonify({'message': 'Legal Metrology Backend API', 'version': '1.0'})
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
