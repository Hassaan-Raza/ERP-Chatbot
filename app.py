import streamlit as st
import pandas as pd
from agents.sales_agent import SalesAgent
from agents.inventory_agent import InventoryAgent
from agents.cashflow_agent import CashFlowAgent
from database.db_connection import db
from database.schema_discovery import SchemaDiscovery
import plotly.express as px
import time
import io
from datetime import datetime

# Initialize agents
sales_agent = SalesAgent()
inventory_agent = InventoryAgent()
cashflow_agent = CashFlowAgent()

# Page configuration
st.set_page_config(
    page_title="ERP AI Chatbot - AWS RDS",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .aws-badge {
        background-color: #FF9900;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        margin-left: 10px;
    }
    .company-badge {
        background-color: #1f77b4;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: bold;
        margin-left: 10px;
    }
</style>
""", unsafe_allow_html=True)


def test_database_connection():
    """Test database connection and return status"""
    try:
        result = db.execute_query("SELECT 1 as test")
        if result and len(result) > 0:
            return True, "AWS RDS Connected ✓"
        return False, "No data returned"
    except Exception as e:
        return False, f"Connection Error"


def get_available_companies():
    """Get list of verified companies with rich data - DEMO OPTIMIZED"""
    # PRE-VERIFIED COMPANIES - These are known to have rich data for demos
    verified_companies = ["922", "1336", "1387", "1415"]
    
    try:
        # Still try to get dynamic list, but fall back to verified list
        query = """
            SELECT DISTINCT company_id
            FROM sales_items
            WHERE company_id IS NOT NULL
            UNION
            SELECT DISTINCT company_id
            FROM voucher_items
            WHERE company_id IS NOT NULL
            ORDER BY company_id LIMIT 10
        """
        result = db.execute_query(query)
        if result and len(result) > 0:
            dynamic_companies = [str(company['company_id']) for company in result]
            # Merge verified with dynamic, keeping verified at top
            all_companies = verified_companies + [c for c in dynamic_companies if c not in verified_companies]
            return all_companies[:10]
    except Exception as e:
        print(f"Error getting companies: {e}")
    
    # Fallback to verified companies
    return verified_companies


def generate_combined_report(company_id):
    """Generate combined data from all three agents for download"""
    try:
        sales_data = sales_agent.get_sales_summary(company_id)
        cashflow_data = cashflow_agent.get_cashflow_summary(company_id)
        inventory_data = inventory_agent.get_inventory_summary(company_id)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        csv_data = f"ERP AI Chatbot - Company {company_id} Report\n"
        csv_data += f"Generated: {timestamp}\n"
        csv_data += f"Data Source: AWS RDS MySQL\n\n"

        csv_data += "SALES METRICS\n"
        csv_data += "Metric,Value\n"
        if "Total Invoices:" in sales_data:
            csv_data += "Total Invoices," + sales_data.split("Total Invoices:")[1].split("\n")[0].strip().replace(",", "") + "\n"
        if "Total Revenue:" in sales_data:
            csv_data += "Total Revenue," + sales_data.split("Total Revenue:")[1].split("\n")[0].strip().replace("$", "").replace(",", "") + "\n"

        csv_data += "\nCASH FLOW METRICS\n"
        csv_data += "Metric,Value\n"
        if "Total Transactions:" in cashflow_data:
            csv_data += "Total Transactions," + cashflow_data.split("Total Transactions:")[1].split("\n")[0].strip().replace(",", "") + "\n"
        if "Total Cash Inflows:" in cashflow_data:
            csv_data += "Total Cash Inflows," + cashflow_data.split("Total Cash Inflows:")[1].split("\n")[0].strip().replace("$", "").replace(",", "") + "\n"

        csv_data += "\nINVENTORY METRICS\n"
        csv_data += "Metric,Value\n"
        if "Total Products:" in inventory_data:
            csv_data += "Total Products," + inventory_data.split("Total Products:")[1].split("\n")[0].strip().replace(",", "") + "\n"

        return csv_data
    except Exception as e:
        print(f"Error generating report: {e}")
        return f"Error generating report: {str(e)}"


def main():
    st.markdown('<div class="main-header">🤖 ERP AI Chatbot <span class="aws-badge">AWS RDS</span></div>',
                unsafe_allow_html=True)

    # DEMO MODE TOGGLE - NEW FEATURE FOR STABLE PRESENTATIONS
    demo_mode = st.sidebar.checkbox("🎬 Demo Mode (Stable)", value=False, 
                                     help="Optimized for presentations - adds smooth loading")
    
    if demo_mode:
        st.sidebar.info("📍 Demo mode active - Optimized data flow")

    # Company selection
    st.sidebar.title("🏢 Company Selection")
    available_companies = get_available_companies()
    
    # Always default to first company (922 - most reliable)
    selected_company = st.sidebar.selectbox(
        "Select Company ID",
        available_companies,
        index=0,
        help="Pre-selected companies verified with rich data"
    )

    # Validate and set company context
    try:
        db.set_company_id(selected_company)
    except ValueError as e:
        st.sidebar.error(f"Invalid company ID: {e}")
        st.stop()

    # Connection status
    st.sidebar.title("🔗 Connection Status")
    db_connected, db_status = test_database_connection()
    db_icon = "✅" if db_connected else "❌"
    st.sidebar.markdown(f"{db_icon} **Database**: {db_status}")

    if db_connected:
        st.sidebar.success("🚀 Live AWS RDS Data Available!")
    else:
        st.sidebar.error("⚠️ Database Connection Issue")
        if not demo_mode:
            st.sidebar.warning("💡 Try enabling Demo Mode")

    # Download Section
    st.sidebar.markdown("---")
    st.sidebar.title("📥 Export Reports")
    csv_data = generate_combined_report(selected_company)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.download_button(
            label="📊 CSV",
            data=csv_data,
            file_name=f"company_{selected_company}_report.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col2:
        st.button("📄 PDF", use_container_width=True, help="PDF export (install reportlab)")

    # Quick Stats Preview
    st.sidebar.markdown("---")
    st.sidebar.title("📈 Quick Preview")

    with st.sidebar:
        with st.spinner("Loading metrics..."):
            sales_result = sales_agent.get_sales_summary(selected_company)
            cashflow_result = cashflow_agent.get_cashflow_summary(selected_company)

    if "Total Invoices:" in sales_result:
        invoices = sales_result.split("Total Invoices:")[1].split("\n")[0].strip()
        st.sidebar.metric("📊 Invoices", invoices)
    if "Total Revenue:" in sales_result:
        revenue = sales_result.split("Total Revenue:")[1].split("\n")[0].strip()
        st.sidebar.metric("💰 Revenue", revenue)
    if "Total Transactions:" in cashflow_result:
        transactions = cashflow_result.split("Total Transactions:")[1].split("\n")[0].strip()
        st.sidebar.metric("💳 Transactions", transactions)

    # Chat Interface
    chat_interface(selected_company, demo_mode)


def chat_interface(company_id, demo_mode=False):
    st.markdown(f"### 💬 AI Chat Interface <span class='company-badge'>Company {company_id}</span>",
                unsafe_allow_html=True)
    st.markdown("Ask natural language questions about sales, inventory, or cash flow!")

    # Quick action buttons
    st.markdown("**💡 Quick Actions:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Sales Summary", use_container_width=True):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "user", "content": "Sales summary"})
            st.rerun()

    with col2:
        if st.button("💰 Cash Flow", use_container_width=True):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "user", "content": "Cash flow summary"})
            st.rerun()

    with col3:
        if st.button("📦 Inventory", use_container_width=True):
            if "messages" not in st.session_state:
                st.session_state.messages = []
            st.session_state.messages.append({"role": "user", "content": "Inventory summary"})
            st.rerun()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": f"👋 Hello! I'm your AI ERP assistant for **Company {company_id}**. I'm connected to **AWS RDS** with live production data!\n\n"
                           f"I can help you analyze:\n\n"
                           f"• 📊 **Sales Data**: Revenue reports, orders, forecasting\n"
                           f"• 📦 **Inventory**: Stock levels, risk assessment, alerts\n"
                           f"• 💰 **Cash Flow**: Financial position, projections\n\n"
                           f"What would you like to know about your business data?"
            }
        ]

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input(f"Ask about Company {company_id} data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing real-time ERP data from AWS..."):
                if demo_mode:
                    time.sleep(0.3)  # Smooth demo experience
                response = process_user_query(prompt, company_id)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


def process_user_query(query, company_id):
    """Process user query using keyword matching and agents"""
    query_lower = query.lower()

    # Check for procedure/help queries first
    if any(word in query_lower for word in ['how to', 'how do i', 'create', 'make', 'generate', 'add', 'new']):
        if any(word in query_lower for word in ['invoice', 'sales invoice', 'bill']):
            return sales_agent.process_query(query, company_id)
        elif any(word in query_lower for word in ['purchase', 'vendor', 'supplier']):
            return "Purchase invoice creation guide coming soon!"
        elif any(word in query_lower for word in ['payment', 'voucher', 'receipt']):
            return "Payment voucher creation guide coming soon!"

    # Keyword-based intent detection
    if any(word in query_lower for word in ['cash', 'flow', 'financial', 'payment', 'voucher', 'liquidity']):
        return cashflow_agent.process_query(query, company_id)
    elif any(word in query_lower for word in ['sales', 'revenue', 'invoice', 'order', 'sell', 'customer']):
        return sales_agent.process_query(query, company_id)
    elif any(word in query_lower for word in ['inventory', 'stock', 'warehouse', 'quantity', 'low stock', 'out of stock']):
        return inventory_agent.process_query(query, company_id)
    elif any(word in query_lower for word in ['help', 'what can', 'assist', 'support', 'guide', 'manual']):
        return f"""
I'm your AI assistant for Company {company_id}, connected to AWS RDS with live ERP data.

I can help you with:

📊 **Data Analysis:**
• Sales performance and revenue reports
• Inventory levels and stock management
• Cash flow and financial position

📝 **Procedural Guides:**
• How to create Sales Invoices
• How to manage inventory
• How to process payments

Try asking me:
• "How do I create a sales invoice?"
• "Show me sales summary"
• "What's our cash flow position?"
• "Any inventory alerts?"
"""
    else:
        try:
            return sales_agent.process_query(query, company_id)
        except:
            return f"I can help you with data analysis or procedural guides for Company {company_id}. What specific information would you like?"


if __name__ == "__main__":
    main()