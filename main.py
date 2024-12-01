import streamlit as st
import glob
import re
from TemporalGraphClass import TemporalGraphClass 

# Utility function for natural sorting of files
def natural_sort(files):
    return sorted(files, key=lambda x: int(re.search(r'timestamp_(\d+)', x).group(1)))

# Streamlit app starts here
def main():
    st.title("Temporal Graph Dashboard")

    # Specify the directory containing JSON files
    data_directory = "data/supply_chain_export_1000/"
    files = glob.glob(f"{data_directory}timestamp_*.json")

    if not files:
        st.error("No JSON files found in the specified directory.")
        return

    # Sort files naturally
    sorted_files = natural_sort(files)

    # Initialize TemporalGraph
    temporal_graph = TemporalGraphClass(sorted_files)   
    if temporal_graph not in st.session_state:
        st.session_state.temporal_graph = temporal_graph 

    # Success message
    st.success("Files processed successfully!")

if __name__ == "__main__":
    main()
