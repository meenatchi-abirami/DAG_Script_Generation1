from flask import Flask
from config import Config
from routes.validate_routes import validate_bp
from routes.dag_routes import dag_bp
from routes.chat_routes import chat_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(validate_bp, url_prefix='/api')
    app.register_blueprint(dag_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')

    return app

if __name__ == '__main__':
    app = create_app()
    # Bind to 0.0.0.0 so the server is reachable from other hosts if needed
    app.run(debug=True, host='0.0.0.0', port=5001)