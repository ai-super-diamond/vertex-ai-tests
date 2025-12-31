import streamlit as st
from vertex_benchmark.dashboard import main

# Set page config
st.set_page_config(page_title="Test Flag Functionality", layout="wide")

# Run the dashboard main function
main()