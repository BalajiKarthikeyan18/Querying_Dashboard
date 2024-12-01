import streamlit as st
import json
import functools
import time
import tracemalloc

import base64

# supplier, parts
# warehouse, facility , po

def time_and_memory(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Start tracking memory and time
        tracemalloc.start()
        start_time = time.time()  # Ensure time module is used correctly

        try:
            # Call the actual function
            result = func(*args, **kwargs)
        finally:
            # Calculate memory and time usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            end_time = time.time()
            elapsed_time = end_time - start_time

            # Print results
            st.write(f"**Function Name:** `{func.__name__}`")
            st.write(f"**Time Taken:** `{elapsed_time:.2f} seconds`")
            st.write(
                f"**Memory Usage:** `{current / 1024:.2f} KiB` (Current), `{peak / 1024:.2f} KiB` (Peak)")

        return result
    return wrapper

 # Encode the image to Base64
def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


@time_and_memory
def query_transportation_cost_for_supplier_and_warehouse(G, supplier_id, warehouse_id):

    if G.has_edge(supplier_id, warehouse_id):
        edge_data = G[supplier_id][warehouse_id]
        st.write(edge_data)
        if edge_data.get("relationship_type") == "SupplierToWarehouse":
            return edge_data.get("transportation_cost")
    return None

@time_and_memory
def query_transportation_cost_for_supplier_and_warehouse_json(json_graph, supplier_id, warehouse_id):
    for edge in json_graph["relationship_values"]:
        if edge[0] == "SupplierToWarehouse" and edge[-2] == supplier_id and edge[-1] == warehouse_id:
            return edge[1]
    return None


@time_and_memory
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


@time_and_memory
def query_parts_for_product_offering_json(json_graph, product_offering_id):
    parts = set()
    for edge in json_graph["relationship_values"]:
        if edge[0] == "FacilityToProductOfferings" and edge[-1] == product_offering_id:
            facility_id = edge[-2]
            for part_edge in json_graph["relationship_values"]:
                if part_edge[0] == "PartsToFacility" and part_edge[-1] == facility_id:
                    parts.add(part_edge[-2])
    return list(parts)

@time_and_memory
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


@time_and_memory
def query_profitable_products_json(json_graph, cost_threshold, demand_threshold):
    profitable_products = []
    for node in json_graph["node_values"]["ProductOffering"]:
        product_id = node[-1]
        making_cost = node[2]
        demand = node[3]

        if making_cost <= cost_threshold and demand >= demand_threshold:
            profitable_products.append((product_id, making_cost, demand))

    return profitable_products

@time_and_memory
def query_high_operating_cost_nodes(G, threshold):
    high_cost_nodes = [
        [node,attrs.get("operating_cost,0")] for node, attrs in G.nodes(data=True)
        if attrs.get("node_type") == "Facility" and attrs.get("operating_cost", 0) > threshold
    ]
    return high_cost_nodes

@time_and_memory
def query_high_operating_cost_nodes_json(json_graph, threshold):
    high_cost_nodes = [
        [node[-1], node[-2] ] for node in json_graph["node_values"]["Facility"]
        if node[-2] > threshold
    ]
    return high_cost_nodes


@time_and_memory
def query_suppliers_for_part_via_warehouse(G,part_id):

    warehouses_with_part = [
        s for s,t,data in G.in_edges(part_id, data=True)
        if data.get("relationship_type") == "WarehouseToParts"
    ]


    suppliers = set()
    for warehouse in warehouses_with_part:
        for s,t,data in G.in_edges(warehouse, data=True):
            if data.get("relationship_type") == "SupplierToWarehouse":
                suppliers.add(s)

    return list(suppliers)

@time_and_memory
def query_suppliers_for_part_via_warehouse_json(json_graph, part_id):
    suppliers = set()
    for edge in json_graph["relationship_values"]:
        if edge[0] == "WarehouseToParts" and edge[-1] == part_id:
            # st.write(edge,edge[-2])
            warehouse_id = edge[-2]
            for supplier_edge in json_graph["relationship_values"]:
                if supplier_edge[0] == "SupplierToWarehouse" and supplier_edge[-1] == warehouse_id:
                    # st.write("nothing ",supplier_edge,supplier_edge[-2])
                    suppliers.add(supplier_edge[-2])

    return list(suppliers)


def main():

    if "temporal_graph" not in st.session_state:
        st.error("No Temporal Graph found in the session state. Please run the main script first.")
        return
    
    timestamp = st.select_slider("Select Timestamp", options=range(len(st.session_state.temporal_graph.files)))
    

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
    with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
        json_graph = json.load(f)

    

   
    # Load and encode the image
    networkx_image = encode_image("pages\graph.png")
    json_image = encode_image("pages\json.png")

    all_suppliers = []
    all_warehouses = []
    all_product_offerings = []
    all_parts = []
    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("node_type") == "Supplier":
            all_suppliers.append(node_id)
        elif node_data.get("node_type") == "Warehouse":
            all_warehouses.append(node_id)
        elif node_data.get("node_type") == "ProductOffering":
            all_product_offerings.append(node_id)
        elif node_data.get("node_type") == "Parts":
            all_parts.append(node_id)

    queries = ["Select Query","Find Transportation Cost between supplier and warehouse",
               "Find Parts needed to manufacture a product",
               "Find Profitable Product Offerings",
               "Find High Operating Cost Facilities",
                "Find Suppliers for a Part"
               ]
    query = st.selectbox("Choose Query", queries)

    if query == "Find Transportation Cost between supplier and warehouse":
        
        st.write("This query retrieves the transportation cost between a Supplier and Warehouse.")

        supplier_id = st.selectbox("Select Supplier ID:", options=all_suppliers)
        warehouse_id = st.selectbox("Select Warehouse ID:", options=all_warehouses)

        cols = st.columns(2, gap="large")

        # Define styles for success and error messages
        success_style = "color: white; font-weight: bold;"
        error_style = "color: red; font-weight: bold;"

        # Left column: Results using Networkx
        with cols[0]:
            # st.markdown("### 🌐 Result using **Networkx**")
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;"> Result using **Networkx**
                """.format(
                    base64_image=networkx_image
                ),
                unsafe_allow_html=True,
            )

            st.divider()  # Optional: Add a horizontal line for separation

            transportation_cost = query_transportation_cost_for_supplier_and_warehouse(graph, supplier_id, warehouse_id)
            if transportation_cost is not None:
                st.write(f"#### Transportation cost between {supplier_id} and {warehouse_id}: {transportation_cost}")
            else:
                st.write("#### The given Supplier and Warehouse are not connected.")

        # Right column: Results using JSON
        with cols[1]:
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;">  Result using **JSON**
                """.format(
                    base64_image=json_image
                ),
                unsafe_allow_html=True,
            )
            st.divider()

            transportation_cost_json = query_transportation_cost_for_supplier_and_warehouse_json(json_graph, supplier_id, warehouse_id)
            if transportation_cost_json is not None:
                st.write(f"#### Transportation cost between {supplier_id} and {warehouse_id}: {transportation_cost_json}")
            else:
                st.write("#### The given Supplier and Warehouse are not connected.")

    elif query == "Find Parts needed to manufacture a product":
        st.write("This query retrieves all parts needed to manufacture a given product offering.")
        product_offering_id = st.selectbox("Select Product Offering ID:", options=all_product_offerings)

        cols = st.columns(2, gap="large")

        # Left column: Results using Networkx
        with cols[0]:
            st.markdown(
                 """
                 ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;"> Result using **Networkx**
                 """.format(
                      base64_image=networkx_image
                 ),
                 unsafe_allow_html=True,
                )
            st.divider()

            parts = query_parts_for_product_offering(graph, product_offering_id)
            if parts:
                st.write(f"#### Parts needed to manufacture {product_offering_id}:")
                # Define a scrollable container with fixed height
                with st.container():
                    scrollable_style = """
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;">
                    """
                    content = "".join([f"<p>{part}</p>" for part in parts])  # Format each part as a paragraph
                    st.markdown(scrollable_style + content + "</div>", unsafe_allow_html=True)

               
               
            else:
               st.warning(f"No valid parts found for Product Offering {product_offering_id}.")

        # Right column: Results using JSON
        with cols[1]:
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;"> Result using **JSON**    
                """.format(
                    base64_image=json_image
                ),
                unsafe_allow_html=True
            )
            st.divider()

            parts_json = query_parts_for_product_offering_json(json_graph, product_offering_id)
            if parts_json:
                st.write(f"#### Parts needed to manufacture {product_offering_id}:")
                # Define a scrollable container with fixed height
                with st.container():
                    scrollable_style = """
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;">
                    """
                    content = "".join([f"<p>{part}</p>" for part in parts_json])  # Format each part as a paragraph
                    st.markdown(scrollable_style + content + "</div>", unsafe_allow_html=True)


            else:
                st.warning(f"No valid parts found for Product Offering {product_offering_id}.") 

    elif query == "Find Profitable Product Offerings":  
        st.write("This query retrieves profitable product offerings whose cost is less and the demand is more given the thresholds.")
        cost_threshold = st.number_input("Enter Cost Threshold", min_value=100, value = 1000 ,max_value=10000,step=100)
        demand_threshold = st.number_input("Enter Demand Threshold", min_value=10, value=50,max_value=200,step=5)

        cols = st.columns(2, gap="large")

        # Left column: Results using Networkx
        with cols[0]:
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;"> Result using **Networkx**
                """.format(
                    base64_image=networkx_image
                ),
                unsafe_allow_html=True,
            )
            st.divider()

            profitable_products = query_profitable_products(graph, cost_threshold, demand_threshold)
            if profitable_products:
                st.write("#### Profitable Products:")
                for product in profitable_products:
                    st.write(f"Product ID: {product[0]}, Cost: {product[1]}, Demand: {product[2]}")
            else:
                st.warning("#### No profitable products found under the given thresholds.")

        # Right column: Results using JSON
        with cols[1]:
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;"> Result using **JSON**
                """.format(
                    base64_image=json_image
                ),
                unsafe_allow_html=True,
            )
            st.divider()

            profitable_products_json = query_profitable_products_json(json_graph, cost_threshold, demand_threshold)
            if profitable_products_json:
                st.write("#### Profitable Products:")
                for product in profitable_products_json:
                    st.write(f"Product ID: {product[0]}, Cost: {product[1]}, Demand: {product[2]}")
            else:
                st.warning("#### No profitable products found under the given thresholds.")

    elif query == "Find High Operating Cost Facilities":
        st.write("This query retrieves facilities with high operating costs above the given threshold.")
        threshold = st.number_input("Enter Operating Cost Threshold", min_value=100, value=5000, max_value=10000, step=500)

        cols = st.columns(2, gap="large")

        # Left column: Results using Networkx
        with cols[0]:
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;"> Result using **Networkx**
                """.format(
                    base64_image=networkx_image
                ),
                unsafe_allow_html=True,
            )
            st.divider()

            high_cost_nodes = query_high_operating_cost_nodes(graph, threshold)
            if high_cost_nodes:
                st.write("#### High Operating Cost Facilities:")
                # Define a scrollable container with fixed height
                with st.container():
                    scrollable_style = """
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;">
                    """
                    # Format each facility and its cost into a paragraph
                    content = "".join([f"<p>Facility ID: <b>{facility}</b> operates with a cost of <b>{cost}</b></p>" for facility, cost in high_cost_nodes])
                    st.markdown(scrollable_style + content + "</div>", unsafe_allow_html=True)

            else:
                st.warning("#### No facilities found with operating costs above the given threshold.")

        # Right column: Results using JSON
        with cols[1]:
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;"> Result using **JSON**
                """.format(
                    base64_image=json_image
                ),
                unsafe_allow_html=True,
            )
            st.divider()

            high_cost_nodes_json = query_high_operating_cost_nodes_json(json_graph, threshold)
            if high_cost_nodes_json:
                st.write("#### High Operating Cost Facilities:")
                # Define a scrollable container with fixed height
                with st.container():
                    scrollable_style = """
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;">
                    """
                    # Format each facility and its cost into a paragraph
                    content = "".join([f"<p>Facility ID: <b>{facility}</b> operates with a cost of <b>{cost}</b></p>" for facility, cost in high_cost_nodes_json])
                    st.markdown(scrollable_style + content + "</div>", unsafe_allow_html=True)

            else:
                st.warning("#### No facilities found with operating costs above the given threshold.")

    elif query == "Find Suppliers for a Part":
        st.write("This query retrieves suppliers for a given part via a warehouse.")
        part_id = st.selectbox("Select Part ID:", options=all_parts)

        cols = st.columns(2, gap="large")

        # Left column: Results using Networkx
        with cols[0]:
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;"> Result using **Networkx**
                """.format(
                    base64_image=networkx_image
                ),
                unsafe_allow_html=True,
            )
            st.divider()

            suppliers = query_suppliers_for_part_via_warehouse(graph, part_id)
            if suppliers:
                st.write(f"#### Suppliers for Part {part_id}:")
                # Define a scrollable container with fixed height
                with st.container():
                    scrollable_style = """
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;">
                    """
                    # Format each supplier into a paragraph
                    content = "".join([f"<p>{supplier} supplies this part</p>" for supplier in suppliers])
                    st.markdown(scrollable_style + content + "</div>", unsafe_allow_html=True)

            else:
                st.warning(f"No suppliers found for Part {part_id}.")

        # Right column: Results using JSON
        with cols[1]:
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;"> Result using **JSON**
                """.format(
                    base64_image=json_image
                ),
                unsafe_allow_html=True,
            )
            st.divider()

            suppliers_json = query_suppliers_for_part_via_warehouse_json(json_graph, part_id)
            if suppliers_json:
                st.write(f"#### Suppliers for Part {part_id}:")
                # Define a scrollable container with fixed height
                with st.container():
                    scrollable_style = """
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;">
                    """
                    # Format each
                    content = "".join([f"<p>{supplier} supplies this part</p>" for supplier in suppliers_json])
                    st.markdown(scrollable_style + content + "</div>", unsafe_allow_html=True)

            else:
                st.warning(f"No suppliers found for Part {part_id}.")


if __name__ == "__main__":
    main()