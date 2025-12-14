import re
import pandas as pd
from database.db_connection import db


class InventoryAgent:
    def __init__(self):
        self.keywords = ['inventory', 'stock', 'levels', 'warehouse', 'quantity', 'in stock', 'risk', 'stockout']

    def process_query(self, message, company_id, method_name="auto"):
        """Process inventory query with optional specific method"""
        if method_name == "auto":
            method_name = self._detect_method(message)

        method_map = {
            "get_inventory_summary": self.get_inventory_summary,
            "get_inventory_risk": self.get_inventory_risk,
            "get_low_stock_items": self.get_low_stock_items,
            "get_out_of_stock_items": self.get_out_of_stock_items,
            "get_product_inventory": self.get_product_inventory
        }

        method = method_map.get(method_name, self.get_inventory_summary)
        return method(company_id)

    def _detect_method(self, message):
        """Detect which method to call based on message content"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['risk', 'stockout', 'prediction', 'alert']):
            return "get_inventory_risk"
        elif any(word in message_lower for word in ['low', 'minimum']):
            return "get_low_stock_items"
        elif any(word in message_lower for word in ['out of stock', 'zero']):
            return "get_out_of_stock_items"
        elif any(word in message_lower for word in ['product', 'item']):
            return "get_product_inventory"
        else:
            return "get_inventory_summary"

    def get_inventory_summary(self, company_id):
        """Get inventory summary - FIXED with parameterized query"""
        try:
            # FIXED: Using %s placeholder instead of f-string
            query = """
                SELECT COUNT(DISTINCT product_id)   as total_products,
                       SUM(quantity)                as total_quantity,
                       AVG(quantity)                as avg_quantity_per_product,
                       COUNT(DISTINCT warehouse_id) as total_warehouses
                FROM stock
                WHERE company_id = %s
                  AND stock_type = 'purchase'
            """

            # FIXED: Passing company_id as parameter tuple
            result = db.execute_query(query, (company_id,))
            
            if result and len(result) > 0:
                summary = result[0]

                # Handle None values before formatting
                total_products = summary['total_products'] or 0
                total_quantity = float(summary['total_quantity'] or 0)
                avg_quantity_per_product = float(summary['avg_quantity_per_product'] or 0)
                total_warehouses = summary['total_warehouses'] or 0

                response_data = f"""
**Inventory Overview - Company {company_id}**

📦 **Stock Summary:**
- Total Products: {total_products:,}
- Total Quantity in Stock: {total_quantity:,.0f} units
- Average per Product: {avg_quantity_per_product:,.0f} units
- Warehouse Locations: {total_warehouses}

*Live data from AWS RDS database*
"""
                return response_data
            else:
                return f"No inventory data found for company {company_id}"

        except Exception as e:
            return f"Error retrieving inventory summary: {str(e)}"

    def get_inventory_risk(self, company_id):
        """Get inventory risk assessment - FIXED with parameterized query"""
        try:
            # FIXED: Using %s placeholder instead of f-string
            query = """
                SELECT stock.product_id,
                       stock.warehouse_id,
                       stock.quantity,
                       products.reorder_qty_alert,
                       products.min_qty_alert,
                       products.max_qty_alert,
                       SUM(stock.cost + stock.overhead) AS cost,
                       stock.stock_date,
                       stock.expired_at,
                       stock.stock_type,
                       CASE
                           WHEN stock.invoice_id IS NULL OR stock.invoice_id = 0
                               THEN goods_receipt_note.received_date
                           ELSE purchase_invoice.invoice_date
                           END                          AS purchase_date
                FROM stock
                         LEFT JOIN purchase_invoice ON purchase_invoice.invoice_id = stock.invoice_id
                         LEFT JOIN goods_receipt_note ON goods_receipt_note.grn_id = stock.grn_id
                         LEFT JOIN products ON products.product_id = stock.product_id
                WHERE stock.company_id = %s
                  AND stock.stock_type = 'purchase'
                GROUP BY stock.stock_id LIMIT 50
            """

            # FIXED: Passing company_id as parameter tuple
            df = db.execute_query_dataframe(query, (company_id,))
            
            if not df.empty:
                low_stock_count = len(df[df['quantity'] <= df['min_qty_alert']])
                total_value = df['cost'].sum()
                avg_risk_score = (low_stock_count / len(df)) * 100

                response_data = f"""
**Inventory Risk Assessment - Company {company_id}**

⚠️ **Risk Analysis:**
- Products at Risk: {low_stock_count} items below minimum levels
- Total Inventory Value: ${total_value:,.2f}
- Risk Score: {avg_risk_score:.1f}%
- Items Monitored: {len(df)} stock entries

🔍 **Key Findings:**
- Recent stock activity up to {df['stock_date'].max().strftime('%Y-%m-%d') if df['stock_date'].max() else 'N/A'}
- Multiple warehouse locations covered
- Reorder alerts configured for risk management

*Analysis based on AWS RDS inventory data*
"""
                return response_data
            else:
                return f"No inventory risk data available for company {company_id}"

        except Exception as e:
            return f"Error analyzing inventory risk: {str(e)}"

    def get_low_stock_items(self, company_id):
        """Get low stock items - FIXED with parameterized query"""
        try:
            # FIXED: Using %s placeholder instead of f-string
            query = """
                SELECT stock.product_id,
                       stock.quantity,
                       products.min_qty_alert,
                       products.reorder_qty_alert,
                       (products.min_qty_alert - stock.quantity) as shortage,
                       stock.warehouse_id
                FROM stock
                         LEFT JOIN products ON products.product_id = stock.product_id
                WHERE stock.company_id = %s
                  AND stock.quantity <= products.min_qty_alert
                  AND stock.stock_type = 'purchase'
                ORDER BY shortage DESC LIMIT 15
            """

            # FIXED: Passing company_id as parameter tuple
            result = db.execute_query(query, (company_id,))
            
            if result:
                if len(result) == 0:
                    return "✅ No items are currently below minimum stock levels."

                response_data = f"**Low Stock Alerts - Company {company_id}**\n\n"
                response_data += "🚨 **Immediate Attention Required:**\n"

                for item in result:
                    response_data += f"📦 **Product {item['product_id']}** (Warehouse {item['warehouse_id']}):\n"
                    response_data += f"   Current Stock: {item['quantity']} units\n"
                    response_data += f"   Minimum Required: {item['min_qty_alert']} units\n"
                    response_data += f"   Shortage: {item['shortage']} units\n"
                    response_data += f"   Reorder Point: {item['reorder_qty_alert']} units\n\n"

                return response_data
            else:
                return "No low stock items found."

        except Exception as e:
            return f"Error retrieving low stock items: {str(e)}"

    def get_out_of_stock_items(self, company_id):
        """Get out of stock items - FIXED with parameterized query"""
        try:
            # FIXED: Using %s placeholder instead of f-string
            query = """
                SELECT stock.product_id,
                       stock.warehouse_id,
                       products.min_qty_alert,
                       products.reorder_qty_alert
                FROM stock
                         LEFT JOIN products ON products.product_id = stock.product_id
                WHERE stock.company_id = %s
                  AND stock.quantity = 0
                  AND stock.stock_type = 'purchase'
                ORDER BY product_id LIMIT 15
            """

            # FIXED: Passing company_id as parameter tuple
            result = db.execute_query(query, (company_id,))
            
            if result:
                if len(result) == 0:
                    return "✅ No items are currently out of stock."

                response_data = f"**Out of Stock Items - Company {company_id}**\n\n"
                response_data += "❌ **Zero Stock Alert:**\n"

                for item in result:
                    response_data += f"📦 **Product {item['product_id']}** (Warehouse {item['warehouse_id']}):\n"
                    response_data += f"   Status: COMPLETELY OUT OF STOCK\n"
                    response_data += f"   Minimum Required: {item['min_qty_alert']} units\n"
                    response_data += f"   Reorder Point: {item['reorder_qty_alert']} units\n\n"

                return response_data
            else:
                return "No out of stock items found."

        except Exception as e:
            return f"Error retrieving out of stock items: {str(e)}"

    def get_product_inventory(self, company_id):
        """Get product inventory distribution - FIXED with parameterized query"""
        try:
            # FIXED: Using %s placeholder instead of f-string
            query = """
                SELECT product_id,
                       SUM(quantity)                as total_quantity,
                       COUNT(DISTINCT warehouse_id) as warehouse_count,
                       AVG(quantity)                as avg_quantity
                FROM stock
                WHERE company_id = %s
                  AND stock_type = 'purchase'
                GROUP BY product_id
                ORDER BY total_quantity DESC LIMIT 15
            """

            # FIXED: Passing company_id as parameter tuple
            result = db.execute_query(query, (company_id,))
            
            if result:
                response_data = f"**Product Inventory Distribution - Company {company_id}**\n\n"
                response_data += "📊 **Stock by Product:**\n"

                for product in result:
                    response_data += f"📦 **Product {product['product_id']}**:\n"
                    response_data += f"   Total Quantity: {product['total_quantity']:,} units\n"
                    response_data += f"   Warehouses: {product['warehouse_count']} locations\n"
                    response_data += f"   Average per Location: {product['avg_quantity']:,.0f} units\n\n"

                return response_data
            else:
                return f"No product inventory data found for company {company_id}"

        except Exception as e:
            return f"Error retrieving product inventory: {str(e)}"