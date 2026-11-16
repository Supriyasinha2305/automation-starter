import os

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    # POLICYHUB_PORT is set per learner when the SQValex backend spawns a
    # dedicated instance (see app/core/policyhub_manager.py in backend/).
    port = int(os.environ.get("POLICYHUB_PORT", "6001"))
    app.run(host="127.0.0.1", port=port, debug=True, use_reloader=False)
