from estatecore_backend import db
from estatecore_backend.models import Organization

org = Organization(name="Test Organization")
db.session.add(org)
db.session.commit()
print("Created organization with ID:", org.id)
