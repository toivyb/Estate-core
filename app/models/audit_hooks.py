from sqlalchemy import event

def register_audit_hooks():
    # Import inside to avoid circulars and duplicate mapper registration
    from estatecore_backend.models import Tenant

    @event.listens_for(Tenant, "after_insert")
    def _tenant_after_insert(mapper, connection, target):
        # placeholder for your real logic
        pass

    @event.listens_for(Tenant, "after_update")
    def _tenant_after_update(mapper, connection, target):
        # placeholder for your real logic
        pass