import streamlit as st

def main():

    if "temporal_graph" not in st.session_state:
        st.error("No Temporal Graph found in the session state. Please run the main script first.")
        return
    
    timestamp = st.select_slider("Select Timestamp", options=range(len(st.session_state.temporal_graph.files)))
    
    graph = st.session_state.temporal_graph.load_graph_at_timestamp(timestamp)
    
if __name__ == "__main__":
    main()