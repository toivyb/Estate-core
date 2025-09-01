# app/errors.py
from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e): return jsonify(error="bad_request"), 400

    @app.errorhandler(401)
    def unauthorized(e): return jsonify(error="unauthorized"), 401

    @app.errorhandler(403)
    def forbidden(e): return jsonify(error="forbidden"), 403

    @app.errorhandler(404)
    def not_found(e): return jsonify(error="not_found"), 404

    @app.errorhandler(422)
    def unprocessable(e): return jsonify(error="unprocessable"), 422

    @app.errorhandler(500)
    def server_error(e): return jsonify(error="server_error"), 500
