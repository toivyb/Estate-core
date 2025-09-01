
def register_routes(app):
    from .auth import bp as auth_bp
    from .invites import bp as invites_bp
    from .rent import bp as rent_bp
    from .maintenance import bp as maint_bp
    from .access import bp as access_bp
    from .dashboard import bp as dash_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(invites_bp, url_prefix='/api')
    app.register_blueprint(rent_bp, url_prefix='/api')
    app.register_blueprint(maint_bp, url_prefix='/api')
    app.register_blueprint(access_bp, url_prefix='/api')
    app.register_blueprint(dash_bp, url_prefix='/api')
