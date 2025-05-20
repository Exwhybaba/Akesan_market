import dash
from dash import html, dcc, Input, Output, State, callback, dash_table, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from sqlalchemy import func
from app import Vendor, get_db
import pandas as pd
import random

# Get db reference using the function from app.py
def get_session():
    return get_db()

# Vendors page layout
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fas fa-store-alt fa-2x text-info float-start me-3 mt-2"),
                html.Div([
                    html.H2("Vendor Management", className="text-primary mb-1"),
                    html.P("Register and manage market vendors", className="text-muted"),
                ])
            ]),
            html.Hr(),
        ], width=12)
    ], className="mb-4"),
    
    # Add Vendor Form
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-user-plus me-2 text-info"),
                        html.H5("Add New Vendor", className="d-inline card-title mb-0"),
                    ])
                ], className="pb-3"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Vendor Name"),
                            dbc.Input(id="vendor-name", type="text", placeholder="Enter vendor name", className="mb-3"),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Shop Number"),
                            dbc.Input(id="shop-number", type="text", placeholder="Enter shop number", className="mb-3"),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Block"),
                            dcc.Dropdown(
                                id="block",
                                options=[
                                    {"label": "Seyi Makinde", "value": "Seyi Makinde"},
                                    {"label": "Oba Adeyemi", "value": "Oba Adeyemi"},
                                    {"label": "Olu Afolabi", "value": "Olu Afolabi"},
                                    {"label": "Block A Open Stall", "value": "Block A Open Stall"},
                                    {"label": "Block B Open Stall", "value": "Block B Open Stall"},
                                    {"label": "Block C Open Stall", "value": "Block C Open Stall"},
                                    {"label": "Open Market", "value": "Open Market"},
                                    {"label": "Making Shift", "value": "Making Shift"}
                                ],
                                placeholder="Select block",
                                clearable=True,
                                className="mb-3"
                            ),
                        ], width=3),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Registration Date"),
                            dcc.DatePickerSingle(
                                id='registration-date',
                                min_date_allowed=datetime(2000, 1, 1),
                                max_date_allowed=datetime.now(),
                                initial_visible_month=datetime.now(),
                                date=datetime.now().date(),
                                className="mb-3"
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-plus me-2"),
                                "Add Vendor"
                            ], id="add-vendor-button", color="info", className="mt-4 shadow-sm"),
                            html.Div(id="add-vendor-alert", className="mt-2"),
                        ], width=6, className="d-flex align-items-start justify-content-end"),
                    ], className="mt-2"),
                ], className="p-3"),
            ], className="mb-4 shadow-lg"),
        ]),
    ]),
    
    # Search and Filter
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-search me-2 text-info"),
                        html.H5("Search & Filter", className="d-inline card-title mb-0"),
                    ])
                ], className="pb-3"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.InputGroup([
                                dbc.InputGroupText([
                                    html.I(className="fas fa-search")
                                ]),
                                dbc.Input(id="vendor-search", type="text", placeholder="Search by name, shop or block"),
                            ], className="mb-3"),
                        ], width=6),
                        dbc.Col([
                            dbc.InputGroup([
                                dbc.InputGroupText([
                                    html.I(className="fas fa-filter")
                                ]),
                                dcc.Dropdown(
                                    id="block-filter",
                                    placeholder="Filter by block",
                                    options=[
                                        {"label": "All Blocks", "value": ""},
                                        {"label": "Seyi Makinde", "value": "Seyi Makinde"},
                                        {"label": "Oba Adeyemi", "value": "Oba Adeyemi"},
                                        {"label": "Olu Afolabi", "value": "Olu Afolabi"},
                                        {"label": "Block A Open Stall", "value": "Block A Open Stall"},
                                        {"label": "Block B Open Stall", "value": "Block B Open Stall"},
                                        {"label": "Block C Open Stall", "value": "Block C Open Stall"},
                                        {"label": "Open Market", "value": "Open Market"},
                                        {"label": "Making Shift", "value": "Making Shift"}

                                    ],
                                    value=None,
                                    className="w-100"
                                ),
                            ], className="mb-3"),
                        ], width=6),
                    ]),
                ], className="p-3"),
            ], className="mb-4 shadow-lg"),
        ]),
    ]),
    
    # Vendor Table
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-list me-2 text-info"),
                        html.H5("Vendor List", className="d-inline card-title mb-0"),
                    ]),
                    html.Small("Click on a row to select for actions", className="text-muted")
                ], className="pb-3"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id="vendor-table",
                        columns=[
                            {"name": "ID", "id": "id"},
                            {"name": "Vendor Name", "id": "name", "editable": True},
                            {"name": "Shop Number", "id": "shop_number", "editable": True},
                            {"name": "Block", "id": "block", "editable": True},
                            {"name": "Registration Date", "id": "registration_date"},
                        ],
                        data=[],
                        page_size=10,
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        row_selectable="single",
                        selected_rows=[],
                        style_table={
                            "overflowX": "auto",
                            "border-radius": "0.5rem",
                            "overflow": "hidden"
                        },
                        style_cell={
                            "minWidth": "100px", 
                            "width": "150px", 
                            "maxWidth": "200px",
                            "overflow": "hidden", 
                            "textOverflow": "ellipsis",
                            "backgroundColor": "#ffffff",
                            "color": "#000000",
                            "fontSize": "14px",
                            "padding": "8px 12px"
                        },
                        style_header={
                            "backgroundColor": "#e9ecef",
                            "fontWeight": "bold",
                            "textAlign": "left",
                            "padding": "12px",
                            "color": "#2c88d9"
                        },
                        style_data_conditional=[
                            {
                                "if": {"row_index": "odd"},
                                "backgroundColor": "#f8f9fa"
                            },
                            {
                                "if": {"state": "selected"},
                                "backgroundColor": "rgba(44, 136, 217, 0.2)",
                                "border": "1px solid #2c88d9"
                            },
                            {
                                "if": {"column_editable": True},
                                "cursor": "pointer"
                            }
                        ],
                        editable=True,
                    ),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Delete Selected Vendor",
                                id="delete-vendor-button",
                                color="danger",
                                className="mt-3 shadow-sm",
                                n_clicks=0  # Initialize n_clicks to avoid None issues
                            ),
                            html.Div(id="delete-status-alert", className="mt-2"),
                        ], width={"size": 4, "offset": 8}),
                    ]),
                ], className="p-3"),
            ], className="mb-4 shadow-lg"),
        ]),
    ]),
    
    # Store for keeping current vendor data
    dcc.Store(id="vendors-data", data=[]),
    
    # Refresh trigger - used to force table refreshes
    dcc.Store(id="refresh-trigger", data=0),
    
    # Hidden interval component for compatibility with dashboard
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # in milliseconds
        n_intervals=0,
        disabled=True  # Disabled to reduce unnecessary updates
    ),
    
    # Hidden date filter for compatibility with dashboard callbacks
    html.Div(
        dcc.DatePickerRange(
            id="date-filter",
            start_date=(datetime.now() - timedelta(days=30)).date(),
            end_date=datetime.now().date(),
            display_format="YYYY-MM-DD"
        ),
        style={"display": "none"}  # Hide this component
    ),
    
    # Hidden payment-type-filter for compatibility with dashboard callbacks
    html.Div(
        dcc.Dropdown(
            id="payment-type-filter",
            options=[
                {"label": "All", "value": "all"},
                {"label": "Regular", "value": "regular"},
                {"label": "Arrears", "value": "arrears"},
                {"label": "Advance", "value": "advance"},
            ],
            value="all"
        ),
        style={"display": "none"}
    ),
    
    # Hidden dashboard components to prevent callback errors
    html.Div([
        # Stat components
        html.Div(id="total-vendors"),
        html.Div(id="total-collections"),
        html.Div(id="outstanding-arrears"),
        html.Div(id="advance-payments"),
        
        # Chart components
        dcc.Graph(id="payment-trends-chart"),
        dcc.Graph(id="payment-status-chart"),
        dcc.Graph(id="advance-payment-chart"),
        
        # Delete button
        dbc.Button(id="delete-vendor-button"),
    ], style={"display": "none"}),
])

# Callback to populate the vendor table
@callback(
    [Output("vendor-table", "data"),
     Output("vendors-data", "data"),
     Output("block-filter", "options", allow_duplicate=True)],
    [Input("vendor-search", "value"),
     Input("block-filter", "value"),
     Input("refresh-trigger", "data")],
    prevent_initial_call='initial_duplicate'
)
def update_vendor_table(search_term, block_filter, refresh_trigger):
    """Update the vendor table based on filters and refresh trigger."""
    # Print debug info about what triggered the callback
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    print(f"update_vendor_table triggered by: {trigger_id}, refresh value: {refresh_trigger}")
    
    query = get_session().query(Vendor)
    
    # Apply search filter if provided
    if search_term:
        search_term = f"%{search_term}%"
        query = query.filter(
            (Vendor.name.ilike(search_term)) | 
            (Vendor.shop_number.ilike(search_term)) | 
            (Vendor.block.ilike(search_term))
        )
    
    # Apply block filter if selected
    if block_filter:
        query = query.filter(Vendor.block == block_filter)
    
    # Get all vendors based on filters
    vendors = query.all()
    print(f"Found {len(vendors)} vendors matching criteria")
    
    # Prepare vendor data for table
    vendor_data = []
    for vendor in vendors:
        vendor_data.append({
            "id": vendor.id,
            "name": vendor.name,
            "shop_number": vendor.shop_number,
            "block": vendor.block,
            "registration_date": vendor.registration_date.strftime("%Y-%m-%d") if vendor.registration_date else "",
        })
    
    # Get unique blocks for the filter dropdown
    blocks = get_session().query(Vendor.block).distinct().all()
    block_options = [
        {"label": "All Blocks", "value": ""},
        {"label": "Seyi Makinde", "value": "Seyi Makinde"},
        {"label": "Oba Adeyemi", "value": "Oba Adeyemi"},
        {"label": "Olu Afolabi", "value": "Olu Afolabi"},
        {"label": "Block A Open Stall", "value": "Block A Open Stall"},
        {"label": "Block B Open Stall", "value": "Block B Open Stall"},
        {"label": "Block C Open Stall", "value": "Block C Open Stall"},
        {"label": "Open Market", "value": "Open Market"},
        {"label": "Making Shift", "value": "Making Shift"}
    ]

    
    # Add any additional blocks from the database that aren't in our predefined list
    existing_block_values = ["", "Seyi Makinde", "Oba Adeyemi", "Olu Afolabi"]
    for block in blocks:
        if block[0] and block[0] not in existing_block_values:
            block_options.append({"label": block[0], "value": block[0]})
    
    return vendor_data, vendor_data, block_options

# Callback to add new vendor
@callback(
    [Output("add-vendor-alert", "children"),
     Output("vendor-name", "value"),
     Output("shop-number", "value"),
     Output("block", "value"),
     Output("refresh-trigger", "data")],
    [Input("add-vendor-button", "n_clicks")],
    [State("vendor-name", "value"),
     State("shop-number", "value"),
     State("block", "value"),
     State("registration-date", "date"),
     State("refresh-trigger", "data")],
    prevent_initial_call=True  # Prevent callback on page load
)
def add_vendor(n_clicks, name, shop_number, block, registration_date, current_refresh):
    print(f"Add Vendor button clicked: n_clicks={n_clicks}")
    print(f"Form values: name='{name}', shop_number='{shop_number}', block='{block}', date='{registration_date}'")
    
    # Handle None values
    name = name or ""
    shop_number = shop_number or ""
    block = block or ""
    
    if not all([name.strip(), shop_number.strip(), block.strip()]):
        print("Validation failed: All fields are required")
        return dbc.Alert("All fields are required!", color="danger"), name, shop_number, block, current_refresh
    
    # Check if shop number and block combination exists
    existing_vendor = get_session().query(Vendor).filter_by(
        shop_number=shop_number,
        block=block
    ).first()
    
    if existing_vendor:
        print(f"Validation failed: Shop {shop_number} and Block {block} combination already exists")
        return dbc.Alert("Shop and Block combination already exists!", color="danger"), name, shop_number, block, current_refresh
    
    # Parse registration date - Dash DatePickerSingle returns date in ISO format
    try:
        # Print for debugging
        print(f"Registration date received: {registration_date}, type: {type(registration_date)}")
        
        # Handle both string and datetime objects
        if isinstance(registration_date, str):
            reg_date = datetime.fromisoformat(registration_date).date()
        else:
            reg_date = registration_date
    except Exception as e:
        print(f"Error parsing date: {str(e)}")
        reg_date = datetime.now().date()
    
    print(f"Using registration date: {reg_date}")
    
    # Create new vendor
    new_vendor = Vendor(
        name=name,
        shop_number=shop_number,
        block=block,
        registration_date=reg_date
    )
    
    try:
        get_session().add(new_vendor)
        get_session().commit()
        print(f"Vendor added successfully: {name}")
        # Increment refresh counter to trigger update
        return dbc.Alert(f"Vendor '{name}' added successfully!", color="success"), "", "", "", current_refresh + 1
    except Exception as e:
        print(f"Error adding vendor to database: {str(e)}")
        get_session().rollback()
        return dbc.Alert(f"Error adding vendor: {str(e)}", color="danger"), name, shop_number, block, current_refresh

# Callback to update vendor data
@callback(
    Output("edit-vendor-alert", "children"),
    [Input("vendor-table", "data_timestamp")],
    [State("vendor-table", "data"),
     State("vendors-data", "data")]
)
def update_vendor_data(timestamp, data, previous_data):
    if timestamp is None:
        return ""
    
    if data is None or previous_data is None or data == previous_data:
        return ""
    
    # Find rows that changed
    changes = []
    for row in data:
        old_row = next((r for r in previous_data if r["id"] == row["id"]), None)
        if old_row and (row["name"] != old_row["name"] or row["shop_number"] != old_row["shop_number"] or row["block"] != old_row["block"]):
            changes.append(row)
    
    if not changes:
        return ""
    
    message = ""
    for row in changes:
        try:
            vendor = get_session().query(Vendor).get(row["id"])
            if vendor:
                # Check if shop+block combination exists
                if (vendor.shop_number != row["shop_number"] or vendor.block != row["block"]):
                    existing = get_session().query(Vendor).filter_by(
                        shop_number=row["shop_number"],
                        block=row["block"]
                    ).first()
                    
                    if existing and existing.id != vendor.id:
                        return dbc.Alert(f"Shop {row['shop_number']} in Block {row['block']} already exists!", color="danger")
                
                vendor.name = row["name"]
                vendor.shop_number = row["shop_number"]
                vendor.block = row["block"]
                get_session().commit()
                message = dbc.Alert("Vendor information updated successfully!", color="success")
        except Exception as e:
            get_session().rollback()
            return dbc.Alert(f"Error updating vendor: {str(e)}", color="danger")
    
    return message

# Simplified delete vendor callback
@callback(
    [Output("delete-status-alert", "children"),
     Output("refresh-trigger", "data", allow_duplicate=True)], 
    [Input("delete-vendor-button", "n_clicks")],
    [State("vendor-table", "selected_rows"),
     State("vendor-table", "data")],
    prevent_initial_call='initial_duplicate'
)
def delete_vendor(n_clicks, selected_rows, data):
    """Delete the selected vendor from the database."""
    # Print debug info
    print(f"Delete button clicked. n_clicks: {n_clicks}")
    print(f"Selected rows: {selected_rows}")
    
    # Check if we have a selection
    if not selected_rows:
        return dbc.Alert("Please select a vendor to delete", color="warning"), 0
    
    try:
        # Get the selected vendor
        row_index = selected_rows[0]
        vendor_id = data[row_index]["id"]
        vendor_name = data[row_index]["name"]
        
        print(f"Attempting to delete vendor ID: {vendor_id}, Name: {vendor_name}")
        
        # Find the vendor in the database
        session = get_session()
        vendor = session.query(Vendor).get(vendor_id)
        
        if not vendor:
            print(f"Vendor with ID {vendor_id} not found in database")
            return dbc.Alert(f"Vendor not found in database", color="danger"), 0
        
        # Delete the vendor and commit
        print(f"Deleting vendor from database: {vendor.name} (ID: {vendor.id})")
        session.delete(vendor)
        session.commit()
        print("Vendor deleted successfully")
        
        # Return success message and increment refresh counter
        refresh_val = random.randint(1, 10000)  # Random value to ensure refresh
        print(f"Setting refresh_trigger to {refresh_val}")
        
        return dbc.Alert(f"Vendor '{vendor_name}' deleted successfully", color="success"), refresh_val
        
    except Exception as e:
        print(f"Error in delete_vendor: {str(e)}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error: {str(e)}", color="danger"), 0

# Separate callback just to clear selected rows after delete
@callback(
    Output("vendor-table", "selected_rows"),
    [Input("delete-status-alert", "children")],
    prevent_initial_call=True
)
def clear_selection(alert):
    return [] 