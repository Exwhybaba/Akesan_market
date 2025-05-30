# Oyo East Local Government Market Management System

A comprehensive digital solution for managing market vendors, fee collections, and financial reporting for Oyo East Local Government.

## Features

### Vendor Management
- Add, edit, and remove vendor records
- Track vendor details (name, shop number, block, registration date)
- Search and filter vendors by name, shop number, or block
- Prevent duplicate shop/block combinations

### Financial Operations
- Process different payment types:
  - Regular payments (current year)
  - Arrears payments (past years)
  - Advance payments (future years)
- Generate unique receipts with printable format
- Daily closing with detailed summaries
- Re-open/lock daily closings as needed

### Dashboard & Analytics
- Real-time metrics on collections, arrears, and advance payments
- Visual charts for payment trends and vendor status
- Block-wise distribution of vendors
- Revenue forecasting

### Reporting & Export
- Generate payment summary reports with date filtering
- Vendor analysis reports with payment status
- Export data to CSV format for further analysis
- Historical payment tracking

## Technical Stack

- **Backend**: Python with Dash framework
- **Database**: SQLite (via SQLAlchemy ORM)
- **Frontend**: Dash Bootstrap Components for responsive UI
- **Visualization**: Plotly for interactive charts
- **Data Handling**: Pandas for data manipulation

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/oyo-market-management.git
cd oyo-market-management
```

2. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run the application:
```
python app.py
```

5. Open your browser and navigate to:
```
http://127.0.0.1:8050/
```

## Project Structure

```
oyo-market-management/
├── app.py                  # Main application file
├── models.py               # Database models
├── assets/                 # Static assets (CSS, images)
│   └── logo_new.jpeg       # Logo file
├── pages/                  # Application pages
│   ├── dashboard.py        # Dashboard with metrics and charts
│   ├── vendors.py          # Vendor management
│   ├── payments.py         # Payment processing
│   ├── reports.py          # Reports and analytics
│   └── daily_closing.py    # Daily closing operations
└── market_management.db    # SQLite database (created on first run)
```

## User Roles

### Market Administrators
- Add and manage vendor information
- Process payments and generate receipts
- Perform daily closings

### Finance Officers
- Monitor payment performance
- Generate financial reports
- Track arrears and advance payments

### Auditors
- View payment history
- Export records for audit purposes
- Analyze revenue trends

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please contact [seyeoyelayo@gmail.com](mailto: seyeoyelayo@gmail.com). 
#   M a r k e t _ M a n a g e m e n t  
 #   A k e s a _ M a r k e t _ M a n a g e m e n t  
 