import os
import sys
import subprocess

# Remove all Streamlit-related environment variables (they are malformed)
for key in list(os.environ.keys()):
    if key.startswith('STREAMLIT_'):
        del os.environ[key]

# Launch Streamlit with explicit arguments
cmd = [
    sys.executable, '-m', 'streamlit', 'run', 'railway_app.py',
    '--server.port=8080',
    '--server.address=0.0.0.0',
    '--server.enableCORS=false',
    '--server.enableXsrfProtection=false'
]
subprocess.run(cmd)
