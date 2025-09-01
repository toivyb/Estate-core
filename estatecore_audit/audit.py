from datetime import datetime
from typing import Optional, Dict, Any
from .models import db, AuditEvent
from .folders import _append_audit_log
from .config import ESTATECORE_DATA_DIR
from pathlib import Path

def log_event(client_id: int, entity_type: str, action: str, entity_id: Optional[str]=None, actor_id: Optional[int]=None, meta: Optional[Dict[str, Any]]=None) -> None:
    ev = AuditEvent(
        client_id=client_id,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        action=action,
        meta=meta or {},
    )
    db.session.add(ev)
    db.session.commit()

    # also append to per-client filesystem audit log
    client_root = Path(ESTATECORE_DATA_DIR) / str(client_id)
    line = f"{datetime.utcnow().isoformat()}Z | client:{client_id} entity:{entity_type}({entity_id}) action:{action} meta:{meta or {}}"
    _append_audit_log(client_root, line)
