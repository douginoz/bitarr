"""
Main entry point for the web application.
"""
import os
import argparse
from bitarr.web import create_app, socketio
from bitarr.db.db_manager import DatabaseManager
from bitarr.db.init_db import init_db

def main():
    """
    Main entry point for the web application.
    """
    parser = argparse.ArgumentParser(description="Bitarr web application")
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8286, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--init-db', action='store_true', help='Initialize the database')
    args = parser.parse_args()

    # Initialize database if requested
    if args.init_db:
        db_path = init_db()
        print(f"Database initialized at: {db_path}")

    # Get configuration from database
    try:
        db = DatabaseManager()
        config = db.get_all_configuration()

        # Override with configuration from database if available
        if 'web_ui_port' in config:
            args.port = int(config['web_ui_port'])
    except Exception as e:
        print(f"Warning: Could not load configuration from database: {str(e)}")

    # Create the app
    app = create_app()

    # Run the app
    socketio.run(app, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
