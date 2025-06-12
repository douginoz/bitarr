"""
Flask application for Bitarr.
"""
import os
from flask import Flask
from flask_socketio import SocketIO

# Create Socket.IO instance
socketio = SocketIO()

def create_app(test_config=None):
    """
    Create and configure the Flask application.

    Args:
        test_config: Test configuration

    Returns:
        Flask: Configured Flask application
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE_PATH=os.path.join(app.instance_path, 'bitarr.db'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    socketio.init_app(app, cors_allowed_origins="*")

    # Register custom template filters
    from .filters import register_filters
    register_filters(app)

    # Register blueprints
    from .routes import bp as routes_bp
    from .api import bp as api_bp
    from .api import db_api

    app.register_blueprint(routes_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(db_api)

    return app
