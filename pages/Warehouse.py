import streamlit as st
import json

def query_transportation_cost_for_supplier_and_warehouse(G, supplier_id, warehouse_id):

    if G.has_edge(supplier_id, warehouse_id):
        edge_data = G[supplier_id][warehouse_id]
        st.write(edge_data)
        if edge_data.get("relationship_type") == "SupplierToWarehouse":
            return edge_data.get("transportation_cost")
    return None

def main():

    if "temporal_graph" not in st.session_state:
        st.error("No Temporal Graph found in the session state. Please run the main script first.")
        return
    
    timestamp = st.sidebar.select_slider("Select Timestamp", options=range(len(st.session_state.temporal_graph.files)))
    

    st.title("Querying Transportation Cost for Supplier and Warehouse")
    
    # Load the JSON data at the given timestamp
    # with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
    #     temporal_graph = json.load(f)

    # all_suppliers = []
    # for supplier_data in temporal_graph["node_values"]["Supplier"] :
    #     all_suppliers.append(supplier_data[-1])

    # all_warehouses = []
    # for warehouse_data in temporal_graph["node_values"]["Warehouse"] :
    #     all_warehouses.append(warehouse_data[-1])

    graph = st.session_state.temporal_graph.load_graph_at_timestamp(timestamp)
    all_suppliers = []
    all_warehouses = []
    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("node_type") == "Supplier":
            all_suppliers.append(node_id)
        elif node_data.get("node_type") == "Warehouse":
            all_warehouses.append(node_id)

    supplier_id = st.sidebar.selectbox("Select Supplier ID:", options=all_suppliers)
    warehouse_id = st.sidebar.selectbox("Select Warehouse ID:", options=all_warehouses)

    transportation_cost = query_transportation_cost_for_supplier_and_warehouse(graph, supplier_id, warehouse_id)
    if transportation_cost is None:
        st.write("No transportation cost found for the given Supplier and Warehouse.")
    else :
        st.write("Transportation cost:",transportation_cost)    
    
if __name__ == "__main__":
    main()