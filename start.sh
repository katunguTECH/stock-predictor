#!/bin/bash
# Unset any malformed Streamlit env vars
unset STREAMLIT_SERVER_PORT
unset STREAMLIT_SERVER_ADDRESS
# Run with explicit fixed port
streamlit run railway_app.py --server.port=8080 --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
