import traceback
try:
    from app import create_app
    a = create_app()
    print("create_app() ->", type(a))
    from flask import Flask
    print("isinstance(app, Flask):", isinstance(a, Flask))
except Exception:
    traceback.print_exc()
