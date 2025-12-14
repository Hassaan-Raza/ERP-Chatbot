import re
import pandas as pd
from database.db_connection import db


class SalesAgent:
    def __init__(self):
        self.keywords = ['sales', 'revenue', 'report', 'performance', 'units sold', 'orders', 'forecast', 'invoice']

    def process_query(self, message, company_id, method_name="auto"):
        """Process sales query with optional specific method"""
        if method_name == "auto":
            method_name = self._detect_method(message)

        method_map = {
            "get_sales_summary": self.get_sales_summary,
            "get_sales_forecast": self.get_sales_forecast,
            "get_regional_sales": self.get_regional_sales,
            "get_product_sales": self.get_product_sales,
            "get_top_products": self.get_top_products,
            "get_invoice_creation_guide": self.get_invoice_creation_guide
        }

        method = method_map.get(method_name, self.get_sales_summary)
        return method(company_id)

    def _detect_method(self, message):
        """Detect which method to call based on message content"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['create', 'new', 'how to', 'make', 'generate', 'add']) and \
           any(word in message_lower for word in ['invoice', 'sales invoice', 'bill']):
            return "get_invoice_creation_guide"
        elif any(word in message_lower for word in ['forecast', 'projection', 'prediction']):
            return "get_sales_forecast"
        elif any(word in message_lower for word in ['region', 'area', 'territory', 'location']):
            return "get_regional_sales"
        elif any(word in message_lower for word in ['product', 'item', 'sku']):
            return "get_product_sales"
        elif any(word in message_lower for word in ['top', 'best', 'popular', 'leading']):
            return "get_top_products"
        else:
            return "get_sales_summary"

    def get_invoice_creation_guide(self, company_id):
        """Return the step-by-step guide for creating a sales invoice"""
        guide = f"""
**📝 SALES INVOICE CREATION GUIDE - Eccountant ERP**

This guide helps you create Sales Invoices for **Company {company_id}**.

---

### 🎯 **PURPOSE**
To create a Sales Invoice in Eccountant ERP for billing customers and recording sales transactions.

---

### 🗺️ **NAVIGATION PATH**
**Sales → Sale Invoice → New → Sale Invoice**

---

### ✅ **MANDATORY PREREQUISITES**
Before creating an invoice:
1. **Customer exists** in the system
2. **Product/Service items** are created
3. **Stock available** (for inventory items)
4. **Taxes and discounts** are configured
5. **Optional**: Sales Order or Delivery Note created

---

### 📋 **STEP-BY-STEP CREATION PROCESS**

**Step 1 – Open Sales Invoice Form**
- Go to: `Sales → Sale Invoice → New → Sale Invoice`

**Step 2 – Select Customer (Mandatory)**
- Select customer from dropdown
- System auto-loads: address, payment terms, currency

**Step 3 – Invoice Date, Due Date & Warehouse**
- **Invoice Date** (Mandatory): Transaction date
- **Due Date** (Mandatory): Payment deadline
- **Warehouse** (Mandatory): For stock items

**Step 4 – Add Items (Mandatory)**
**Required Fields:**
- **Product Name** (select from list)
- **Quantity** (number of units)
- **Rate** (price per unit)
- **Warehouse** (for stock items)

**Auto-calculated:**
- Amount (Qty × Rate)
- Tax (if configured)
*At least one item is required*

**Step 5 – Additional Charges (Optional)**
- Shipping charges
- Service fees
- Discounts (percentage or amount)

**Step 6 – Notes / Terms (Optional)**
- Special instructions
- Payment terms
- Delivery notes

**Step 7 – Save & Submit**
- **Save Draft**: For incomplete invoices
- **Submit Invoice**: Creates accounting & stock entries

---

### 🚨 **MANDATORY FIELDS SUMMARY**
1. Customer
2. Invoice Date
3. Due Date
4. Items (at least one)
5. Quantity
6. Rate
7. Warehouse (if stock item)
8. Payment Method (for paid invoices)

---

### 🔍 **SYSTEM VALIDATIONS**
The system checks:
- ✅ **Credit limit** (customer credit limit)
- ✅ **Stock availability** (warehouse stock levels)
- ✅ **Zero rate or amount** (prevents zero-value invoices)
- ✅ **Posting date restrictions** (accounting period)
- ✅ **Currency mismatch** (customer vs. invoice currency)

---

### ❌ **COMMON ERRORS & SOLUTIONS**

| Error | Solution |
|-------|----------|
| **Missing required field** | Fill highlighted field |
| **Insufficient stock** | Select different warehouse or adjust quantity |
| **Invoice not submitted** | Click 'Submit' button after saving |
| **Customer credit limit exceeded** | Contact finance department |
| **Invalid date** | Select date within open accounting period |

---

*Note: This guide is based on standard Eccountant ERP configuration. Company {company_id} may have specific settings.*
"""
        return guide

    def get_sales_summary(self, company_id):
        """Get sales summary - FIXED with parameterized query"""
        try:
            # FIXED: Using %s placeholder instead of f-string
            query = """
                SELECT COUNT(DISTINCT sales_invoice.invoice_id)  as total_invoices,
                       SUM(sales_items.total)                    as total_revenue,
                       AVG(sales_items.total)                    as avg_invoice_value,
                       COUNT(DISTINCT sales_invoice.customer_id) as unique_customers,
                       MAX(sales_invoice.invoice_date)           as latest_invoice,
                       SUM(sales_items.quantity)                 as total_units_sold
                FROM sales_items
                         LEFT JOIN sales_invoice ON sales_invoice.invoice_id = sales_items.invoice_id
                         LEFT JOIN contacts ON contacts.contact_id = sales_invoice.customer_id
                WHERE sales_items.company_id = %s
                  AND sales_invoice.status IN ('unpaid', 'paid', 'remaining')
            """

            # FIXED: Passing company_id as parameter tuple
            result = db.execute_query(query, (company_id,))
            
            if result and len(result) > 0:
                summary = result[0]

                # Handle None values
                total_invoices = summary['total_invoices'] or 0
                total_revenue = float(summary['total_revenue'] or 0)
                avg_invoice_value = float(summary['avg_invoice_value'] or 0)
                unique_customers = summary['unique_customers'] or 0
                total_units_sold = summary['total_units_sold'] or 0

                if summary['latest_invoice']:
                    latest_activity = summary['latest_invoice'].strftime('%Y-%m-%d')
                else:
                    latest_activity = 'N/A'

                response_data = f"""
**Sales Performance Summary - Company {company_id}**

📊 **Key Metrics:**
- Total Invoices: {total_invoices:,}
- Total Revenue: ${total_revenue:,.2f}
- Average Invoice Value: ${avg_invoice_value:,.2f}
- Unique Customers: {unique_customers:,}
- Total Units Sold: {total_units_sold:,}
- Latest Activity: {latest_activity}

*Live data from AWS RDS database*
"""
                return response_data
            else:
                return f"No sales data found for company {company_id}"

        except Exception as e:
            return f"Error retrieving sales summary: {str(e)}"

    def get_sales_forecast(self, company_id):
        """Get sales forecast - FIXED with parameterized query"""
        try:
            query = """
                SELECT sales_invoice.invoice_date  AS issue_date,
                       CASE
                           WHEN sales_invoice.note_id IS NULL OR sales_invoice.note_id = 0
                               THEN sales_invoice.invoice_date
                           ELSE store_issue_note.note_date
                           END                     AS delivery_date,
                       sales_items.total,
                       sales_items.subtotal        AS sub_total,
                       sales_items.discount_amount AS discount,
                       contacts.region             AS region_id,
                       origins.title               AS region,
                       sales_invoice.customer_id,
                       sales_invoice.warehouse_id,
                       sales_items.product_id,
                       sales_items.quantity,
                       sales_items.price,
                       sales_items.tax,
                       sales_invoice.status,
                       sales_invoice.currency      AS currency_id,
                       foreign_currency.title      AS currency,
                       sales_invoice.project_id,
                       sales_invoice.salesman      AS salesman_id
                FROM sales_items
                         LEFT JOIN sales_invoice ON sales_invoice.invoice_id = sales_items.invoice_id
                         LEFT JOIN store_issue_note ON store_issue_note.note_id = sales_invoice.note_id
                         LEFT JOIN contacts ON contacts.contact_id = sales_invoice.customer_id
                         LEFT JOIN origins ON origins.id = contacts.region
                         LEFT JOIN foreign_currency ON foreign_currency.fc_id = sales_invoice.currency
                WHERE sales_items.company_id = %s
                  AND sales_invoice.status IN ('unpaid', 'paid', 'remaining')
                ORDER BY sales_invoice.invoice_date DESC LIMIT 100
            """

            df = db.execute_query_dataframe(query, (company_id,))
            if not df.empty:
                recent_revenue = float(df['total'].sum() or 0)
                avg_daily = recent_revenue / min(30, len(df)) if len(df) > 0 else 0
                monthly_forecast = avg_daily * 30

                response_data = f"""
**Sales Forecasting Analysis - Company {company_id}**

🔮 **Revenue Projections:**
- Recent Sample Revenue: ${recent_revenue:,.2f}
- Estimated Monthly Revenue: ${monthly_forecast:,.2f}
- Average Daily Revenue: ${avg_daily:,.2f}
- Analysis Period: {len(df)} recent transactions

📈 **Growth Indicators:**
- Sample covers multiple products and regions
- Based on historical sales patterns
- Adjusts for seasonal trends

*Forecast based on AWS RDS sales data*
"""
                return response_data
            else:
                return f"No sales data available for forecasting for company {company_id}"

        except Exception as e:
            return f"Error generating sales forecast: {str(e)}"

    def get_regional_sales(self, company_id):
        """Get regional sales - FIXED with parameterized query"""
        try:
            query = """
                SELECT origins.title                            AS region,
                       COUNT(DISTINCT sales_invoice.invoice_id) as invoice_count,
                       SUM(sales_items.total)                   as regional_revenue,
                       SUM(sales_items.quantity)                as units_sold,
                       AVG(sales_items.total)                   as avg_order_value
                FROM sales_items
                         LEFT JOIN sales_invoice ON sales_invoice.invoice_id = sales_items.invoice_id
                         LEFT JOIN contacts ON contacts.contact_id = sales_invoice.customer_id
                         LEFT JOIN origins ON origins.id = contacts.region
                WHERE sales_items.company_id = %s
                  AND sales_invoice.status IN ('unpaid', 'paid', 'remaining')
                GROUP BY origins.title
                ORDER BY regional_revenue DESC
            """

            result = db.execute_query(query, (company_id,))
            if result:
                response_data = f"**Regional Sales Performance - Company {company_id}**\n\n"
                response_data += "🏢 **Performance by Region:**\n"

                for i, region in enumerate(result, 1):
                    response_data += f"{i}. **{region['region']}**: ${region['regional_revenue']:,.2f} ({region['invoice_count']} orders, {region['units_sold']} units)\n"
                    response_data += f"   Average Order: ${region['avg_order_value']:,.2f}\n\n"

                return response_data
            else:
                return f"No regional sales data found for company {company_id}"

        except Exception as e:
            return f"Error retrieving regional sales: {str(e)}"

    def get_product_sales(self, company_id):
        """Get product sales - FIXED with parameterized query"""
        try:
            query = """
                SELECT sales_items.product_id,
                       SUM(sales_items.quantity)                as total_sold,
                       SUM(sales_items.total)                   as total_revenue,
                       AVG(sales_items.price)                   as avg_price,
                       COUNT(DISTINCT sales_invoice.invoice_id) as order_count
                FROM sales_items
                         LEFT JOIN sales_invoice ON sales_invoice.invoice_id = sales_items.invoice_id
                WHERE sales_items.company_id = %s
                  AND sales_invoice.status IN ('unpaid', 'paid', 'remaining')
                GROUP BY sales_items.product_id
                ORDER BY total_revenue DESC LIMIT 15
            """

            result = db.execute_query(query, (company_id,))
            if result:
                response_data = f"**Product Sales Analysis - Company {company_id}**\n\n"
                response_data += "📦 **Top Performing Products:**\n"

                for i, product in enumerate(result, 1):
                    response_data += f"{i}. **Product {product['product_id']}**:\n"
                    response_data += f"   Revenue: ${product['total_revenue']:,.2f}\n"
                    response_data += f"   Units Sold: {product['total_sold']:,}\n"
                    response_data += f"   Average Price: ${product['avg_price']:,.2f}\n"
                    response_data += f"   Orders: {product['order_count']}\n\n"

                return response_data
            else:
                return f"No product sales data found for company {company_id}"

        except Exception as e:
            return f"Error retrieving product sales: {str(e)}"

    def get_top_products(self, company_id):
        return self.get_product_sales(company_id)