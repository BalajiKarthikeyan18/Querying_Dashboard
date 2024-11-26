import streamlit as st
from datetime import date

def main():

    if "temporal_graph" not in st.session_state:
        st.error("No Temporal Graph found in the session state. Please run the main script first.")
        return
    
    timestamp = st.select_slider("Select Timestamp", options=range(len(st.session_state.temporal_graph.files)))
    
    graph = st.session_state.temporal_graph.load_graph_at_timestamp(timestamp)
    
    # Dropdown to select query
    query_type = st.selectbox("Choose Query", ["Valid Products in a given date range", "N most frequent subtype in parts", "Bottleneck Analysis Based on Part Attributes","Suppliers to a Part", "Parts transported to the facility over long distances with high transportation costs."])

    if query_type == "Valid Products in a given date range":
        
        default_date1 = date(2026, 12, 10)

        # Date input widget
        selected_date = st.date_input("Pick a start date", value=default_date1)

        default_date2 = date(2026, 1, 17)

        # Date input widget
        selected_date = st.date_input("Pick a end date", value=default_date2)
        # Generate the ego graph using the selected node and radius
        ego_graph = ego_graph_query(graph, node_id, radius)
        if ego_graph:
            st.write(f"Ego Graph for Node: {node_id}")
            st.write(f"Nodes: {ego_graph.number_of_nodes()}, Edges: {ego_graph.number_of_edges()}")

            # Visualize and render the ego graph with Plotly
            fig = plotly_ego_graph(ego_graph)
            st.plotly_chart(fig)  # Display the figure in Streamlit
if __name__ == "__main__":
    main()