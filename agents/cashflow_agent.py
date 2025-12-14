import re
import pandas as pd
from database.db_connection import db
import traceback


class CashFlowAgent:
    def __init__(self):
        self.keywords = ['cash flow', 'cashflow', 'liquidity', 'financial', 'forecast', 'voucher', 'payment']

    def process_query(self, message, company_id, method_name="auto"):
        """Process cash flow query with optional specific method"""
        print(f"🔍 CashFlowAgent.process_query called with company_id={company_id}, method={method_name}")
        if method_name == "auto":
            method_name = self._detect_method(message)

        method_map = {
            "get_cashflow_summary": self.get_cashflow_summary,
            "get_transaction_breakdown": self.get_transaction_breakdown,
        }

        method = method_map.get(method_name, self.get_cashflow_summary)
        return method(company_id)

    def _detect_method(self, message):
        """Detect which method to call based on message content"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['breakdown', 'detail', 'category', 'type', 'overview']):
            return "get_transaction_breakdown"
        else:
            return "get_cashflow_summary"

    def get_cashflow_summary(self, company_id):
        """Get cash flow summary - FIXED with parameterized query"""
        print(f"💰 CashFlowAgent.get_cashflow_summary called for company {company_id}")

        try:
            # FIXED: Using %s placeholder instead of f-string
            query = """
                SELECT COUNT(*)                   as transaction_count,
                       SUM(COALESCE(credit, 0))   as total_inflow,
                       SUM(COALESCE(debit, 0))    as total_outflow,
                       COUNT(DISTINCT voucher_id) as unique_vouchers
                FROM voucher_items
                WHERE company_id = %s
            """

            print(f"🔍 Executing cash flow query for company {company_id}")
            # FIXED: Passing company_id as parameter tuple
            result = db.execute_query(query, (company_id,))

            if result and len(result) > 0:
                data = result[0]
                print(f"✅ Query successful! Data: {data}")

                # Handle None values
                transaction_count = data['transaction_count'] or 0
                total_inflow = float(data['total_inflow'] or 0)
                total_outflow = float(data['total_outflow'] or 0)
                unique_vouchers = data['unique_vouchers'] or 0
                net_cashflow = total_inflow - total_outflow

                response = f"""
**💰 CASH FLOW SUMMARY - Company {company_id}**

📊 **Core Metrics:**
- **Total Transactions**: {transaction_count:,}
- **Unique Vouchers**: {unique_vouchers:,}
- **Total Cash Inflows**: **${total_inflow:,.2f}**
- **Total Cash Outflows**: **${total_outflow:,.2f}**
- **Net Cash Position**: **${net_cashflow:,.2f}**
- **Financial Status**: {'⚖️ PERFECTLY BALANCED' if abs(net_cashflow) < 1 else '📈 NET POSITIVE' if net_cashflow > 0 else '📉 NET NEGATIVE'}

📈 **Business Insights:**
- **Enterprise Scale**: Processing **${total_inflow / 1_000_000:,.1f}M** in financial operations
- **Transaction Velocity**: **{transaction_count:,}** processed transactions
- **Document Efficiency**: **{unique_vouchers:,}** financial documents managed

*Live data from AWS RDS production database*
"""
                return response
            else:
                return f"No cash flow data found for company {company_id}"

        except Exception as e:
            print(f"❌ Error in get_cashflow_summary: {str(e)}")
            print(f"❌ Traceback:\n{traceback.format_exc()}")
            return f"Error retrieving cash flow data: {str(e)}"

    def get_transaction_breakdown(self, company_id):
        """Get transaction breakdown - FIXED with parameterized query"""
        try:
            # FIXED: Using %s placeholder instead of f-string
            query = """
                SELECT COUNT(*)                   as total_count,
                       COUNT(DISTINCT voucher_id) as voucher_count,
                       SUM(COALESCE(credit, 0))   as total_credit,
                       SUM(COALESCE(debit, 0))    as total_debit
                FROM voucher_items
                WHERE company_id = %s
            """

            # FIXED: Passing company_id as parameter tuple
            result = db.execute_query(query, (company_id,))

            if result and len(result) > 0:
                data = result[0]

                if data['total_count'] is None or data['total_count'] == 0:
                    return f"No transaction data found for company {company_id}"

                return f"""
**Transaction Breakdown - Company {company_id}**

📊 **Summary:**
- Total Transactions: {data['total_count']:,}
- Unique Vouchers: {data['voucher_count']:,}
- Total Credit: ${data['total_credit']:,.2f}
- Total Debit: ${data['total_debit']:,.2f}

*Data retrieved successfully from AWS RDS*
"""
            else:
                return f"No transaction data found for company {company_id}"

        except Exception as e:
            return f"Error retrieving transaction breakdown: {str(e)}"