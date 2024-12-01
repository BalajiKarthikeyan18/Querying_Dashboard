import streamlit as st

# supplier, parts
# warehouse, facility , po

def query_parts_for_product_offering(graph, product_offering_id):
    """
    Retrieve all parts needed to manufacture a given product offering based on the schema.
    """
    parts = set()
    
    # Traverse Facility -> ProductOffering relationships
    for facility, facility_data in graph.nodes(data=True):
        if facility_data.get("node_type") == "Facility":
            if graph.has_edge(facility, product_offering_id):
                edge_data = graph[facility][product_offering_id]
                if edge_data.get("relationship_type") == "FacilityToProductOfferings":
                    
                    # Traverse Parts -> Facility relationships
                    for part, part_data in graph.nodes(data=True):
                        if part_data.get("node_type") == "Parts" and graph.has_edge(part, facility):
                            part_edge_data = graph[part][facility]
                            if part_edge_data.get("relationship_type") == "PartsToFacility":
                                parts.add(part)
    
    return list(parts)



def query_profitable_products(graph, cost_threshold, demand_threshold):
    """
    Retrieve profitable products based on cost and demand thresholds.
    """
    profitable_products = []
    for node, attrs in graph.nodes(data=True):
        if attrs.get("node_type") == "ProductOffering":
            making_cost = attrs.get("cost", float("inf"))
            demand = attrs.get("demand", 0)

            if making_cost <= cost_threshold and demand >= demand_threshold:
                profitable_products.append((node, making_cost, demand))

    return profitable_products

def main() :
    
    if "temporal_graph" not in st.session_state:
        st.error("No Temporal Graph found in the session state. Please run the main script first.")
        return
    
    st.markdown("""
            ## Select Query to Execute :
        """)
    
    timestamp = st.select_slider("Select Timestamp", options=range(len(st.session_state.temporal_graph.files)))
    
    graph = st.session_state.temporal_graph.load_graph_at_timestamp(timestamp)

        # Dropdown to select query
    query_type = st.selectbox("Choose Query", ["Parts needed to manufacture a product", "Profitable Product Offerings"])

    if query_type == "Parts needed to manufacture a product":
        product_offering_id = st.text_input("Enter Product Offering ID", "PO_001")
        if st.button("Find Parts"):
            parts = query_parts_for_product_offering(graph, product_offering_id)
            if parts:
                st.write(f"Parts needed to manufacture {product_offering_id}:")
                st.json(parts)
            else:
                st.warning(f"No valid parts found for Product Offering {product_offering_id}.")

    elif query_type == "Profitable Product Offerings":
        cost_threshold = st.number_input("Enter Cost Threshold", min_value=0.0, value=100.0)
        demand_threshold = st.number_input("Enter Demand Threshold", min_value=0, value=10)

        if st.button("Find Profitable Products"):
            profitable_products = query_profitable_products(graph, cost_threshold, demand_threshold)
            if profitable_products:
                st.write("Profitable Products:")
                for product in profitable_products:
                    st.write(f"Product ID: {product[0]}, Cost: {product[1]}, Demand: {product[2]}")
            else:
                st.warning("No profitable products found under the given thresholds.")


if __name__ == "__main__":
    main()