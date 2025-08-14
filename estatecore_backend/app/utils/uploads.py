import os
from werkzeug.utils import secure_filename
def ensure_dir(p): os.makedirs(p, exist_ok=True)
def save_file(base, *parts, storage):
    fname = secure_filename(storage.filename or 'file')
    folder = os.path.join(base, *map(str, parts))
    ensure_dir(folder)
    full = os.path.join(folder, fname)
    storage.save(full)
    return full
