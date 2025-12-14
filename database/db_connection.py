import mysql.connector
import streamlit as st
from mysql.connector import Error
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConnection:
    def __init__(self):
        self.connection = None
        try:
            self.config = {
                'host': st.secrets.get("DB_HOST", os.getenv('DB_HOST')),
                'database': st.secrets.get("DB_NAME", os.getenv('DB_NAME')),
                'user': st.secrets.get("DB_USER", os.getenv('DB_USER')),
                'password': st.secrets.get("DB_PASSWORD", os.getenv('DB_PASSWORD')),
                'port': int(st.secrets.get("DB_PORT", os.getenv('DB_PORT', 3306))),
                'connection_timeout': 30,
                'connect_timeout': 30,
                'use_pure': True,
                'buffered': True
            }
        except:
            # Fallback to env vars if secrets not available
            self.config = {
                'host': os.getenv('DB_HOST'),
                'database': os.getenv('DB_NAME'),
                'user': os.getenv('DB_USER'),
                'password': os.getenv('DB_PASSWORD'),
                'port': int(os.getenv('DB_PORT', 3306)),
                'connection_timeout': 30,
                'connect_timeout': 30,
                'use_pure': True,
                'buffered': True
            }
        self.current_company_id = None
        
        # Validate required config
        if not all([self.config['host'], self.config['database'], 
                    self.config['user'], self.config['password']]):
            raise ValueError("Missing required database configuration in .env file")
        
        print(f"🔧 DatabaseConnection initialized with host: {self.config['host']}")

    def set_company_id(self, company_id):
        """Set the current company context with validation"""
        # Validate company_id is numeric
        try:
            company_id_int = int(company_id)
            self.current_company_id = company_id_int
            print(f"🔧 Set company_id to: {company_id_int}")
        except (ValueError, TypeError):
            raise ValueError(f"Invalid company_id: {company_id}. Must be numeric.")

    def get_connection(self):
        try:
            # Always try to reconnect if connection doesn't exist or is closed
            if self.connection is None:
                print(f"🔄 Connecting to AWS RDS (new connection)...")
                self.connection = mysql.connector.connect(**self.config)

                if self.connection.is_connected():
                    print("✅ Connected to AWS RDS MySQL successfully!")
                    db_info = self.connection.get_server_info()
                    print(f"✅ MySQL Server version: {db_info}")
                    return self.connection
                else:
                    print("❌ Connection failed - not connected")
                    return None
            else:
                # Check if existing connection is still alive
                try:
                    self.connection.ping(reconnect=True, attempts=3, delay=5)
                    if self.connection.is_connected():
                        print(f"🔗 Using existing connection (connected)")
                        return self.connection
                    else:
                        print(f"🔄 Reconnecting (connection lost)...")
                        self.connection = mysql.connector.connect(**self.config)
                        if self.connection.is_connected():
                            print("✅ Reconnected to AWS RDS MySQL successfully!")
                            return self.connection
                        else:
                            print("❌ Reconnection failed")
                            self.connection = None
                            return None
                except Error as e:
                    print(f"🔄 Connection ping failed, reconnecting: {e}")
                    try:
                        self.connection = mysql.connector.connect(**self.config)
                        if self.connection.is_connected():
                            print("✅ Reconnected to AWS RDS MySQL successfully!")
                            return self.connection
                        else:
                            print("❌ Reconnection failed")
                            self.connection = None
                            return None
                    except Error as e2:
                        print(f"❌ Reconnection error: {e2}")
                        self.connection = None
                        return None

        except Error as e:
            error_msg = f"❌ AWS RDS Connection Error: {e}"
            print(error_msg)
            st.error(f"Database Error: {e}")
            self.connection = None
            return None
        except Exception as e:
            error_msg = f"❌ Unexpected Connection Error: {e}"
            print(error_msg)
            self.connection = None
            return None

    def close_connection(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔒 Database connection closed")
        self.connection = None

    def execute_query(self, query, params=None, company_id=None):
        """Execute query with company context - READ ONLY"""
        print(f"🔍 DatabaseConnection.execute_query called")
        print(f"🔍 Query preview: {query[:100]}...")
        print(f"🔍 Params received: {params}")
        print(f"🔍 Company context: {company_id or self.current_company_id}")

        # SQL Injection Prevention - Check for write operations
        import re
        
        # Remove string literals and comments before checking
        string_pattern = r'(\"[^\"]*\"|\'[^\']*\')'
        query_without_strings = re.sub(string_pattern, "''", query)
        comment_pattern = r'(--[^\n]*|/\*.*?\*/)'
        query_clean = re.sub(comment_pattern, '', query_without_strings, flags=re.DOTALL | re.MULTILINE)
        
        query_upper = query_clean.upper().strip()
        statements = [s.strip() for s in query_upper.split(';') if s.strip()]
        write_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'REPLACE']
        
        for statement in statements:
            first_word = statement.split()[0] if statement.split() else ''
            if first_word in write_keywords:
                raise Exception(f"Security violation: Write operation '{first_word}' detected. Read-only mode.")

        # Get connection with retry
        connection = None
        for attempt in range(2):
            connection = self.get_connection()
            if connection:
                break
            print(f"⚠️ Connection attempt {attempt + 1} failed, retrying...")

        if not connection:
            print("❌ No database connection available after retries")
            return None

        try:
            cursor = connection.cursor(dictionary=True)
            print(f"🔍 Executing query with cursor...")
            
            # Execute with provided params (agents provide complete params)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            print(f"🔍 Query executed successfully, fetched {len(result)} rows")
            cursor.close()
            return result
            
        except Error as e:
            print(f"❌ Query Error: {e}")
            print(f"❌ Query was: {query}")
            print(f"❌ Params were: {params}")
            self.close_connection()
            return None
        except Exception as e:
            print(f"❌ Unexpected query error: {e}")
            self.close_connection()
            return None

    def execute_query_dataframe(self, query, params=None, company_id=None):
        """Execute query and return as pandas DataFrame"""
        result = self.execute_query(query, params, company_id)
        if result:
            df = pd.DataFrame(result)
            print(f"🔍 Created DataFrame with {len(df)} rows")
            return df
        print("🔍 No result, returning empty DataFrame")
        return pd.DataFrame()


# Global database instance
db = DatabaseConnection()