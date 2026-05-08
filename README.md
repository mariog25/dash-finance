# Finance Dashboard

A modern finance analytics dashboard built with Plotly Dash, designed to provide monthly insights, trend analysis, and transaction-level exploration for personal banking data.

## Project Summary

This project is a Dash web application that connects to a Trino data warehouse and renders interactive finance insights using charts, cards, and tables.

The dashboard includes:
- Monthly overview cards for expense, income, and savings.
- A trend panel for revenue and expense evolution over time.
- Category-level transaction analysis.
- Responsive layout with mobile-friendly controls.
- A sidebar navigation system with desktop and mobile behavior.

## Technology Stack

- Python
- Dash / Plotly
- Pandas
- SQLAlchemy
- Trino (via `trino[sqlalchemy]`)
- dash-ag-grid
- python-dotenv

## Architecture

The core application lives in `finance_app/` and uses a component-based Dash architecture.

### Main folders

- `finance_app/app.py` - Dash application entry point, layout, and sidebar toggle callbacks.
- `finance_app/pages/` - Page modules registered with Dash pages.
- `finance_app/components/` - Reusable UI components for cards, charts, header, sidebar, and panels.
- `finance_app/services/` - Data access layer that runs SQL queries against Trino.
- `finance_app/assets/` - CSS styles for the dashboard.
- `finance_app/utils/` - Utility helpers for formatting values.
- `finance_app/config/` - Theme and styling constants.

### Key pages

- `overview.py` - Main monthly overview page with summary cards and trend panel.
- `transactions.py` - Transaction details and donut category analysis.
- `year_evolution.py` - Yearly evolution and trend comparison.
- `mortgage_revision.py` - Mortgage review page.
- `merchant_revision.py` - Merchant review page.

## Data and Queries

The dashboard reads from a Trino-backed data warehouse using the `services/trino_client.py` engine.

Primary dataset references include:
- `iceberg.gold.fact_bank_transaction`

The query layer provides methods for:
- Available month selection
- Expense, income, and savings insights
- Monthly overview and trend windows
- Category breakdowns and 12-month trends
- Transaction-level details by category

## UI Components

The app uses reusable components to structure the interface:
- `header.py` - Title, subtitle, and primary page header.
- `sidebar.py` - Collapsible navigation sidebar with desktop and mobile variants.
- `category_donut_card.py` - Donut chart cards for transaction categories.
- `expense_insight_card.py`, `income_insight_card.py`, `savings_activity_card.py` - Summary cards with sparkline trend graphics.
- `monthly_trend_panel.py` - Monthly trend chart panel supporting desktop and mobile layouts.

## Styling

Styles are defined in `finance_app/assets/styles.css`.

The CSS handles:
- Layout structure and card spacing
- Sidebar transformations and responsive mobile behavior
- Form control styling for filters
- Graph container positioning and consistent spacing
- Card height and chart integration

## Installation

1. Install Python dependencies:

```bash
pip install -r finance_app/requirements.txt
```

2. Configure Trino connection settings in environment variables or a `.env` file.

3. Run the application:

```bash
python finance_app/app.py
```

4. Open the dashboard at `http://localhost:8050`.

## Environment Variables

The app supports the following environment variables:
- `DASH_HOST` - Host address for Dash (default: `0.0.0.0`).
- `DASH_PORT` - Port for Dash (default: `8050`).
- `DASH_DEBUG` - Debug mode flag (default: `true`).

## Notes

- The app is intended for internal analytics and assumes access to a Trino data source.
- The project is structured to make UI components reusable and data queries centralized.
- Styling is kept in a single CSS file to ensure consistent card and grid behavior across screen sizes.
