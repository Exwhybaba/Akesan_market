import dash
from dash import html, dcc, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from app import DailyClosing, Payment, Receipt, Vendor, get_db
import pandas as pd
import plotly.express as px
from flask import current_app

# Get db reference using the function from app.py
def get_session():
    return get_db()

# Daily closing page layout
layout = dbc.Container([
    dbc.Row([
        html.H2("Daily Closing", className="mb-4"),
    ]),
    
    # Daily closing form
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Daily Closing Details"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Closing Date"),
                            dcc.DatePickerSingle(
                                id='closing-date',
                                min_date_allowed=datetime.now() - timedelta(days=30),
                                max_date_allowed=datetime.now(),
                                initial_visible_month=datetime.now(),
                                date=datetime.now().date(),
                            ),
                        ], width=6),
                    ]),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Notes"),
                            dbc.Textarea(
                                id="closing-notes",
                                placeholder="Enter any notes about today's collections...",
                                style={"height": "100px"},
                            ),
                        ], width=12),
                    ], className="mt-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Generate Report", id="generate-closing-button", color="primary", className="mt-3"),
                        ], width={"size": 4, "offset": 4}, className="text-center"),
                    ]),
                ]),
            ], className="mb-4"),
        ]),
    ]),
    
    # Daily Summary Report (shows after generation)
    html.Div(id="daily-summary-container", className="d-none"),
    
    # Previous Closings
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Previous Closings"),
                dbc.CardBody([
                    dash_table.DataTable(
                        id="closings-table",
                        columns=[
                            {"name": "Date", "id": "date"},
                            {"name": "Total Amount", "id": "total_amount"},
                            {"name": "Regular", "id": "regular_amount"},
                            {"name": "Arrears", "id": "arrears_amount"},
                            {"name": "Advance", "id": "advance_amount"},
                            {"name": "Status", "id": "status"},
                            {"name": "Notes", "id": "notes"},
                        ],
                        data=[],
                        page_size=10,
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        row_selectable="single",
                        selected_rows=[],
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "minWidth": "100px", "width": "150px", "maxWidth": "200px",
                            "overflow": "hidden", "textOverflow": "ellipsis",
                        },
                        style_header={
                            "backgroundColor": "rgb(230, 230, 230)",
                            "fontWeight": "bold"
                        },
                    ),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Re-open Selected", id="reopen-closing-button", color="warning", className="mt-3 mr-2"),
                            dbc.Button("View Details", id="view-closing-button", color="info", className="mt-3"),
                        ], width={"size": 6, "offset": 6}, className="text-right"),
                    ]),
                ]),
            ]),
        ]),
    ]),
    
    # Store for selected closing data
    dcc.Store(id="selected-closing-data"),
])

# Callback to generate daily summary report
@callback(
    [Output("daily-summary-container", "children"),
     Output("daily-summary-container", "className")],
    [Input("generate-closing-button", "n_clicks")],
    [State("closing-date", "date"),
     State("closing-notes", "value")]
)
def generate_daily_summary(n_clicks, closing_date, notes):
    if n_clicks is None:
        return "", "d-none"
    
    try:
        # Parse closing date
        closing_date_obj = datetime.strptime(closing_date, "%Y-%m-%d").date()
        
        # Check if a closing already exists for this date
        existing_closing = get_session().query(DailyClosing).filter_by(date=closing_date_obj).first()
        
        if existing_closing:
            if not existing_closing.is_closed:
                # Get payments for this date
                payments = get_payments_for_date(closing_date_obj)
                
                # Update existing closing
                existing_closing.total_amount = payments["total_amount"]
                existing_closing.regular_amount = payments["regular_amount"]
                existing_closing.arrears_amount = payments["arrears_amount"]
                existing_closing.advance_amount = payments["advance_amount"]
                existing_closing.notes = notes
                existing_closing.is_closed = True
                
                # Update payments to link to this daily closing
                for payment in payments["payment_records"]:
                    payment.daily_closing_id = existing_closing.id
                
                get_session().commit()
            
            # Return the closing summary
            return generate_closing_summary_html(existing_closing, closing_date_obj), ""
        else:
            # Get payments for this date
            payments = get_payments_for_date(closing_date_obj)
            
            # Create new daily closing record
            new_closing = DailyClosing(
                date=closing_date_obj,
                total_amount=payments["total_amount"],
                regular_amount=payments["regular_amount"],
                arrears_amount=payments["arrears_amount"],
                advance_amount=payments["advance_amount"],
                notes=notes,
                is_closed=True
            )
            
            get_session().add(new_closing)
            get_session().flush()  # Get the ID without committing yet
            
            # Link payments to this daily closing
            for payment in payments["payment_records"]:
                payment.daily_closing_id = new_closing.id
            
            get_session().commit()
            
            # Return the closing summary
            return generate_closing_summary_html(new_closing, closing_date_obj), ""
    except Exception as e:
        return html.Div([
            dbc.Alert(f"Error generating daily summary: {str(e)}", color="danger"),
        ]), ""

# Function to get payments for a specific date
def get_payments_for_date(date):
    # Get all payments for the specified date
    payments_query = get_session().query(Payment).filter(
        Payment.date == date,
        Payment.daily_closing_id.is_(None)  # Only include payments not already in a closing
    ).all()
    
    # Calculate totals
    total_amount = sum(p.amount for p in payments_query)
    regular_amount = sum(p.amount for p in payments_query if p.payment_type == "regular")
    arrears_amount = sum(p.amount for p in payments_query if p.payment_type == "arrears")
    advance_amount = sum(p.amount for p in payments_query if p.payment_type == "advance")
    
    return {
        "payment_records": payments_query,
        "total_amount": total_amount,
        "regular_amount": regular_amount,
        "arrears_amount": arrears_amount,
        "advance_amount": advance_amount,
    }

# Function to generate closing summary HTML
def generate_closing_summary_html(closing, date):
    # Get payment details for this closing
    payment_details = get_session().query(
        Payment.id,
        Vendor.name.label('vendor_name'),
        Vendor.shop_number,
        Vendor.block,
        Payment.amount,
        Payment.payment_type,
        Payment.year,
        Receipt.receipt_number
    ).join(
        Vendor, Payment.vendor_id == Vendor.id
    ).join(
        Receipt, Receipt.payment_id == Payment.id
    ).filter(
        Payment.daily_closing_id == closing.id
    ).all()
    
    # Convert to DataFrame for the table
    payment_data = []
    for row in payment_details:
        payment_data.append({
            "receipt_number": row.receipt_number,
            "vendor_name": row.vendor_name,
            "shop_number": row.shop_number,
            "block": row.block,
            "amount": f"₦{row.amount:,.2f}",
            "payment_type": row.payment_type.title(),
            "year": row.year,
        })
    
    # Create closing report HTML
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H3(f"Daily Closing Summary - {date.strftime('%d-%m-%Y')}", className="text-center"),
            ]),
            dbc.CardBody([
                # Summary figures
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Total Collection", className="card-title"),
                                html.H3(f"₦{closing.total_amount:,.2f}", className="card-text text-primary"),
                            ])
                        ]),
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Regular Payments", className="card-title"),
                                html.H3(f"₦{closing.regular_amount:,.2f}", className="card-text text-success"),
                            ])
                        ]),
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Arrears Payments", className="card-title"),
                                html.H3(f"₦{closing.arrears_amount:,.2f}", className="card-text text-warning"),
                            ])
                        ]),
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H5("Advance Payments", className="card-title"),
                                html.H3(f"₦{closing.advance_amount:,.2f}", className="card-text text-info"),
                            ])
                        ]),
                    ], width=3),
                ]),
                
                # Notes section
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5("Notes", className="mt-4"),
                            html.P(closing.notes or "No notes provided"),
                        ], className="mt-4"),
                    ]),
                ]),
                
                # Payment details table
                dbc.Row([
                    dbc.Col([
                        html.H5("Payment Details", className="mt-4"),
                        dash_table.DataTable(
                            id="closing-payments-table",
                            columns=[
                                {"name": "Receipt #", "id": "receipt_number"},
                                {"name": "Vendor", "id": "vendor_name"},
                                {"name": "Shop", "id": "shop_number"},
                                {"name": "Block", "id": "block"},
                                {"name": "Amount", "id": "amount"},
                                {"name": "Type", "id": "payment_type"},
                                {"name": "Year", "id": "year"},
                            ],
                            data=payment_data,
                            page_size=10,
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "minWidth": "100px", "width": "150px", "maxWidth": "200px",
                                "overflow": "hidden", "textOverflow": "ellipsis",
                            },
                            style_header={
                                "backgroundColor": "rgb(230, 230, 230)",
                                "fontWeight": "bold"
                            },
                        ),
                    ]),
                ]),
                
                # Print and export buttons
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Print Report", id="print-closing-btn", color="primary", className="mt-4 mr-2"),
                        dbc.Button("Export CSV", id="export-closing-csv", color="success", className="mt-4"),
                        dcc.Download(id="download-closing-csv"),
                    ], width={"size": 6, "offset": 3}, className="text-center"),
                ]),
            ]),
        ], className="mb-4"),
        
        # Script for printing
        html.Script("""
            function printClosingReport() {
                const printContents = document.querySelector('.closing-report').innerHTML;
                const originalContents = document.body.innerHTML;
                document.body.innerHTML = printContents;
                window.print();
                document.body.innerHTML = originalContents;
                return null;
            }
        """)
    ], className="closing-report")

# Callback to update previous closings table
@callback(
    Output("closings-table", "data"),
    [Input("generate-closing-button", "n_clicks"),
     Input("reopen-closing-button", "n_clicks")]
)
def update_closings_table(n1, n2):
    closings = get_session().query(DailyClosing).order_by(DailyClosing.date.desc()).all()
    
    closings_data = []
    for closing in closings:
        closings_data.append({
            "id": closing.id,
            "date": closing.date.strftime("%Y-%m-%d"),
            "total_amount": f"₦{closing.total_amount:,.2f}",
            "regular_amount": f"₦{closing.regular_amount:,.2f}",
            "arrears_amount": f"₦{closing.arrears_amount:,.2f}",
            "advance_amount": f"₦{closing.advance_amount:,.2f}",
            "status": "Closed" if closing.is_closed else "Open",
            "notes": closing.notes[:50] + "..." if closing.notes and len(closing.notes) > 50 else closing.notes or "",
        })
    
    return closings_data

# Callback to re-open a closing
@callback(
    Output("closings-table", "selected_rows"),
    [Input("reopen-closing-button", "n_clicks")],
    [State("closings-table", "selected_rows"),
     State("closings-table", "data")]
)
def reopen_closing(n_clicks, selected_rows, data):
    if n_clicks is None or not selected_rows:
        return []
    
    try:
        row_idx = selected_rows[0]
        closing_id = data[row_idx]["id"]
        closing = get_session().query(DailyClosing).get(closing_id)
        
        if closing:
            closing.is_closed = False
            get_session().commit()
    except Exception as e:
        get_session().rollback()
    
    return []

# Callback to view closing details
@callback(
    [Output("selected-closing-data", "data"),
     Output("daily-summary-container", "children", allow_duplicate=True),
     Output("daily-summary-container", "className", allow_duplicate=True)],
    [Input("view-closing-button", "n_clicks")],
    [State("closings-table", "selected_rows"),
     State("closings-table", "data")],
    prevent_initial_call=True
)
def view_closing_details(n_clicks, selected_rows, data):
    if n_clicks is None or not selected_rows:
        return {}, "", "d-none"
    
    try:
        row_idx = selected_rows[0]
        closing_id = data[row_idx]["id"]
        closing = get_session().query(DailyClosing).get(closing_id)
        
        if closing:
            # Generate summary HTML
            closing_date = datetime.strptime(data[row_idx]["date"], "%Y-%m-%d").date()
            summary_html = generate_closing_summary_html(closing, closing_date)
            
            return {"id": closing.id}, summary_html, ""
    except Exception as e:
        pass
    
    return {}, "", "d-none"

# Callback for exporting closing details to CSV
@callback(
    Output("download-closing-csv", "data"),
    Input("export-closing-csv", "n_clicks"),
    State("selected-closing-data", "data"),
    prevent_initial_call=True
)
def export_closing_csv(n_clicks, closing_data):
    if not closing_data or "id" not in closing_data:
        return None
    
    # Get payment details for this closing
    payment_details = get_session().query(
        Payment.id,
        Vendor.name.label('vendor_name'),
        Vendor.shop_number,
        Vendor.block,
        Payment.amount,
        Payment.payment_type,
        Payment.year,
        Receipt.receipt_number,
        Payment.date
    ).join(
        Vendor, Payment.vendor_id == Vendor.id
    ).join(
        Receipt, Receipt.payment_id == Payment.id
    ).filter(
        Payment.daily_closing_id == closing_data["id"]
    ).all()
    
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
    } for row in payment_details]
    
    df = pd.DataFrame(data)
    
    closing = get_session().query(DailyClosing).get(closing_data["id"])
    filename = f"closing_{closing.date.strftime('%Y%m%d')}.csv"
    
    return dcc.send_data_frame(df.to_csv, filename, index=False) 