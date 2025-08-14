from .. import db  # type: ignore

# Association table so a manager can handle multiple properties (and vice-versa)
property_manager_properties = db.Table(
    "property_manager_properties",
    db.Column("manager_id", db.Integer, db.ForeignKey("property_manager.id"), primary_key=True),
    db.Column("property_id", db.Integer, db.ForeignKey("property.id"), primary_key=True),
)

class PropertyManager(db.Model):
    __tablename__ = "property_manager"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    full_name = db.Column(db.String(120), nullable=False)

    user = db.relationship("User", back_populates="manager")
    properties = db.relationship("Property",
                                 secondary=property_manager_properties,
                                 back_populates="managers")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "property_ids": [p.id for p in self.properties],
        }
