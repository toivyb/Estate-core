from estatecore_backend import create_app, db
app = create_app()

@app.shell_context_processor
def make_shell_context():
    from estatecore_backend.models import User, Property, Tenant, RentRecord, FeatureFlag, InviteToken
    return dict(db=db, User=User, Property=Property, Tenant=Tenant, RentRecord=RentRecord,
                FeatureFlag=FeatureFlag, InviteToken=InviteToken)
