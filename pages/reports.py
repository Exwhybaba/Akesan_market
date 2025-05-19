import dash
from dash import html, dcc, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from sqlalchemy import func, extract, and_
from app import Vendor, Payment, Receipt, DailyClosing, get_db
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import current_app

# Get db reference using the function from app.py
def get_session():
    return get_db()

# Reports page layout
layout = dbc.Container([
    dbc.Row([
        html.H2("Reports & Analytics", className="mb-4"),
    ]),
    
    # Report Selection Tabs
    dbc.Tabs([
        # Payment Summary Report Tab
        dbc.Tab(label="Payment Summary", children=[
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Date Range"),
                            dcc.DatePickerRange(
                                id='payment-date-range',
                                min_date_allowed=datetime(2000, 1, 1),
                                max_date_allowed=datetime.now(),
                                start_date=datetime.now().replace(day=1).date(),
                                end_date=datetime.now().date(),
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Payment Type"),
                            dcc.Dropdown(
                                id="payment-type-filter",
                                options=[
                                    {"label": "All Types", "value": "all"},
                                    {"label": "Regular", "value": "regular"},
                                    {"label": "Arrears", "value": "arrears"},
                                    {"label": "Advance", "value": "advance"},
                                ],
                                value="all",
                                clearable=False,
                            ),
                        ], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Generate Report", id="generate-payment-report", color="primary", className="mt-3"),
                        ], width={"size": 4, "offset": 4}, className="text-center"),
                    ]),
                    
                    # Report Results
                    html.Div(id="payment-report-container", className="mt-4"),
                ]),
            ]),
        ]),
        
        # Vendor Analysis Tab
        dbc.Tab(label="Vendor Analysis", children=[
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Block Filter"),
                            dcc.Dropdown(
                                id="vendor-block-filter",
                                placeholder="Select block (optional)",
                                options=[],
                                value=None,
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Payment Status"),
                            dcc.Dropdown(
                                id="vendor-status-filter",
                                options=[
                                    {"label": "All Vendors", "value": "all"},
                                    {"label": "Paid (Current Year)", "value": "paid"},
                                    {"label": "With Arrears", "value": "arrears"},
                                    {"label": "With Advance", "value": "advance"},
                                ],
                                value="all",
                                clearable=False,
                            ),
                        ], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Generate Analysis", id="generate-vendor-analysis", color="primary", className="mt-3"),
                        ], width={"size": 4, "offset": 4}, className="text-center"),
                    ]),
                    
                    # Analysis Results
                    html.Div(id="vendor-analysis-container", className="mt-4"),
                ]),
            ]),
        ]),
        
        # Revenue Forecast Tab
        dbc.Tab(label="Revenue Forecast", children=[
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Forecast Period"),
                            dcc.Dropdown(
                                id="forecast-period",
                                options=[
                                    {"label": "Next 3 Months", "value": "3"},
                                    {"label": "Next 6 Months", "value": "6"},
                                    {"label": "Next 12 Months", "value": "12"},
                                ],
                                value="6",
                                clearable=False,
                            ),
                        ], width=6),
                        dbc.Col([
                            dbc.Label("Include Advance Payments"),
                            dbc.RadioItems(
                                id="include-advance",
                                options=[
                                    {"label": "Yes", "value": True},
                                    {"label": "No", "value": False},
                                ],
                                value=True,
                                inline=True,
                            ),
                        ], width=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Generate Forecast", id="generate-forecast", color="primary", className="mt-3"),
                        ], width={"size": 4, "offset": 4}, className="text-center"),
                    ]),
                    
                    # Forecast Results
                    html.Div(id="forecast-container", className="mt-4"),
                ]),
            ]),
        ]),
    ]),
    
    # Export Options
    dbc.Row([
        dbc.Col([
            dbc.Button("Export to CSV", id="export-report-csv", color="success", className="mt-3"),
            dcc.Download(id="download-report-csv"),
        ], width={"size": 3, "offset": 9}, className="text-right mt-3"),
    ]),
])

# Callback to populate block filter dropdown
@callback(
    Output("vendor-block-filter", "options"),
    Input("vendor-analysis-container", "id")
)
def populate_block_filter(container_id):
    blocks = get_session().query(Vendor.block).distinct().all()
    return [{"label": "All Blocks", "value": "all"}] + [{"label": block[0], "value": block[0]} for block in blocks]

# Callback to generate payment summary report
@callback(
    Output("payment-report-container", "children"),
    [Input("generate-payment-report", "n_clicks")],
    [State("payment-date-range", "start_date"),
     State("payment-date-range", "end_date"),
     State("payment-type-filter", "value")]
)
def generate_payment_report(n_clicks, start_date, end_date, payment_type):
    if n_clicks is None:
        return ""
    
    try:
        # Parse dates
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Build query filters
        filters = [Payment.date.between(start_date_obj, end_date_obj)]
        if payment_type != "all":
            filters.append(Payment.payment_type == payment_type)
        
        # Get payment data
        payments = get_session().query(
            Payment.id,
            Payment.date,
            Payment.amount,
            Payment.payment_type,
            Payment.year,
            Vendor.name.label('vendor_name'),
            Vendor.shop_number,
            Vendor.block,
            Receipt.receipt_number
        ).join(
            Vendor, Payment.vendor_id == Vendor.id
        ).join(
            Receipt, Receipt.payment_id == Payment.id
        ).filter(
            *filters
        ).order_by(
            Payment.date.desc()
        ).all()
        
        # Calculate summary stats
        total_amount = sum(payment.amount for payment in payments)
        payment_count = len(payments)
        
        # Prepare data for table
        payment_data = []
        for payment in payments:
            payment_data.append({
                "receipt_number": payment.receipt_number,
                "date": payment.date.strftime("%Y-%m-%d"),
                "vendor_name": payment.vendor_name,
                "shop_number": payment.shop_number,
                "block": payment.block,
                "amount": f"₦{payment.amount:,.2f}",
                "payment_type": payment.payment_type.title(),
                "year": payment.year,
            })
        
        # Group by date for chart
        date_grouped = get_session().query(
            func.date(Payment.date).label('date'),
            func.sum(Payment.amount).label('amount')
        ).filter(
            *filters
        ).group_by(
            func.date(Payment.date)
        ).order_by(
            func.date(Payment.date)
        ).all()
        
        # Create DataFrame for chart
        df_chart = pd.DataFrame([(d.date, d.amount) for d in date_grouped], columns=['date', 'amount'])
        
        # Create chart
        fig = px.line(
            df_chart,
            x='date',
            y='amount',
            title=f"Daily Payment Totals ({start_date_obj.strftime('%d-%m-%Y')} to {end_date_obj.strftime('%d-%m-%Y')})",
            labels={'date': 'Date', 'amount': 'Amount (₦)'},
            markers=True
        )
        
        # Add bar chart
        fig.add_trace(
            go.Bar(
                x=df_chart['date'],
                y=df_chart['amount'],
                name='Daily Total',
                marker_color='lightblue',
                opacity=0.5
            )
        )
        
        fig.update_layout(
            hovermode="x unified",
            yaxis_title="Amount (₦)",
            xaxis_title="Date"
        )
        
        # Create report container
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Total Payments", className="card-title"),
                            html.H3(f"{payment_count}", className="card-text text-primary"),
                        ])
                    ]),
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Total Amount", className="card-title"),
                            html.H3(f"₦{total_amount:,.2f}", className="card-text text-success"),
                        ])
                    ]),
                ], width=6),
            ]),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig),
                ], className="mt-4"),
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Payment Details", className="mt-4"),
                    dash_table.DataTable(
                        id="payment-report-table",
                        columns=[
                            {"name": "Receipt #", "id": "receipt_number"},
                            {"name": "Date", "id": "date"},
                            {"name": "Vendor", "id": "vendor_name"},
                            {"name": "Shop", "id": "shop_number"},
                            {"name": "Block", "id": "block"},
                            {"name": "Amount", "id": "amount"},
                            {"name": "Type", "id": "payment_type"},
                            {"name": "Year", "id": "year"},
                        ],
                        data=payment_data,
                        page_size=10,
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
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
        ])
    except Exception as e:
        return html.Div([
            dbc.Alert(f"Error generating report: {str(e)}", color="danger"),
        ])

# Callback to generate vendor analysis
@callback(
    Output("vendor-analysis-container", "children"),
    [Input("generate-vendor-analysis", "n_clicks")],
    [State("vendor-block-filter", "value"),
     State("vendor-status-filter", "value")]
)
def generate_vendor_analysis(n_clicks, block_filter, status_filter):
    if n_clicks is None:
        return ""
    
    try:
        # Get current year
        current_year = datetime.now().year
        
        # Build base query
        vendors_query = get_session().query(Vendor)
        
        # Apply block filter
        if block_filter and block_filter != "all":
            vendors_query = vendors_query.filter(Vendor.block == block_filter)
        
        # Get all vendors based on filters
        vendors = vendors_query.all()
        
        # Prepare vendor data with payment status
        vendor_data = []
        paid_count = 0
        arrears_count = 0
        advance_count = 0
        
        for vendor in vendors:
            # Check for current year payment
            current_year_payment = get_session().query(Payment).filter(
                Payment.vendor_id == vendor.id,
                Payment.year == current_year,
                Payment.payment_type == 'regular'
            ).first()
            
            # Check for arrears payments
            arrears_payments = get_session().query(Payment).filter(
                Payment.vendor_id == vendor.id,
                Payment.payment_type == 'arrears'
            ).all()
            
            # Check for advance payments
            advance_payments = get_session().query(Payment).filter(
                Payment.vendor_id == vendor.id,
                Payment.payment_type == 'advance'
            ).all()
            
            # Determine payment status
            has_paid_current = current_year_payment is not None
            has_arrears = len(arrears_payments) > 0
            has_advance = len(advance_payments) > 0
            
            # Apply status filter
            include_vendor = True
            if status_filter == "paid" and not has_paid_current:
                include_vendor = False
            elif status_filter == "arrears" and not has_arrears:
                include_vendor = False
            elif status_filter == "advance" and not has_advance:
                include_vendor = False
            
            if include_vendor:
                # Count for summary stats
                if has_paid_current:
                    paid_count += 1
                if has_arrears:
                    arrears_count += 1
                if has_advance:
                    advance_count += 1
                
                # Add to vendor data
                vendor_data.append({
                    "id": vendor.id,
                    "name": vendor.name,
                    "shop_number": vendor.shop_number,
                    "block": vendor.block,
                    "registration_date": vendor.registration_date.strftime("%Y-%m-%d") if vendor.registration_date else "",
                    "paid_current_year": "Yes" if has_paid_current else "No",
                    "has_arrears": "Yes" if has_arrears else "No",
                    "has_advance": "Yes" if has_advance else "No",
                })
        
        # Create summary stats
        total_vendors = len(vendor_data)
        paid_percentage = (paid_count / total_vendors * 100) if total_vendors > 0 else 0
        arrears_percentage = (arrears_count / total_vendors * 100) if total_vendors > 0 else 0
        advance_percentage = (advance_count / total_vendors * 100) if total_vendors > 0 else 0
        
        # Create pie chart for payment status
        status_data = {
            'Status': ['Paid (Current Year)', 'With Arrears', 'With Advance'],
            'Count': [paid_count, arrears_count, advance_count]
        }
        df_status = pd.DataFrame(status_data)
        
        status_fig = px.pie(
            df_status, 
            names='Status', 
            values='Count',
            color='Status',
            color_discrete_map={
                'Paid (Current Year)': '#28a745',
                'With Arrears': '#dc3545',
                'With Advance': '#17a2b8'
            },
            title="Vendor Payment Status Distribution",
            hole=0.4
        )
        
        # Create block distribution chart
        if total_vendors > 0:
            block_data = {}
            for vendor in vendor_data:
                block = vendor["block"]
                if block not in block_data:
                    block_data[block] = 0
                block_data[block] += 1
            
            df_blocks = pd.DataFrame({
                'Block': list(block_data.keys()),
                'Count': list(block_data.values())
            })
            
            block_fig = px.bar(
                df_blocks,
                x='Block',
                y='Count',
                title="Vendors by Block",
                color='Count',
                text_auto=True
            )
        else:
            block_fig = go.Figure()
            block_fig.update_layout(title="No vendors found")
        
        # Create analysis container
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Total Vendors", className="card-title"),
                            html.H3(f"{total_vendors}", className="card-text text-primary"),
                        ])
                    ]),
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Paid Current Year", className="card-title"),
                            html.H3(f"{paid_count} ({paid_percentage:.1f}%)", className="card-text text-success"),
                        ])
                    ]),
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("With Arrears", className="card-title"),
                            html.H3(f"{arrears_count} ({arrears_percentage:.1f}%)", className="card-text text-danger"),
                        ])
                    ]),
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("With Advance", className="card-title"),
                            html.H3(f"{advance_count} ({advance_percentage:.1f}%)", className="card-text text-info"),
                        ])
                    ]),
                ], width=3),
            ]),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=status_fig),
                ], width=6, className="mt-4"),
                dbc.Col([
                    dcc.Graph(figure=block_fig),
                ], width=6, className="mt-4"),
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Vendor Details", className="mt-4"),
                    dash_table.DataTable(
                        id="vendor-analysis-table",
                        columns=[
                            {"name": "Vendor Name", "id": "name"},
                            {"name": "Shop Number", "id": "shop_number"},
                            {"name": "Block", "id": "block"},
                            {"name": "Registration Date", "id": "registration_date"},
                            {"name": "Paid Current Year", "id": "paid_current_year"},
                            {"name": "Has Arrears", "id": "has_arrears"},
                            {"name": "Has Advance", "id": "has_advance"},
                        ],
                        data=vendor_data,
                        page_size=10,
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "minWidth": "100px", "width": "150px", "maxWidth": "200px",
                            "overflow": "hidden", "textOverflow": "ellipsis",
                        },
                        style_header={
                            "backgroundColor": "rgb(230, 230, 230)",
                            "fontWeight": "bold"
                        },
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{paid_current_year} = "Yes"', 'column_id': 'paid_current_year'},
                                'backgroundColor': 'rgba(40, 167, 69, 0.2)',
                                'color': 'green'
                            },
                            {
                                'if': {'filter_query': '{paid_current_year} = "No"', 'column_id': 'paid_current_year'},
                                'backgroundColor': 'rgba(220, 53, 69, 0.2)',
                                'color': 'red'
                            },
                            {
                                'if': {'filter_query': '{has_arrears} = "Yes"', 'column_id': 'has_arrears'},
                                'backgroundColor': 'rgba(220, 53, 69, 0.2)',
                                'color': 'red'
                            },
                            {
                                'if': {'filter_query': '{has_advance} = "Yes"', 'column_id': 'has_advance'},
                                'backgroundColor': 'rgba(23, 162, 184, 0.2)',
                                'color': 'blue'
                            },
                        ]
                    ),
                ]),
            ]),
        ])
    except Exception as e:
        return html.Div([
            dbc.Alert(f"Error generating analysis: {str(e)}", color="danger"),
        ])

# Callback to generate revenue forecast
@callback(
    Output("forecast-container", "children"),
    [Input("generate-forecast", "n_clicks")],
    [State("forecast-period", "value"),
     State("include-advance", "value")]
)
def generate_forecast(n_clicks, period, include_advance):
    if n_clicks is None:
        return ""
    
    try:
        # Parse forecast period
        months = int(period)
        
        # Get current date and year
        current_date = datetime.now().date()
        current_year = current_date.year
        
        # Get total number of vendors
        total_vendors = get_session().query(func.count(Vendor.id)).scalar() or 0
        
        # Get vendors who have paid for current year
        paid_vendors = get_session().query(func.count(Payment.vendor_id.distinct())).filter(
            Payment.year == current_year,
            Payment.payment_type == 'regular'
        ).scalar() or 0
        
        # Get vendors with advance payments
        advance_payments = {}
        if include_advance:
            advance_query = get_session().query(
                Payment.year,
                func.sum(Payment.amount).label('amount')
            ).filter(
                Payment.payment_type == 'advance',
                Payment.year > current_year
            ).group_by(Payment.year).all()
            
            for year, amount in advance_query:
                advance_payments[year] = amount
        
        # Calculate potential revenue (remaining unpaid vendors for current year)
        remaining_vendors = total_vendors - paid_vendors
        potential_current_year = remaining_vendors * 12000  # ₦12,000 annual fee
        
        # Generate forecast data
        forecast_data = []
        forecast_months = []
        forecast_amounts = []
        
        for i in range(months):
            forecast_date = current_date + timedelta(days=30 * (i + 1))
            forecast_year = forecast_date.year
            
            # Calculate expected revenue for this month
            if forecast_date.month == 1:  # January - assume all vendors pay annual fee
                expected_revenue = total_vendors * 12000
                # Subtract advance payments already made for this year
                if forecast_year in advance_payments:
                    expected_revenue -= advance_payments[forecast_year]
            else:
                # For other months, assume some percentage of remaining vendors pay
                # This is a simplified model - in a real app you'd use historical data
                monthly_factor = 0.1  # Assume 10% of remaining vendors pay each month
                expected_revenue = remaining_vendors * monthly_factor * 12000
            
            forecast_months.append(forecast_date.strftime("%b %Y"))
            forecast_amounts.append(expected_revenue)
            
            forecast_data.append({
                "month": forecast_date.strftime("%B %Y"),
                "expected_revenue": f"₦{expected_revenue:,.2f}",
                "cumulative_revenue": f"₦{sum(forecast_amounts):,.2f}",
            })
        
        # Create forecast chart
        fig = go.Figure()
        
        # Add bar chart for monthly revenue
        fig.add_trace(go.Bar(
            x=forecast_months,
            y=forecast_amounts,
            name='Monthly Revenue',
            marker_color='lightblue'
        ))
        
        # Add line chart for cumulative revenue
        fig.add_trace(go.Scatter(
            x=forecast_months,
            y=[sum(forecast_amounts[:i+1]) for i in range(len(forecast_amounts))],
            name='Cumulative Revenue',
            line=dict(color='darkblue', width=2),
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title=f"Revenue Forecast (Next {months} Months)",
            yaxis_title="Amount (₦)",
            xaxis_title="Month",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Create forecast container
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Total Vendors", className="card-title"),
                            html.H3(f"{total_vendors}", className="card-text text-primary"),
                        ])
                    ]),
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Paid Vendors (Current Year)", className="card-title"),
                            html.H3(f"{paid_vendors}", className="card-text text-success"),
                        ])
                    ]),
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Potential Revenue (Current Year)", className="card-title"),
                            html.H3(f"₦{potential_current_year:,.2f}", className="card-text text-info"),
                        ])
                    ]),
                ], width=4),
            ]),
            
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure=fig),
                ], className="mt-4"),
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H5("Monthly Forecast Details", className="mt-4"),
                    dash_table.DataTable(
                        id="forecast-table",
                        columns=[
                            {"name": "Month", "id": "month"},
                            {"name": "Expected Revenue", "id": "expected_revenue"},
                            {"name": "Cumulative Revenue", "id": "cumulative_revenue"},
                        ],
                        data=forecast_data,
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
        ])
    except Exception as e:
        return html.Div([
            dbc.Alert(f"Error generating forecast: {str(e)}", color="danger"),
        ])

# Callback for exporting report data to CSV
@callback(
    Output("download-report-csv", "data"),
    Input("export-report-csv", "n_clicks"),
    prevent_initial_call=True
)
def export_report_csv(n_clicks):
    # Get all payment data for a comprehensive report
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
    
    return dcc.send_data_frame(df.to_csv, "market_report.csv", index=False)