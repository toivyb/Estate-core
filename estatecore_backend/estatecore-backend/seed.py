from estatecore_backend import create_app, db
from estatecore_backend.models import User, Organization, Property, Tenant, Invoice, Payment, MaintenanceRequest, Document

app = create_app()
app.app_context().push()

# Reset DB
db.drop_all()

# Create org
org = Organization(name='TestOrg')
db.session.add(org)
db.session.commit()

# Create users
admin = User(email='admin@example.com', role='super_admin', organization_id=org.id)
admin.set_password('adminpass')
manager = User(email='manager@example.com', role='property_manager', organization_id=org.id)
manager.set_password('managerpass')
tenant_user = User(email='tenant@example.com', role='tenant', organization_id=org.id)
tenant_user.set_password('tenantpass')

db.session.add_all([admin, manager, tenant_user])
db.session.commit()

# Create property
property = Property(name='123 Main St', address='123 Main St, City', organization_id=org.id)
db.session.add(property)
db.session.commit()

# Create tenant
tenant = Tenant(full_name='John Doe', email='johndoe@example.com', property_id=property.id)
db.session.add(tenant)
db.session.commit()

# Create invoice
invoice = Invoice(tenant_id=tenant.id, amount_due=1200.00, due_date='2025-08-01', is_paid=False)
db.session.add(invoice)

# Create payment
payment = Payment(tenant_id=tenant.id, amount_paid=600.00, payment_date='2025-07-10', method='card')
db.session.add(payment)

# Create document
doc = Document(tenant_id=tenant.id, name='Lease Agreement', url='http://example.com/lease.pdf', expires_at='2026-01-01')
db.session.add(doc)

# Create maintenance request
req = MaintenanceRequest(
    tenant_id=tenant.id,
    property_id=property.id,
    title='Leaky Faucet',
    description='Kitchen faucet leaking under sink',
    status='open'
)
db.session.add(req)

db.session.commit()
print('✅ Database seeded successfully.')
