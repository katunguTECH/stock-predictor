import os
import sys

# Remove all Streamlit environment variables
for k in list(os.environ.keys()):
    if k.startswith('STREAMLIT'):
        del os.environ[k]

# Now import and run streamlit via its internal command
from streamlit.web import cli as st_cli
sys.argv = ['streamlit', 'run', 'railway_app.py', '--server.port=8080', '--server.address=0.0.0.0']
st_cli.main()
