#!/bin/bash
# Remove the malformed variables injected by Railway
unset STREAMLIT_SERVER_PORT
unset STREAMLIT_SERVER_ADDRESS
unset STREAMLIT_SERVER_ENABLECORS
unset STREAMLIT_SERVER_ENABLEXSRFPROTECTION

# Run Streamlit with a fixed, explicit port
exec streamlit run railway_app.py --server.port=8080 --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
