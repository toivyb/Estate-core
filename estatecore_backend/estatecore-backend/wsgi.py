from flask import Flask
from estatecore_backend.models import db
from routes.rent import rent_bp
from estatecore_backend.routes.maintenance import maintenance_bp
from estatecore_backend.routes.access import access_bp
from estatecore_backend.routes.payment import payment_bp
from routes.reporting import reporting_bp
from estatecore_backend.routes.accounting import accounting_bp
from estatecore_backend.routes.auth import auth_bp

app.register_blueprint(auth_bp)
app.register_blueprint(accounting_bp)
app.register_blueprint(reporting_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(access_bp)
app.register_blueprint(maintenance_bp)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@127.0.0.1:5433/estatecore_devestatecore.db'
db.init_app(app)

app.register_blueprint(rent_bp)

if __name__ == '__main__':
    app.run(debug=True)
