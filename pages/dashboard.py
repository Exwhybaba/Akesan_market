import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import func, extract
from datetime import datetime, date, timedelta
from app import Vendor, Payment, Receipt, DailyClosing, get_db
import dash_table

# Get db reference using the function from app.py
def get_session():
    return get_db()

# Dashboard layout
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fas fa-tachometer-alt fa-2x text-primary float-start me-3 mt-2"),
                html.Div([
                    html.H2("Market Management Dashboard", className="text-primary mb-1"),
                    html.P("Overview of market vendors, collections, and payment statistics", 
                           className="text-muted"),
                ])
            ]),
            html.Hr(),
        ], width=12)
    ], className="mb-4"),
    
    # Filter Section
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Dashboard Filters", className="bg-primary text-white"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Date Range:", className="fw-bold mb-2"),
                            dcc.DatePickerRange(
                                id="date-filter",
                                start_date=(datetime.now() - timedelta(days=30)).date(),
                                end_date=datetime.now().date(),
                                display_format="YYYY-MM-DD",
                                className="w-100"
                            ),
                        ], width=12, md=4),
                        dbc.Col([
                            html.Label("Payment Type:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="payment-type-filter",
                                options=[
                                    {"label": "All", "value": "all"},
                                    {"label": "Regular", "value": "regular"},
                                    {"label": "Arrears", "value": "arrears"},
                                    {"label": "Advance", "value": "advance"},
                                ],
                                value="all",
                                className="w-100"
                            ),
                        ], width=12, md=4),
                        dbc.Col([
                            html.Label("Block:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="block-filter",
                                options=[
                                    {"label": "All", "value": "all"},
                                ],
                                value="all",
                                className="w-100"
                            ),
                        ], width=12, md=4),
                    ]),
                ])
            ], className="mb-4 shadow-sm"),
        ], width=12),
    ], className="mb-4"),
    
    # Summary Stats Cards
    dbc.Row([
        # Total Vendors Card
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-users fa-2x text-info float-start me-3"),
                        html.Div([
                            html.H6("Total Vendors", className="card-subtitle text-muted"),
                            html.H3(id="total-vendors", className="card-title mb-0 fw-bold"),
                        ], className="ms-5")
                    ])
                ], className="p-4"),
                dbc.CardFooter([
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"),
                        "Total registered market vendors"
                    ], className="text-muted")
                ], className="bg-transparent")
            ], className="mb-4 h-100 shadow-lg"),
        ], width=12, lg=3, className="mb-4"),
        
        # Total Collections Card
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-money-bill-wave fa-2x text-success float-start me-3"),
                        html.Div([
                            html.H6("Total Collections", className="card-subtitle text-muted"),
                            html.H3(id="total-collections", className="card-title mb-0 fw-bold"),
                        ], className="ms-5")
                    ])
                ], className="p-4"),
                dbc.CardFooter([
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"),
                        "Total revenue collected"
                    ], className="text-muted")
                ], className="bg-transparent")
            ], className="mb-4 h-100 shadow-lg"),
        ], width=12, lg=3, className="mb-4"),
        
        # Outstanding Arrears Card
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-exclamation-circle fa-2x text-warning float-start me-3"),
                        html.Div([
                            html.H6("Arrears Payments", className="card-subtitle text-muted"),
                            html.H3(id="outstanding-arrears", className="card-title mb-0 fw-bold"),
                        ], className="ms-5")
                    ])
                ], className="p-4"),
                dbc.CardFooter([
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"),
                        "Total arrears payments (paid and outstanding)"
                    ], className="text-muted")
                ], className="bg-transparent")
            ], className="mb-4 h-100 shadow-lg"),
        ], width=12, lg=3, className="mb-4"),
        
        # Advance Payments Card
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-calendar-plus fa-2x text-info float-start me-3"),
                        html.Div([
                            html.H6("Advance Payments", className="card-subtitle text-muted"),
                            html.H3(id="advance-payments", className="card-title mb-0 fw-bold"),
                        ], className="ms-5")
                    ])
                ], className="p-4"),
                dbc.CardFooter([
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"),
                        "Prepaid fees for future periods"
                    ], className="text-muted")
                ], className="bg-transparent")
            ], className="mb-4 h-100 shadow-lg"),
        ], width=12, lg=3, className="mb-4"),
    ], className="mb-4"),
    
    # Chart Row
    dbc.Row([
        # Payment Trends Chart
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-chart-line me-2 text-info"),
                        html.H5("Payment Trends", className="d-inline card-title mb-0"),
                    ]),
                    html.Small("Last 12 Months", className="text-muted")
                ], className="pb-3"),
                dbc.CardBody([
                    dcc.Graph(id="payment-trends-chart"),
                ], className="pt-3"),
            ], className="mb-4 h-100 shadow-lg"),
        ], width=12, lg=6, className="mb-4"),
        
        # Payment Status Breakdown
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-chart-pie me-2 text-info"),
                        html.H5("Vendor Payment Status", className="d-inline card-title mb-0"),
                    ]),
                    html.Small("Distribution by Type", className="text-muted")
                ], className="pb-3"),
                dbc.CardBody([
                    dcc.Graph(id="payment-status-chart"),
                ], className="pt-3"),
            ], className="mb-4 h-100 shadow-lg"),
        ], width=12, lg=6, className="mb-4"),
    ], className="mb-4"),
    
    # Additional Chart Row
    dbc.Row([
        # Advance Payment Distribution Chart
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.I(className="fas fa-chart-bar me-2 text-info"),
                        html.H5("Advance Payment Distribution", className="d-inline card-title mb-0"),
                    ]),
                    html.Small("By Future Year", className="text-muted")
                ], className="pb-3"),
                dbc.CardBody([
                    dcc.Graph(id="advance-payment-chart"),
                ], className="pt-3"),
            ], className="mb-5 shadow-lg"),
        ], width=12, className="mb-4"),
    ], className="mb-4"),
    
    # Refresh interval
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # in milliseconds (1 minute)
        n_intervals=0,
        disabled=True
    ),
    
    # Hidden components for compatibility with other pages
    html.Div([
        # Hidden vendor search from vendor page
        dbc.Input(id="vendor-search", type="text", value=""),
        
        # Hidden vendor table from vendor page
        dash_table.DataTable(
            id="vendor-table",
            data=[],
            columns=[
                {"name": "ID", "id": "id"},
                {"name": "Name", "id": "name"},
                {"name": "Shop Number", "id": "shop_number"},
                {"name": "Block", "id": "block"},
                {"name": "Registration Date", "id": "registration_date"}
            ]
        ),
        
        # Hidden vendor data store
        dcc.Store(id="vendors-data", data=[]),
        
        # Hidden refresh trigger
        dcc.Store(id="refresh-trigger", data=0),
        
        # Hidden elements for vendor management
        html.Div(id="add-vendor-alert"),
        html.Div(id="edit-vendor-alert"),
        html.Div(id="delete-status-alert"),
    ], style={"display": "none"}),
])

# Callback for updating dashboard metrics and charts
@callback(
    [Output("total-vendors", "children"),
     Output("total-collections", "children"),
     Output("outstanding-arrears", "children"),
     Output("advance-payments", "children"),
     Output("payment-trends-chart", "figure"),
     Output("payment-status-chart", "figure"),
     Output("advance-payment-chart", "figure"),
     Output("block-filter", "options", allow_duplicate=True)],
    [Input("interval-component", "n_intervals"),
     Input("date-filter", "start_date"),
     Input("date-filter", "end_date"),
     Input("payment-type-filter", "value"),
     Input("block-filter", "value"),
     Input("refresh-payment-history", "data")],
    prevent_initial_call='initial_duplicate'
)
def update_dashboard(n, start_date, end_date, payment_type, selected_block, refresh_data):
    try:
        # Get blocks for dropdown options
        blocks = get_session().query(Vendor.block).distinct().all()
        block_options = [{"label": "All", "value": "all"}] + [{"label": block[0], "value": block[0]} for block in blocks]
        
        # Apply date filter if provided
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            start_date = (datetime.now() - timedelta(days=30)).date()
            end_date = datetime.now().date()
        
        # Get total number of vendors (apply block filter if selected)
        if selected_block and selected_block != "all":
            total_vendors = get_session().query(func.count(Vendor.id)).filter(
                Vendor.block == selected_block
            ).scalar() or 0
        else:
            total_vendors = get_session().query(func.count(Vendor.id)).scalar() or 0
        
        # Get total collections (all payments made)
        query = get_session().query(func.sum(Payment.amount)).filter(
            Payment.date >= start_date,
            Payment.date <= end_date
        )
        
        # Apply payment type filter if not "all"
        if payment_type and payment_type != "all":
            query = query.filter(Payment.payment_type == payment_type)
        
        # Apply block filter if selected
        if selected_block and selected_block != "all":
            query = query.join(Vendor).filter(Vendor.block == selected_block)
        
        total_collections = query.scalar() or 0
        
        # Calculate current year
        current_year = datetime.now().year
        
        # Calculate paid arrears for previous years
        arrears_query = get_session().query(func.sum(Payment.amount)).filter(
            Payment.payment_type == 'arrears',
            Payment.date >= start_date,
            Payment.date <= end_date
        )
        
        # Apply block filter if selected
        if selected_block and selected_block != "all":
            arrears_query = arrears_query.join(Vendor).filter(Vendor.block == selected_block)
        
        paid_arrears = arrears_query.scalar() or 0
        
        # Estimate total potential arrears (vendors * annual fee * years since establishment)
        # This is simplified and should be adjusted based on your business logic
        # In a real application, you would track this per vendor based on their registration date
        annual_fee = 12000  # ₦12,000 annual fee per vendor
        
        # Get all vendors with block filter if applicable
        vendor_query = get_session().query(Vendor)
        if selected_block and selected_block != "all":
            vendor_query = vendor_query.filter(Vendor.block == selected_block)
        
        # Calculate total potential arrears based on vendor registration dates
        total_potential_arrears = 0
        for vendor in vendor_query.all():
            reg_year = vendor.registration_date.year
            years_active = current_year - reg_year
            if years_active > 0:
                total_potential_arrears += annual_fee * years_active
        
        # Calculate outstanding arrears by subtracting paid arrears from total potential
        outstanding_arrears = total_potential_arrears - paid_arrears
        if outstanding_arrears < 0:
            outstanding_arrears = 0  # Ensure we don't show negative arrears
        
        # Get total advance payments
        advance_query = get_session().query(func.sum(Payment.amount)).filter(
            Payment.payment_type == 'advance',
            Payment.date >= start_date,
            Payment.date <= end_date
        )
        
        # Apply block filter if selected
        if selected_block and selected_block != "all":
            advance_query = advance_query.join(Vendor).filter(Vendor.block == selected_block)
        
        advance_payments = advance_query.scalar() or 0
        
        # Create payment trends chart (for selected date range)
        payment_trends = get_session().query(
            func.strftime('%Y-%m-%d', Payment.date).label('date'),
            func.sum(Payment.amount).label('amount')
        ).filter(
            Payment.date >= start_date,
            Payment.date <= end_date
        )
        
        # Apply payment type filter if not "all"
        if payment_type and payment_type != "all":
            payment_trends = payment_trends.filter(Payment.payment_type == payment_type)
        
        # Apply block filter if selected
        if selected_block and selected_block != "all":
            payment_trends = payment_trends.join(Vendor).filter(Vendor.block == selected_block)
        
        # Group by date and get results
        payment_trends = payment_trends.group_by(func.strftime('%Y-%m-%d', Payment.date)).all()
        
        # Convert to DataFrame for Plotly
        df_trends = pd.DataFrame(payment_trends, columns=['date', 'amount'])
        
        # Create a complete range of dates in the selected period
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        all_dates_df = pd.DataFrame({'date': all_dates.strftime('%Y-%m-%d')})
        
        # Merge with actual data to fill in missing dates
        df_trends = pd.merge(all_dates_df, df_trends, on='date', how='left').fillna(0)
        
        # Create trend chart
        trend_fig = px.bar(
            df_trends, 
            x='date', 
            y='amount',
            title="Payment Collections",
            labels={'date': 'Date', 'amount': 'Amount (₦)'},
            text_auto='.2s',
            color_discrete_sequence=['#2c88d9']  # Blue theme color
        )
        trend_fig.update_layout(
            xaxis_tickangle=-45,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis_gridcolor='rgba(0, 0, 0, 0.1)',
            xaxis_gridcolor='rgba(0, 0, 0, 0.1)',
            font=dict(color='#333'),
            margin=dict(l=40, r=40, t=60, b=80),
            height=280  # Reduced height from 350 to 280
        )
        
        # Create payment status chart
        status_query = get_session().query(
            Payment.payment_type,
            func.count(Payment.id).label('count')
        ).filter(
            Payment.date >= start_date,
            Payment.date <= end_date
        )
        
        # Apply block filter if selected
        if selected_block and selected_block != "all":
            status_query = status_query.join(Vendor).filter(Vendor.block == selected_block)
        
        status_query = status_query.group_by(Payment.payment_type).all()
        
        # Convert to a proper format for the chart
        status_dict = {status: 0 for status in ['regular', 'arrears', 'advance']}
        for payment_type, count in status_query:
            if payment_type in status_dict:
                status_dict[payment_type] = count
        
        status_data = {
            'Status': ['Regular', 'Arrears', 'Advance'],
            'Count': [
                status_dict['regular'],
                status_dict['arrears'],
                status_dict['advance']
            ]
        }
        df_status = pd.DataFrame(status_data)
        
        status_fig = px.pie(
            df_status, 
            names='Status', 
            values='Count',
            color='Status',
            color_discrete_map={
                'Regular': '#28a745',  # Success green
                'Arrears': '#ffc107',  # Warning yellow
                'Advance': '#2c88d9'   # Info blue
            },
            hole=0.4
        )
        status_fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5,
                font=dict(color='#333')
            ),
            font=dict(color='#333'),
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=60, b=100),
            height=280  # Reduced height from 350 to 280
        )
        
        # Create advance payment distribution chart
        advance_data = get_session().query(
            Payment.year,
            func.sum(Payment.amount).label('amount')
        ).filter(
            Payment.payment_type == 'advance',
            Payment.year > current_year,
            Payment.date >= start_date,
            Payment.date <= end_date
        )
        
        # Apply block filter if selected
        if selected_block and selected_block != "all":
            advance_data = advance_data.join(Vendor).filter(Vendor.block == selected_block)
        
        advance_data = advance_data.group_by(Payment.year).all()
        
        df_advance = pd.DataFrame(advance_data, columns=['year', 'amount'])
        
        advance_fig = px.bar(
            df_advance,
            x='year',
            y='amount',
            title='Advance Payments by Future Year',
            labels={'year': 'Year', 'amount': 'Amount (₦)'},
            text_auto=True,
            color_discrete_sequence=['#2c88d9']  # Blue color
        )
        advance_fig.update_layout(
            xaxis=dict(
                tickmode='linear',
                dtick=1
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis_gridcolor='rgba(0, 0, 0, 0.1)',
            xaxis_gridcolor='rgba(0, 0, 0, 0.1)',
            font=dict(color='#333'),
            margin=dict(l=40, r=40, t=60, b=60),
            height=280  # Reduced height from 350 to 280
        )
        
        # Calculate total arrears payments (paid and outstanding)
        total_arrears = paid_arrears + outstanding_arrears
        total_arrears_formatted = f"₦{total_arrears:,.2f}"
        
        return (
            f"{total_vendors:,}",
            f"₦{total_collections:,.2f}",
            total_arrears_formatted,
            f"₦{advance_payments:,.2f}",
            trend_fig,
            status_fig,
            advance_fig,
            block_options
        )
    except Exception as e:
        # Log the error for debugging
        import traceback
        traceback.print_exc()
        # Return error indicators to the output components
        return (
            f"Error: {e}",
            f"Error: {e}",
            f"Error: {e}",
            f"Error: {e}",
            go.Figure(), # Return an empty figure
            go.Figure(), # Return an empty figure
            go.Figure(), # Return an empty figure
            [], # Return empty options for the dropdown
        ) 