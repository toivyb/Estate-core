"""placeholder for missing base revision"""
from alembic import op
import sqlalchemy as sa  # noqa

# Alembic identifiers
revision = "7657ba3395c1"
down_revision = None          # leave as None unless you KNOW the real parent
branch_labels = None
depends_on = None

def upgrade():
    # No-op: this revision never actually ran on your DB
    pass

def downgrade():
    pass
