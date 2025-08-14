from flask import Blueprint, request, jsonify
import csv, io

bp = Blueprint("bulk", __name__)

@bp.post("/rent/bulk_upload")
def bulk_upload():
    ctype = request.headers.get("Content-Type","")
    rows = []
    if "text/csv" in ctype:
        content = request.get_data(as_text=True)
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
    else:
        rows = request.get_json(force=True)
        if isinstance(rows, dict) and "rows" in rows:
            rows = rows["rows"]
    required = {"tenant_id","month","amount_due","amount_paid"}
    valid = []
    errors = []
    for i,r in enumerate(rows, start=1):
        missing = required - set(r.keys())
        if missing:
            errors.append({"row": i, "error": f"Missing: {', '.join(sorted(missing))}"})
            continue
        valid.append(r)
    return jsonify({"parsed": len(rows), "valid": len(valid), "errors": errors})
