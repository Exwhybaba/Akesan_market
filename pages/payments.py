import dash
from dash import html, dcc, Input, Output, State, callback, dash_table, ALL, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import uuid
from sqlalchemy import func, extract
from app import Vendor, Payment, Receipt, get_db, app
import pandas as pd
import plotly.express as px
from flask import current_app, jsonify, request
import json

# Get db reference using the function from app.py
def get_session():
    return get_db()

# Default annual market fee
ANNUAL_FEE = 12000  # ₦12,000

# Payments page layout
layout = dbc.Container([
    dbc.Row([
        html.H2("Payment Management", className="mb-4"),
    ]),
    
    # Vendor selection for payment
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Select Vendor"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Search Vendor"),
                            dbc.Input(id="payment-vendor-search", type="text", placeholder="Search by name, shop or block"),
                        ]),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Div(id="vendor-search-results", className="mt-3"),
                        ]),
                    ]),
                ]),
            ], className="mb-4"),
        ]),
    ]),
    
    # Payment Form (shows after vendor is selected)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Payment Information"),
                dbc.CardBody([
                    html.Div(id="selected-vendor-info"),
                    html.Hr(),
                    
                    # Payment Type Selection
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Payment Type"),
                            dcc.Dropdown(
                                id="payment-type",
                                options=[
                                    {"label": "Regular Payment", "value": "regular"},
                                    {"label": "Arrears Payment", "value": "arrears"},
                                    {"label": "Advance Payment", "value": "advance"},
                                ],
                                placeholder="Select payment type",
                                value="regular",
                                clearable=False,
                            ),
                        ], width=6),
                        
                        dbc.Col([
                            dbc.Label("Payment Year"),
                            dcc.Dropdown(
                                id="payment-year",
                                placeholder="Select year",
                                clearable=False,
                            ),
                        ], width=6),
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Amount (₦)"),
                            dbc.Input(id="payment-amount", type="number", value=ANNUAL_FEE),
                        ], width=6),
                        
                        dbc.Col([
                            dbc.Label("Payment Date"),
                            dcc.DatePickerSingle(
                                id='payment-date',
                                min_date_allowed=datetime(2000, 1, 1),
                                max_date_allowed=datetime.now(),
                                initial_visible_month=datetime.now(),
                                date=datetime.now().date(),
                            ),
                        ], width=6),
                    ], className="mt-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Process Payment", id="process-payment-button", color="success", className="mt-4"),
                            html.Div(id="payment-alert", className="mt-2"),
                        ], width={"size": 6, "offset": 3}, className="text-center"),
                    ]),
                    
                    # Receipt Preview (shows after successful payment)
                    html.Div(id="receipt-container", className="mt-4 d-none"),
                ]),
            ], className="mb-4"),
        ]),
    ]),
    
    # Payment History
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Payment History"),
                dbc.CardBody([
                    html.Div(id="payment-delete-alert"),
                    dash_table.DataTable(
                        id="payment-history-table",
                        columns=[
                            {"name": "Receipt #", "id": "receipt_number"},
                            {"name": "Vendor", "id": "vendor_name"},
                            {"name": "Shop", "id": "shop_number"},
                            {"name": "Block", "id": "block"},
                            {"name": "Amount", "id": "amount"},
                            {"name": "Type", "id": "payment_type"},
                            {"name": "Year", "id": "year"},
                            {"name": "Date", "id": "date"},
                            {"name": "Time", "id": "time"},
                            {"name": "Action", "id": "action"},
                        ],
                        data=[],
                        page_size=10,
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "minWidth": "80px", "width": "120px", "maxWidth": "180px",
                            "overflow": "hidden", "textOverflow": "ellipsis",
                        },
                        style_header={
                            "backgroundColor": "rgb(230, 230, 230)",
                            "fontWeight": "bold"
                        },
                        style_data_conditional=[
                            {
                                'if': {'column_id': 'action'},
                                'cursor': 'pointer',
                                'color': 'red',
                                'textAlign': 'center',
                                'fontWeight': 'bold',
                            }
                        ],
                        row_selectable=False,
                        cell_selectable=True,
                    ),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Export CSV", id="export-payments-csv", color="primary", className="mt-3"),
                            dcc.Download(id="download-payments-csv"),
                        ], width={"size": 3, "offset": 9}),
                    ]),
                ]),
            ]),
        ]),
    ]),
    
    # Stores for data
    dcc.Store(id="selected-vendor-data"),
    dcc.Store(id="selected-payment-id"),
    dcc.Store(id="refresh-payment-history", data=0),
])

# Add hidden refresh button
layout.children.append(html.Button(id='refresh-payment-table', style={'display': 'none'}))
layout.children.append(dcc.Store(id='payment-to-delete'))

# Callback for vendor search
@callback(
    Output("vendor-search-results", "children"),
    [Input("payment-vendor-search", "value")]
)
def search_vendors(search_term):
    if not search_term or len(search_term) < 2:
        return html.Div("Enter at least 2 characters to search")
    
    search_term = f"%{search_term}%"
    vendors = get_session().query(Vendor).filter(
        (Vendor.name.ilike(search_term)) | 
        (Vendor.shop_number.ilike(search_term)) | 
        (Vendor.block.ilike(search_term))
    ).all()
    
    if not vendors:
        return html.Div("No vendors found", className="text-danger")
    
    vendor_list = []
    for vendor in vendors:
        vendor_item = dbc.ListGroupItem(
            f"{vendor.name} - Shop {vendor.shop_number}, Block {vendor.block}",
            id={"type": "vendor-item", "index": vendor.id},
            action=True,
            className="vendor-item"
        )
        vendor_list.append(vendor_item)
    
    return html.Div([
        dbc.ListGroup(vendor_list),
        html.Div([
            html.Hr(),
            html.P("Click on a vendor to select for payment", className="text-muted small"),
        ]),
    ])

# Pattern-matching callback for vendor selection
@callback(
    Output("selected-vendor-data", "data"),
    Input({"type": "vendor-item", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def select_vendor(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    # Get the triggered input ID
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    vendor_id = json.loads(triggered_id)["index"]
    
    # Query vendor data
    vendor = get_session().query(Vendor).filter_by(id=vendor_id).first()
    if not vendor:
        return dash.no_update
    
    return {
        "id": vendor.id, 
        "name": vendor.name, 
        "shop_number": vendor.shop_number, 
        "block": vendor.block
    }

# Callback to display selected vendor info and prepare payment form
@callback(
    [Output("selected-vendor-info", "children"),
     Output("payment-year", "options")],
    [Input("selected-vendor-data", "data")]
)
def update_selected_vendor(vendor_data):
    if not vendor_data:
        return html.Div("No vendor selected"), []
    
    # Prepare years for dropdown (current year, past 5 years for arrears, next 3 for advance)
    current_year = datetime.now().year
    years = [{"label": f"{year}", "value": year} for year in range(current_year - 5, current_year + 4)]
    
    # Show vendor information
    return html.Div([
        html.H4(vendor_data["name"], className="text-primary"),
        html.P(f"Shop Number: {vendor_data['shop_number']}"),
        html.P(f"Block: {vendor_data['block']}"),
        
        # Payment status section
        html.Div(id="vendor-payment-status"),
        html.Button(
            "View Payment History", 
            id="view-payment-history-btn",
            className="btn btn-link btn-sm p-0"
        ),
    ]), years

# Add pattern-matching callback for the payment history button
@callback(
    Output("selected-vendor-data", "data", allow_duplicate=True),
    Input("view-payment-history-btn", "n_clicks"),
    State("selected-vendor-data", "data"),
    prevent_initial_call=True
)
def refresh_vendor_data(n_clicks, data):
    if n_clicks and data:
        # Return the same data to trigger an update in dependent callbacks
        return data
    # Fallback case
    raise dash.exceptions.PreventUpdate

# Callback to filter available years based on payment type
@callback(
    [Output("payment-year", "value"),
     Output("payment-amount", "value")],
    [Input("payment-type", "value")],
    [State("selected-vendor-data", "data")]
)
def update_payment_year_options(payment_type, vendor_data):
    if not vendor_data or not payment_type:
        return None, ANNUAL_FEE
    
    current_year = datetime.now().year
    
    if payment_type == "regular":
        return current_year, ANNUAL_FEE
    elif payment_type == "arrears":
        return current_year - 1, ANNUAL_FEE
    elif payment_type == "advance":
        return current_year + 1, ANNUAL_FEE
    
    return None, ANNUAL_FEE

# Callback to process payment and generate receipt
@callback(
    [Output("payment-alert", "children"),
     Output("receipt-container", "children"),
     Output("receipt-container", "className")],
    [Input("process-payment-button", "n_clicks")],
    [State("selected-vendor-data", "data"),
     State("payment-type", "value"),
     State("payment-year", "value"),
     State("payment-amount", "value"),
     State("payment-date", "date")]
)
def process_payment(n_clicks, vendor_data, payment_type, payment_year, amount, payment_date):
    if n_clicks is None or not vendor_data or not payment_type or not payment_year or not amount:
        raise dash.exceptions.PreventUpdate
    
    try:
        # Parse payment details
        amount = float(amount)
        vendor_id = vendor_data["id"]
        vendor_name = vendor_data["name"]
        vendor_block = vendor_data["block"]
        vendor_shop = vendor_data["shop_number"]
        
        # Parse payment date if provided
        if payment_date:
            try:
                payment_date = datetime.strptime(payment_date, "%Y-%m-%d").date()
            except:
                # If there's any issue with parsing, use current date
                payment_date = datetime.now().date()
        else:
            payment_date = datetime.now().date()
            
        # Generate payment time
        payment_time = datetime.now().strftime("%H:%M:%S")
        
        # Create payment record
        new_payment = Payment(
            vendor_id=vendor_id,
            amount=amount,
            year=int(payment_year),
            payment_type=payment_type,
            date=payment_date,
            time=payment_time
        )
        
        # Save to database
        get_session().add(new_payment)
        get_session().flush()  # To get the payment ID
        
        # Generate receipt number (simple format: YY-MM-DD-VENDORID-PAYMENTID)
        receipt_number = f"{payment_date.strftime('%y%m%d')}-{vendor_id:04d}-{new_payment.id:04d}"
        
        # Create receipt record
        new_receipt = Receipt(
            vendor_id=vendor_id,
            issue_date=payment_date,
            amount=amount,
            year=int(payment_year),
            receipt_number=receipt_number,
            payment_id=new_payment.id
        )
        
        # Save to database and commit both payment and receipt
        get_session().add(new_receipt)
        get_session().commit()
        
        # Generate printable receipt
        receipt_html = dbc.Card([
            dbc.CardBody([
                html.Div([
                    # Receipt Header
                    html.Div([
                        html.H5("OYO EAST LOCAL GOVERNMENT", className="receipt-title mb-0"),
                        html.H6("MARKET MANAGEMENT SYSTEM", className="mb-3"),
                        html.Div([
                            html.Strong("OFFICIAL RECEIPT", className="d-block"),
                            html.Small(f"Receipt #: {receipt_number}", className="receipt-number d-block"),
                            html.Small(f"Date: {payment_date.strftime('%d-%b-%Y')} | Time: {payment_time}", className="d-block"),
                        ]),
                    ], className="text-center receipt-header"),
                    
                    # Vendor Details
                    html.Div([
                        html.Strong("VENDOR DETAILS", className="d-block mb-2"),
                        html.Div([
                            html.Div([
                                html.Span("Name: ", className="font-weight-bold"),
                                html.Span(vendor_name)
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Shop: ", className="font-weight-bold"),
                                html.Span(vendor_shop)
                            ], className="mb-1"),
                            html.Div([
                                html.Span("Block: ", className="font-weight-bold"),
                                html.Span(vendor_block)
                            ]),
                        ])
                    ], className="my-3 py-2 vendor-details"),
                    
                    # Payment Details
                    html.Div([
                        html.Strong("PAYMENT DETAILS", className="d-block mb-2"),
                        html.Table([
                            html.Thead([
                                html.Tr([
                                    html.Th("Description", style={"width": "50%"}),
                                    html.Th("Year", style={"width": "25%"}),
                                    html.Th("Amount", style={"width": "25%", "text-align": "right"}),
                                ])
                            ]),
                            html.Tbody([
                                html.Tr([
                                    html.Td(f"Market Fee ({payment_type.title()})"),
                                    html.Td(f"{payment_year}"),
                                    html.Td(f"₦{amount:,.2f}", style={"text-align": "right"}),
                                ]),
                                html.Tr([
                                    html.Td("Total", className="font-weight-bold"),
                                    html.Td(""),
                                    html.Td(f"₦{amount:,.2f}", style={"text-align": "right", "font-weight": "bold"}),
                                ]),
                            ])
                        ], className="table table-sm table-bordered payment-details"),
                    ]),
                    
                    # Signature Area
                    html.Div([
                        html.Div([
                            html.Div([
                                html.P("____________________________", className="mb-1"),
                                html.P("Authorized Signature", className="signature-line"),
                            ], className="text-center"),
                        ], className="col-6"),
                        html.Div([
                            html.Div([
                                html.P("____________________________", className="mb-1"),
                                html.P("Vendor Signature", className="signature-line"),
                            ], className="text-center"),
                        ], className="col-6"),
                    ], className="row signature-area mt-4"),
                ], id="receipt-content", className="print-receipt"),
                
                dbc.CardFooter([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Export as PDF", id="print-receipt-btn", color="primary", className="mr-2"),
                        ], width={"size": 6, "offset": 3}, className="text-center"),
                    ]),
                ]),
            ]),
        ])
        
        return dbc.Alert("Payment processed successfully!", color="success"), receipt_html, "mt-4"
    except Exception as e:
        get_session().rollback()
        return dbc.Alert(f"Error processing payment: {str(e)}", color="danger"), "", "mt-4 d-none"

# Use our external print receipt JS function
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            // Use the external function defined in print_receipt.js
            if (window.printReceipt) {
                window.printReceipt('receipt-content');
            } else {
                console.error('printReceipt function not found. Check that print_receipt.js is loaded.');
            }
            return null;
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("print-trigger", "children"),
    Input("print-receipt-btn", "n_clicks"),
    prevent_initial_call=True
)

# Add a hidden div for print trigger if it doesn't exist
if not any(isinstance(child, html.Div) and getattr(child, 'id', None) == 'print-trigger' for child in layout.children):
    layout.children.append(html.Div(id="print-trigger", style={"display": "none"}))

# Callback to update payment history table
@callback(
    Output("payment-history-table", "data"),
    [Input("process-payment-button", "n_clicks"),
     Input("selected-vendor-data", "data"),
     Input("refresh-payment-history", "data")],
    prevent_initial_call=False
)
def update_payment_history(process_click, vendor_data, refresh_count):
    # Query for payments with vendor details
    query = get_session().query(
        Receipt.receipt_number,
        Vendor.name.label('vendor_name'),
        Vendor.shop_number,
        Vendor.block,
        Payment.amount,
        Payment.payment_type,
        Payment.year,
        Payment.date,
        Payment.time,
        Payment.id.label('payment_id')
    ).join(
        Vendor, Receipt.vendor_id == Vendor.id
    ).join(
        Payment, Receipt.payment_id == Payment.id
    )
    
    # Filter by vendor if viewing specific vendor's history or vendor is selected
    if vendor_data:
        query = query.filter(Vendor.id == vendor_data["id"])
    
    # Get results and format for datatable
    results = query.order_by(Payment.date.desc()).all()
    
    payment_data = []
    for row in results:
        payment_data.append({
            "receipt_number": row.receipt_number,
            "vendor_name": row.vendor_name,
            "shop_number": row.shop_number,
            "block": row.block,
            "amount": f"₦{row.amount:,.2f}",
            "payment_type": row.payment_type.title(),
            "year": row.year,
            "date": row.date.strftime("%Y-%m-%d"),
            "time": row.time if row.time else "N/A",
            "action": "Delete",
            "payment_id": row.payment_id
        })
    
    return payment_data

# Callback to capture selected cell for deletion
@callback(
    Output("selected-payment-id", "data"),
    Input("payment-history-table", "active_cell"),
    State("payment-history-table", "data"),
    prevent_initial_call=True
)
def capture_selected_cell(active_cell, table_data):
    if not active_cell:
        return dash.no_update
    
    row_idx = active_cell["row"]
    col_id = active_cell["column_id"]
    
    # Only process if the Delete action is clicked
    if col_id == "action":
        payment_id = table_data[row_idx]["payment_id"]
        return payment_id
    
    return dash.no_update

# Callback to delete selected payment
@callback(
    [Output("payment-delete-alert", "children"),
     Output("refresh-payment-history", "data")],
    Input("selected-payment-id", "data"),
    State("refresh-payment-history", "data"),
    prevent_initial_call=True
)
def delete_selected_payment(payment_id, refresh_count):
    if not payment_id:
        return dash.no_update, dash.no_update
    
    try:
        # First delete the receipt
        receipt = get_session().query(Receipt).filter_by(payment_id=payment_id).first()
        if receipt:
            get_session().delete(receipt)
        
        # Then delete the payment
        payment = get_session().query(Payment).filter_by(id=payment_id).first()
        if payment:
            get_session().delete(payment)
        
        get_session().commit()
        
        # Return success message and increment refresh counter
        return dbc.Alert(
            "Payment record deleted successfully", 
            color="success",
            dismissable=True,
            duration=3000
        ), refresh_count + 1
    
    except Exception as e:
        get_session().rollback()
        return dbc.Alert(
            f"Error deleting payment: {str(e)}", 
            color="danger",
            dismissable=True
        ), refresh_count

# Callback for exporting payment history to CSV
@callback(
    Output("download-payments-csv", "data"),
    Input("export-payments-csv", "n_clicks"),
    prevent_initial_call=True
)
def export_payments_csv(n_clicks):
    # Query for payments with vendor details
    results = get_session().query(
        Receipt.receipt_number,
        Vendor.name.label('vendor_name'),
        Vendor.shop_number,
        Vendor.block,
        Payment.amount,
        Payment.payment_type,
        Payment.year,
        Payment.date
    ).join(
        Vendor, Receipt.vendor_id == Vendor.id
    ).join(
        Payment, Receipt.payment_id == Payment.id
    ).order_by(Payment.date.desc()).all()
    
    # Convert to DataFrame
    data = [{
        "Receipt Number": row.receipt_number,
        "Vendor Name": row.vendor_name,
        "Shop Number": row.shop_number,
        "Block": row.block,
        "Amount": row.amount,
        "Payment Type": row.payment_type,
        "Year": row.year,
        "Date": row.date.strftime("%Y-%m-%d")
    } for row in results]
    
    df = pd.DataFrame(data)
    
    return dcc.send_data_frame(df.to_csv, "payment_history.csv", index=False)

# Add JavaScript for dynamically adding event listeners to delete buttons
layout.children.append(html.Div([
    html.Script('''
    document.addEventListener('DOMContentLoaded', function() {
        // Function to set up delete button event listeners
        function setupDeleteButtons() {
            document.querySelectorAll('[id^="delete-"]').forEach(function(button) {
                button.addEventListener('click', function() {
                    const paymentId = this.dataset.id;
                    if(confirm('Are you sure you want to delete this payment record?')) {
                        // Trigger the callback for this specific button
                        const triggerObj = {
                            type: 'delete-btn',
                            index: parseInt(paymentId)
                        };
                        
                        // Create a custom event that Dash callbacks listen for
                        const event = new CustomEvent('dash-callback-triggered', {
                            detail: {
                                id: JSON.stringify(triggerObj),
                                prop: 'n_clicks',
                                value: 1
                            }
                        });
                        document.dispatchEvent(event);
                    }
                });
            });
        }
        
        // Set up initial buttons
        setupDeleteButtons();
        
        // Set up a mutation observer to watch for new buttons being added to the table
        const observer = new MutationObserver(function(mutations) {
            setupDeleteButtons();
        });
        
        // Start observing the document body for changes
        observer.observe(document.body, { childList: true, subtree: true });
    });
    ''')
])) 