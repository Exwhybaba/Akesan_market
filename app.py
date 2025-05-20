import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date, Text, Boolean, func, extract, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import importlib

# Initialize the Dash app with Bootstrap
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.FLATLY],  # Changed from SUPERHERO to FLATLY for a blue and white theme
                suppress_callback_exceptions=True,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                assets_folder="assets")

# Custom CSS for better styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Oyo East LG Market Management System</title>
        {%favicon%}
        {%css%}
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Poppins', sans-serif;
                background-color: #f8f9fa;
                color: #333;
            }
            .navbar-brand img {
                height: 40px;
                margin-right: 10px;
            }
            .card {
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
                transition: all 0.3s ease;
                border-radius: 0.5rem;
                margin-bottom: 2rem;
                border: none !important;
                background-color: #ffffff;
            }
            .card:hover {
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15) !important;
                transform: translateY(-5px);
            }
            .card-header {
                background-color: rgba(240, 240, 240, 0.5);
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                padding: 1.25rem 1.5rem;
                font-weight: 600;
            }
            .card-body {
                padding: 1.5rem;
            }
            .card-footer {
                padding: 1rem 1.5rem;
                background-color: rgba(240, 240, 240, 0.5);
                border-top: 1px solid rgba(0, 0, 0, 0.05);
            }
            .nav-link {
                font-weight: 500;
                padding: 0.7rem 1.2rem;
                margin: 0 0.3rem;
            }
            .nav-link:hover {
                background-color: rgba(2, 117, 216, 0.1);
                border-radius: 4px;
            }
            .nav-link.active {
                background-color: rgba(2, 117, 216, 0.2);
                border-radius: 4px;
            }
            .btn {
                font-weight: 500;
                border-radius: 0.25rem;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                padding: 0.5rem 1.25rem;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
            }
            table {
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                border-radius: 0.5rem;
                margin-bottom: 2rem;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
                font-weight: 600;
                background-color: rgba(2, 117, 216, 0.1);
                padding: 1rem;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
                font-size: 0.875rem;
                padding: 0.8rem 1rem;
            }
            footer {
                border-top: 1px solid rgba(0, 0, 0, 0.1);
                padding-top: 2rem;
                margin-top: 3rem;
            }
            .js-plotly-plot .plotly .modebar {
                margin-top: 10px;
            }
            .container-fluid {
                padding: 2rem;
            }
            .row {
                margin-bottom: 1.5rem;
            }
            /* Graph spacing fixes */
            .js-plotly-plot {
                padding: 1rem 0;
            }
            /* Custom scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
            }
            ::-webkit-scrollbar-track {
                background: #f8f9fa;
            }
            ::-webkit-scrollbar-thumb {
                background: #2c88d9;
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #1d6fb8;
            }
            /* Filter dropdown styles */
            .Select {
                width: 100% !important;
                min-width: 200px;
            }
            .Select-control {
                border-radius: 4px;
                border: 1px solid #e9ecef;
                padding: 6px;
            }
            .Select.is-focused > .Select-control {
                border-color: #2c88d9;
                box-shadow: 0 0 0 0.2rem rgba(2, 117, 216, 0.25);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Initialize server
server = app.server

# Set up SQLAlchemy with SQLite
DATABASE_URL = 'sqlite:///market_management.db'
engine = create_engine(DATABASE_URL)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# Define models using SQLAlchemy
class Vendor(Base):
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    shop_number = Column(String(50), nullable=False)
    block = Column(String(50), nullable=False)
    registration_date = Column(Date, default=datetime.utcnow().date)
    
    # Relationships
    payments = relationship('Payment', backref='vendor', lazy='dynamic')
    receipts = relationship('Receipt', backref='vendor', lazy='dynamic')
    
    # Constraint to prevent duplicate shop+block combinations
    __table_args__ = (UniqueConstraint('shop_number', 'block', name='unique_shop_block'),)
    
    def __repr__(self):
        return f'<Vendor {self.name} - Shop {self.shop_number}, Block {self.block}>'

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)
    amount = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)
    payment_type = Column(String(20), nullable=False)  # regular, arrears, advance
    date = Column(Date, default=datetime.utcnow().date)
    time = Column(String(8), default=datetime.utcnow().strftime('%H:%M:%S'))  # Store as HH:MM:SS
    daily_closing_id = Column(Integer, ForeignKey('daily_closings.id'), nullable=True)
    
    def __repr__(self):
        return f'<Payment ₦{self.amount} - Vendor ID: {self.vendor_id}, Type: {self.payment_type}>'

class Receipt(Base):
    __tablename__ = 'receipts'
    
    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)
    issue_date = Column(Date, default=datetime.utcnow().date)
    amount = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)
    receipt_number = Column(String(50), unique=True, nullable=False)
    payment_id = Column(Integer, ForeignKey('payments.id'), nullable=False)
    
    # Create a relationship back to payment
    payment = relationship('Payment', backref='receipt', uselist=False)
    
    def __repr__(self):
        return f'<Receipt #{self.receipt_number} - ₦{self.amount}>'

class DailyClosing(Base):
    __tablename__ = 'daily_closings'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.utcnow().date, unique=True)
    total_amount = Column(Float, nullable=False)
    regular_amount = Column(Float, default=0.0)
    arrears_amount = Column(Float, default=0.0)
    advance_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    is_closed = Column(Boolean, default=True)
    
    # Relationships
    payments = relationship('Payment', backref='daily_closing', lazy='dynamic')
    
    def __repr__(self):
        return f'<Daily Closing {self.date} - ₦{self.total_amount}>'

# Create database tables
Base.metadata.create_all(bind=engine)
print("Database tables created successfully.")

# Function to get DB session - used by page modules
def get_db():
    return db_session

# Clean up database session when app shuts down
@server.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# App layout
app.layout = html.Div([
    dbc.Navbar(
        dbc.Container([
            # Logo and brand
            html.A(
                dbc.Row([
                    dbc.Col(html.Img(src="/assets/logo_new.jpeg", height="40px", style={"border-radius": "5px"})),
                    dbc.Col(dbc.NavbarBrand("Oyo East LG Market Management System", className="ms-3 fw-bold")),
                ], align="center", className="g-0"),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            # Navigation links
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink([html.I(className="fas fa-chart-line me-2"), "Dashboard"], href="/dashboard", active="exact")),
                    dbc.NavItem(dbc.NavLink([html.I(className="fas fa-store me-2"), "Vendors"], href="/vendors", active="exact")),
                    dbc.NavItem(dbc.NavLink([html.I(className="fas fa-money-bill-wave me-2"), "Payments"], href="/payments", active="exact")),
                    dbc.NavItem(dbc.NavLink([html.I(className="fas fa-file-alt me-2"), "Reports"], href="/reports", active="exact")),
                    dbc.NavItem(dbc.NavLink([html.I(className="fas fa-cash-register me-2"), "Daily Closing"], href="/daily-closing", active="exact")),
                ], 
                className="ms-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
            ),
        ]),
        color="primary",
        dark=True,
        className="mb-5 shadow-lg",
        sticky="top",
    ),
    
    # Content will be rendered in this container
    dbc.Container([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content', className="py-4")
    ], fluid=True, className="pt-3 px-4"),
    
    # Footer
    html.Footer(
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            html.P([
                                html.I(className="fas fa-chart-bar me-2 text-info"),
                                "Oyo East Local Government Market Management System"
                            ], className="mb-1"),
                            html.P("Efficient tracking of market vendors and payments", className="text-muted small")
                        ], width={"size": 8}),
                        dbc.Col([
                            html.P("© 2024 All Rights Reserved", className="text-end text-muted small mt-3")
                        ], width={"size": 4})
                    ])
                ])
            ])
        ]),
        className="mt-5 pt-4 pb-4 bg-dark"
    )
])

# Toggle navbar
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# Page routing
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/dashboard' or pathname == '/':
        # Import and register the dashboard page
        import pages.dashboard
        # Ensure the module is reloaded to register callbacks
        importlib.reload(pages.dashboard)
        return pages.dashboard.layout
    elif pathname == '/vendors':
        # Import and register the vendors page
        import pages.vendors
        # Ensure the module is reloaded to register callbacks
        importlib.reload(pages.vendors)
        return pages.vendors.layout
    elif pathname == '/payments':
        # Import and register the payments page
        import pages.payments
        # Ensure the module is reloaded to register callbacks
        importlib.reload(pages.payments)
        return pages.payments.layout
    elif pathname == '/reports':
        # Import and register the reports page
        import pages.reports
        # Ensure the module is reloaded to register callbacks
        importlib.reload(pages.reports)
        return pages.reports.layout
    elif pathname == '/daily-closing':
        # Import and register the daily_closing page
        import pages.daily_closing
        # Ensure the module is reloaded to register callbacks
        importlib.reload(pages.daily_closing)
        return pages.daily_closing.layout
    else:
        # 404 page
        return dbc.Container([
            html.H1("404: Page not found", className="text-center mt-5"),
            html.Hr(),
            html.P("The page you requested was not found.", className="text-center")
        ])

if __name__ == '__main__':
    # Ensure directory structure exists
    os.makedirs('pages', exist_ok=True)
    
    # Pre-register all page modules to ensure callbacks are registered
    print("Pre-registering page modules...")
    try:
        import pages.dashboard
        import pages.vendors
        import pages.payments
        import pages.reports
        import pages.daily_closing
        print("All page modules registered successfully.")
    except Exception as e:
        print(f"Error registering modules: {str(e)}")
    
    # Run the app
    app.run_server(debug=True) 