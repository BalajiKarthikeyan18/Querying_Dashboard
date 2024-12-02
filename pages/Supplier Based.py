import streamlit as st
import time  # Ensure this is imported properly
import tracemalloc
import functools
import json
import base64
from datetime import datetime
from collections import Counter

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
def supplier_reliability_costing_temporal(graph, reliability_threshold, max_transportation_cost):
    """
    Analyze supplier reliability and transportation costs at a specific timestamp in a temporal graph.

    Parameters:
        tg (TemporalGraph): The temporal graph object.
        timestamp (int): The specific timestamp to analyze.
        reliability_threshold (float): The maximum acceptable reliability threshold for suppliers.
        max_transportation_cost (float): The maximum acceptable transportation cost.

    Returns:
        list: A list of suppliers meeting the criteria, including supplier ID, reliability, and transportation cost.
    """
    # Load the graph for the specified timestamp

    suppliers = []

    # Iterate through edges to find SupplierToWarehouse relationships
    for u, v, data in graph.edges(data=True):

        if data.get("relationship_type") == "SupplierToWarehouse":

            transportation_cost = data.get("transportation_cost", 0)

            # Check transportation cost and reliability
            if transportation_cost >= max_transportation_cost:
                reliability = graph.nodes[u].get("reliability", 0)
                if reliability <= reliability_threshold:
                    suppliers.append((u, reliability, transportation_cost))

    return suppliers


@time_and_memory
def supplier_reliability_costing_json(json_graph, reliability_threshold, max_transportation_cost):
    """
    Analyze supplier reliability and transportation costs at a specific timestamp in a temporal graph.

    Parameters:
        tg (TemporalGraph): The temporal graph object.
        timestamp (int): The specific timestamp to analyze.
        reliability_threshold (float): The maximum acceptable reliability threshold for suppliers.
        max_transportation_cost (float): The maximum acceptable transportation cost.

    Returns:
        list: A list of suppliers meeting the criteria, including supplier ID, reliability, and transportation cost.
    """
    # Load the graph for the specified timestamp
    suppliers = []

    # Iterate through edges to find SupplierToWarehouse relationships
    for i in json_graph["relationship_values"]:

        if i[0] == "SupplierToWarehouse":

            transportation_cost = i[1]

            # Check transportation cost and reliability
            if transportation_cost >= max_transportation_cost:
                supplier_id = i[-2]
                # reliability =
                for nodes in json_graph["node_values"]["Supplier"]:
                    if nodes[-1] == supplier_id:
                        reliability = nodes[3]
                        break

                if reliability <= reliability_threshold:
                    suppliers.append(
                        (supplier_id, reliability, transportation_cost))

    return suppliers


@time_and_memory
def query_supplied_part_types_for_supplier(G, supplier_id):
    if supplier_id in G.nodes and G.nodes[supplier_id].get("node_type") == "Supplier":
        supplied_part_types = G.nodes[supplier_id].get("supplied_part_types")
        return supplied_part_types
    else:
        return None


@time_and_memory
def query_supplied_part_types_for_supplier_json(json_graph, supplier_id):
    for nodes in json_graph["node_values"]["Supplier"]:
        if nodes[-1] == supplier_id:
            return nodes[-2]
    return None

@time_and_memory
def query_lead_time_supplier_to_warehouse(G, supplier_id, warehouse_id):
    if G.has_edge(supplier_id, warehouse_id):
        edge_data = G[supplier_id][warehouse_id]
        if edge_data.get("relationship_type") == "SupplierToWarehouse":
            lead_time = edge_data.get("lead_time")
            return lead_time
        else:
            return None
    else:
        return None

@time_and_memory
def query_lead_time_supplier_to_warehouse_json(json_graph, supplier_id, warehouse_id):
    for edge in json_graph["relationship_values"]:
        if edge[0] == "SupplierToWarehouse" and edge[-2] == supplier_id and edge[-1] == warehouse_id:
            return edge[2]
    return None



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

@time_and_memory
def query_valid_parts_nx(graph, start_date: str, end_date: str):
    # Convert start and end dates to datetime objects
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        return []

    # Load the graph at the given timestamp
    # graph = temporal_graph.load_graph_at_timestamp(timestamp)
    
    # List to store valid parts (node IDs)
    valid_parts = []
    
    # Iterate through the nodes in the graph
    for node, attributes in graph.nodes(data=True):
        # Extract valid_from and valid_till, with default empty string if not present
        valid_from_str = attributes.get('valid_from', '')
        valid_till_str = attributes.get('valid_till', '')
        
        # Only process valid nodes with valid dates
        if valid_from_str and valid_till_str:
            try:
                valid_from = datetime.strptime(valid_from_str, "%Y-%m-%d")
                valid_till = datetime.strptime(valid_till_str, "%Y-%m-%d")
                
                # Check if the node is valid within the given date range
                if valid_from <= end_date and valid_till >= start_date:
                    valid_parts.append(node)
            except ValueError:
                # Handle any invalid date format gracefully
                print(f"Skipping node {node} due to invalid date format.")
                continue
    
    return valid_parts


@time_and_memory
def query_valid_parts_json(data, start_date: str, end_date: str):
    # Convert start and end dates to datetime objects
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        return []

    # Load the JSON data at the given timestamp
    # with open(temporal_graph.files[timestamp], 'r') as f:
    #     data = json.load(f)
    
    # List to store valid parts (node IDs)
    valid_parts = []

    # Access the node values from the data
    node_values = data.get("node_values", {}).get("Parts", [])
    
    # Iterate over nodes to check validity dates
    for node in node_values:
        # Extract valid_from and valid_till
        try:
            valid_from = datetime.strptime(node[6], "%Y-%m-%d")  # Assuming 'valid_from' is at index 4
            valid_till = datetime.strptime(node[7], "%Y-%m-%d")  # Assuming 'valid_till' is at index 5
        except ValueError:
            print(f"Skipping node due to invalid date format: {node}")
            continue
        
        # Extract node ID (last element in node list)
        node_id = node[-1]

        # If the node is valid within the given range, add it to the list
        if valid_from <= end_date and valid_till >= start_date:
            valid_parts.append(node_id)

    return valid_parts


@time_and_memory
def query_most_common_subtypes_json(temporal_graph, timestamp: int, n: int):
   
    # Load the JSON data at the given timestamp
    with open(temporal_graph.files[timestamp], 'r') as f:
        data = json.load(f)
    
    # List to store subtypes
    subtypes = []

    # Access the node values from the data
    node_values = data.get("node_values", {}).get("Parts", [])
    
    # Iterate over nodes and extract the subtypes (index 3 is the position of 'subtype' in the data schema)
    for node in node_values:
        subtypes.append(node[3])

    # Use Counter to count occurrences of each subtype
    subtype_counts = Counter(subtypes)

    # Get the n most common subtypes
    most_common_subtypes = subtype_counts.most_common(n)

    return most_common_subtypes


@time_and_memory
def query_most_common_subtypes_nx(temporal_graph, timestamp: int, n: int):
    
    # Load the graph at the given timestamp
    graph = temporal_graph.load_graph_at_timestamp(timestamp)

    # List to store subtypes
    subtypes = []

    # Iterate through the nodes in the graph and extract the 'subtype' from the node attributes
    for node, attributes in graph.nodes(data=True):
        subtype = attributes.get('subtype', None)
        if subtype:
            subtypes.append(subtype)

    # Use Counter to count occurrences of each subtype
    subtype_counts = Counter(subtypes)

    # Get the n most common subtypes
    most_common_subtypes = subtype_counts.most_common(n)

    return most_common_subtypes




def main():

    if "temporal_graph" not in st.session_state:
        st.error(
            "No Temporal Graph found in the session state. Please run the main script first.")
        return

    timestamp = st.select_slider("Select Timestamp", options=range(
        len(st.session_state.temporal_graph.files)))

    graph = st.session_state.temporal_graph.load_graph_at_timestamp(timestamp)

    with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
        json_graph = json.load(f)

    all_parts = []
    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("node_type") == "Parts":
            all_parts.append(node_id)

    # Load and encode the image
    networkx_image = encode_image("pages\graph.png")
    json_image = encode_image("pages\json.png")

    queries = st.selectbox("Select Query", [
                           "Select Query", "Supplier Reliability and Costing",
                             "Supplied Part Types",
                               "Lead Time Supplier to Warehouse",
                                 "Find Suppliers for a Part", 
                                 "Find Valid Parts for a given Date Range",
                                   "Find Most Common Parts Used"
                               ])

    if queries == "Supplier Reliability and Costing":

        st.write(
            "This query will return suppliers meeting the criteria of reliability and transportation cost.")
        reliability_threshold = st.number_input(
            "Reliability Threshold", value=0.8, min_value=0.0, max_value=1.0, step=0.01)
        max_transportation_cost = st.number_input(
            "Max Transportation Cost", value=800, min_value=10, max_value=10000, step=10)

        # cols = st.columns(2)

        # with cols[0]:
        #     st.write("Result using Networkx:")
        #     suppliers = supplier_reliability_costing_temporal(graph, reliability_threshold, max_transportation_cost)
        #     if suppliers:
        #         for supplier in suppliers:
        #             st.write(f"Supplier ID: {supplier[0]}, Reliability: {supplier[1]}, Transportation Cost: {supplier[2]}")
        #     else:
        #         st.write("No suppliers meet the criteria.")

        # with cols[1]:
        #     st.write("Result using JSON:")
        #     suppliers = supplier_reliability_costing_json(json_graph, reliability_threshold, max_transportation_cost)

        #     if suppliers:
        #         for supplier in suppliers:
        #             st.write(f"Supplier ID: {supplier[0]}, Reliability: {supplier[1]}, Transportation Cost: {supplier[2]}")
        #     else:
        #         st.write("No suppliers meet the criteria.")

        # Two-column layout for displaying results
        cols = st.columns(2, gap="large")

        # Define styles for success and error messages
        success_style = "color: white; font-weight: bold;"
        error_style = "color: red; font-weight: bold;"

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
            st.divider()  # Optional: Add a horizontal line for separation

            suppliers_networkx = supplier_reliability_costing_temporal(
                graph, reliability_threshold, max_transportation_cost)

            if suppliers_networkx:
                for supplier in suppliers_networkx:
                    st.markdown(
                        f"""
                        <div style="{success_style}">
                        Supplier ID: `{supplier[0]}`<br>
                        Reliability: `{supplier[1]:.4f}`<br>
                        Transportation Cost: `{supplier[2]:.2f}`
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.divider()
            else:
                st.markdown(
                    f"<div style='{error_style}'>No suppliers meet the criteria.</div>",
                    unsafe_allow_html=True,
                )

        # Right column: Results using JSON
        with cols[1]:
            # st.markdown("### 🗃️ Result using **JSON**")
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;">  Result using **JSON**
                """.format(
                    base64_image=json_image
                ),
                unsafe_allow_html=True,
            )
            st.divider()  # Optional: Add a horizontal line for separation

            suppliers_json = supplier_reliability_costing_json(
                json_graph, reliability_threshold, max_transportation_cost)

            if suppliers_json:
                for supplier in suppliers_json:
                    st.markdown(
                        f"""
                        <div style="{success_style}">
                        Supplier ID: `{supplier[0]}`<br>
                        Reliability: `{supplier[1]:.4f}`<br>
                        Transportation Cost: `{supplier[2]:.2f}`
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.divider()
            else:
                st.markdown(
                    f"<div style='{error_style}'>No suppliers meet the criteria.</div>",
                    unsafe_allow_html=True,
                )

        # Add spacing for better layout management
        # st.write("---")

    elif queries == "Supplied Part Types":
        st.write(
            "This query will return the part types supplied by a specific supplier.")

        # supplier_id = st.number_input("Supplier ID", value=0)
        all_suppliers = [node for node in graph.nodes if graph.nodes[node].get(
            "node_type") == "Supplier"]
        supplier_id = st.selectbox("Select Supplier ID", options=all_suppliers)

        cols = st.columns(2, gap="large")

        # Define styles for success and error messages
        success_style = "color: white; font-weight: bold;"
        error_style = "color: red; font-weight: bold;"

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
            supplied_part_types = query_supplied_part_types_for_supplier(
                graph, supplier_id)

            if supplied_part_types is not None:
                st.markdown(
                    f" #### Supplier {supplier_id} supplies the following part types:",
                    unsafe_allow_html=True,
                )

                for part_type in supplied_part_types:
                    st.markdown(
                        f"<div style='{success_style}'>{part_type}</div>",
                        unsafe_allow_html=True,
                    )

            else:
                st.markdown(
                    f"<div style='{error_style}'>Supplier {supplier_id} does not exist in the graph or is not a supplier.</div>",
                    unsafe_allow_html=True,
                )

        with cols[1]:
            # st.write("### 🗃️ Result using **JSON**")
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;">  Result using **JSON**
                """.format(
                    base64_image=json_image
                ),
                unsafe_allow_html=True,
            )
            supplied_part_types = query_supplied_part_types_for_supplier_json(
                json_graph, supplier_id)

            if supplied_part_types is not None:
                st.markdown(
                    f" #### Supplier {supplier_id} supplies the following part types:",
                    unsafe_allow_html=True,
                )

                for part_type in supplied_part_types:
                    st.markdown(
                        f"<div style='{success_style}'>{part_type}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    f"<div style='{error_style}'>Supplier {supplier_id} does not exist in the graph or is not a supplier.</div>",
                    unsafe_allow_html=True,
                )

    elif queries == "Lead Time Supplier to Warehouse":

        st.write(
            "This query will return the lead time for a specific Supplier to Warehouse relationship.")

        all_suppliers = [node for node in graph.nodes if graph.nodes[node].get(
            "node_type") == "Supplier"]
        all_warehouses = [node for node in graph.nodes if graph.nodes[node].get(
            "node_type") == "Warehouse"]

        supplier_id = st.selectbox("Select Supplier ID", options=all_suppliers)
        warehouse_id = st.selectbox("Select Warehouse ID", options=all_warehouses)

        cols = st.columns(2, gap="large")

        # Define styles for success and error messages
        success_style = "color: white; font-weight: bold;"
        error_style = "color: red; font-weight: bold;"

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
            lead_time = query_lead_time_supplier_to_warehouse(
                graph, supplier_id, warehouse_id)

            if lead_time is not None:
                st.markdown(
                    f" #### Lead time from Supplier {supplier_id} to Warehouse {warehouse_id}:",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='{success_style}'>{lead_time}</div>",
                    unsafe_allow_html=True,
                )

            else:
                st.markdown(
                    f"<div style='{error_style}'>No relationship found between Supplier {supplier_id} and Warehouse {warehouse_id}.</div>",
                    unsafe_allow_html=True,
                )

        with cols[1]:
            # st.write("### 🗃️ Result using **JSON**")
            st.markdown(
                """
                ### <img src="data:image/png;base64,{base64_image}" alt="Icon" style="width: 30px; height: 30px; vertical-align: middle;">  Result using **JSON**
                """.format(
                    base64_image=json_image
                ),
                unsafe_allow_html=True,
            )
            lead_time = query_lead_time_supplier_to_warehouse_json(
                json_graph, supplier_id, warehouse_id)

            if lead_time is not None:
                st.markdown(
                    f" #### Lead time from Supplier {supplier_id} to Warehouse {warehouse_id}:",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='{success_style}'>{lead_time}</div>",
                    unsafe_allow_html=True,
                )

            else:
                st.markdown(
                    f"<div style='{error_style}'>No relationship found between Supplier {supplier_id} and Warehouse {warehouse_id}.</div>",
                    unsafe_allow_html=True,
                )

    
    elif queries == "Find Suppliers for a Part":
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

    elif queries == "Find Valid Parts for a given Date Range":
        st.write("This query retrieves valid parts for a given date range.")
        start_date = st.date_input("Enter Start Date:")
        end_date = st.date_input("Enter End Date:")

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

            valid_parts = query_valid_parts_nx(graph, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            if valid_parts:
                st.write("#### Valid Parts:")
                # Define a scrollable container with fixed height
                with st.container():
                    scrollable_style = """
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;">
                    """
                    # Format each part into a paragraph
                    content = "".join([f"<p>{part}</p>" for part in valid_parts])
                    st.markdown(scrollable_style + content + "</div>", unsafe_allow_html=True)

            else:
                st.warning("#### No valid parts found for the given date range.")

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

            valid_parts_json = query_valid_parts_json(json_graph, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            if valid_parts_json:
                st.write("#### Valid Parts:")
                # Define a scrollable container with fixed height
                with st.container():
                    scrollable_style = """
                    <div style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; border-radius: 5px;"> 
                    """
                    # Format each part into a paragraph
                    content = "".join([f"<p>{part}</p>" for part in valid_parts_json])
                    st.markdown(scrollable_style + content + "</div>", unsafe_allow_html=True)

            else:
                st.warning("#### No valid parts found for the given date range.")

    elif queries == "Find Most Common Parts Used":
        st.write("This query retrieves the most common parts .")
        n = st.number_input("Enter the number of most common parts to retrieve:", min_value=1, value=5, max_value=10)

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

            most_common_parts = query_most_common_subtypes_nx(st.session_state.temporal_graph, timestamp, n)
            if most_common_parts:
                st.write("#### Most Common Parts:")
                for part, count in most_common_parts:
                    st.write(f"Part: {part}, Count: {count}")
            else:
                st.warning("#### No common parts found in the dataset.")

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

            most_common_parts_json = query_most_common_subtypes_json(st.session_state.temporal_graph, timestamp, n)
            if most_common_parts_json:
                st.write("#### Most Common Parts:")
                for part, count in most_common_parts_json:
                    st.write(f"Part: {part}, Count: {count}")
            else:
                st.warning("#### No common parts found in the dataset.")



if __name__ == "__main__":
    main()
