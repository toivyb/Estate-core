import sys, os, re, io

REL_PROPERTY = """    tenants = db.relationship(
        'Tenant',
        back_populates='property',
        cascade="all, delete-orphan"
    )
"""

REL_TENANT_FK = "    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))\n"
REL_TENANT_REL = """    property = db.relationship(
        'Property',
        back_populates='tenants'
    )
"""

def patch_property(path):
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    if "tenants = db.relationship(" in src:
        return False, "Property already has tenants relationship"
    # Find class Property line
    m = re.search(r'^(class\s+Property\s*\(.*?\)\s*:\s*\n)', src, flags=re.M)
    if not m:
        raise RuntimeError("Couldn't find class Property in " + path)
    insert_at = m.end()
    new_src = src[:insert_at] + REL_PROPERTY + src[insert_at:]
    with open(path + ".bak", 'w', encoding='utf-8') as f:
        f.write(src)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_src)
    return True, "Inserted tenants relationship"

def patch_tenant(path):
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    changed = False
    messages = []
    # Ensure FK line exists inside class Tenant
    m = re.search(r'^(class\s+Tenant\s*\(.*?\)\s*:\s*\n)', src, flags=re.M)
    if not m:
        raise RuntimeError("Couldn't find class Tenant in " + path)
    class_start = m.end()
    # We'll insert after class header
    if "property_id = db.Column(" not in src:
        src = src[:class_start] + REL_TENANT_FK + src[class_start:]
        changed = True
        messages.append("Inserted Tenant.property_id FK")
        class_start += len(REL_TENANT_FK)
    # Ensure relationship
    if "property = db.relationship(" not in src:
        src = src[:class_start] + REL_TENANT_REL + src[class_start:]
        changed = True
        messages.append("Inserted Tenant.property relationship")
    if changed:
        with open(path + ".bak", 'w', encoding='utf-8') as f:
            f.write(open(path, 'r', encoding='utf-8').read())
        with open(path, 'w', encoding='utf-8') as f:
            f.write(src)
        return True, "; ".join(messages)
    else:
        return False, "Tenant already has FK and relationship"
    

def main():
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    prop_path = os.path.join(project_root, 'app', 'models', 'property.py')
    tenant_path = os.path.join(project_root, 'app', 'models', 'tenant.py')
    for p in [prop_path, tenant_path]:
        if not os.path.exists(p):
            raise SystemExit(f"File not found: {p}. Make sure you run this on your backend root.")
    p_changed, p_msg = patch_property(prop_path)
    t_changed, t_msg = patch_tenant(tenant_path)
    print("Property:", p_msg)
    print("Tenant:", t_msg)
    print("Done. Backups saved as *.bak next to each file. Restart your Flask shell and try creating the user.")

if __name__ == "__main__":
    main()
