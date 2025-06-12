"""
Web application module for Bitarr.
"""
from .app import create_app, socketio

__all__ = ['create_app', 'socketio']
