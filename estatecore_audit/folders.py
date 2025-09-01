from pathlib import Path
from datetime import datetime
from .config import ESTATECORE_DATA_DIR, CLIENT_SUBFOLDERS, AUDIT_LOG_NAME

def _safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def _append_audit_log(client_root: Path, line: str) -> None:
    audit_dir = client_root / CLIENT_SUBFOLDERS["audit"]
    _safe_mkdir(audit_dir)
    log_file = audit_dir / AUDIT_LOG_NAME
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line.rstrip() + "\n")

def ensure_client_folder(client_id: int) -> str:
    client_root = Path(ESTATECORE_DATA_DIR) / str(client_id)
    _safe_mkdir(client_root)
    for sub in CLIENT_SUBFOLDERS.values():
        _safe_mkdir(client_root / sub)
    _append_audit_log(client_root, f"{datetime.utcnow().isoformat()}Z | client:{client_id} | created client folder structure")
    return str(client_root)

def ensure_building_folder(client_id: int, building_id: int) -> str:
    client_root = Path(ESTATECORE_DATA_DIR) / str(client_id)
    _safe_mkdir(client_root)
    buildings_root = client_root / CLIENT_SUBFOLDERS["buildings"]
    _safe_mkdir(buildings_root)
    bdir = buildings_root / str(building_id)
    _safe_mkdir(bdir)
    _append_audit_log(client_root, f"{datetime.utcnow().isoformat()}Z | client:{client_id} building:{building_id} | ensured building folder")
    return str(bdir)

def ensure_tenant_folder(client_id: int, tenant_id: int) -> str:
    client_root = Path(ESTATECORE_DATA_DIR) / str(client_id)
    _safe_mkdir(client_root)
    tenants_root = client_root / CLIENT_SUBFOLDERS["tenants"]
    _safe_mkdir(tenants_root)
    tdir = tenants_root / str(tenant_id)
    _safe_mkdir(tdir)
    _append_audit_log(client_root, f"{datetime.utcnow().isoformat()}Z | client:{client_id} tenant:{tenant_id} | ensured tenant folder")
    return str(tdir)
