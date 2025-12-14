from database.db_connection import db


class SchemaDiscovery:
    def __init__(self):
        self.db = db

    def get_company_tables(self):
        """Discover tables that contain company_id"""
        query = """
                SELECT DISTINCT TABLE_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE COLUMN_NAME = 'company_id'
                  AND TABLE_SCHEMA = 'app_database' LIMIT 10 \
                """
        return self.db.execute_query(query)

    def get_table_structure(self, table_name):
        """Get column structure for a specific table"""
        query = """
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = %s
                  AND TABLE_SCHEMA = 'app_database'
                ORDER BY ORDINAL_POSITION LIMIT 20 \
                """
        return self.db.execute_query(query, (table_name,))

    def discover_sales_tables(self):
        """Discover sales-related tables"""
        sales_tables = ['sales_invoice', 'sales_items', 'store_issue_note', 'contacts', 'origins']
        schema_info = {}

        for table in sales_tables:
            try:
                schema_info[table] = self.get_table_structure(table)
            except:
                schema_info[table] = []

        return schema_info

    def discover_inventory_tables(self):
        """Discover inventory-related tables"""
        inventory_tables = ['stock', 'products', 'purchase_invoice', 'goods_receipt_note']
        schema_info = {}

        for table in inventory_tables:
            try:
                schema_info[table] = self.get_table_structure(table)
            except:
                schema_info[table] = []

        return schema_info

    def get_available_companies(self):
        """Get list of available companies from the database"""
        query = """
                SELECT DISTINCT company_id
                FROM sales_items
                WHERE company_id IS NOT NULL
                ORDER BY company_id LIMIT 10 \
                """
        return self.db.execute_query(query)