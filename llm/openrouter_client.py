import os
import requests
import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


class OpenRouterClient:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        self.model = os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.1-8b-instruct:free')

    def classify_intent(self, user_message, company_id):
        """Use LLM to classify user intent and generate appropriate response"""

        system_prompt = f"""You are an intelligent ERP assistant for a multi-company system. 
Current company context: {company_id}

Analyze the user's query and determine:
1. Intent category: sales, inventory, cashflow, or general
2. Specific information needed
3. Appropriate response based on available ERP data

Available data domains:
- SALES: revenue reports, orders, invoices, sales performance, forecasting
- INVENTORY: stock levels, warehouse data, risk assessment, stockout predictions
- CASHFLOW: payments, vouchers, liquidity, financial forecasting, cash positions

Respond in JSON format with:
{{
    "intent": "sales|inventory|cashflow|general",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "suggested_agent_method": "specific method to call",
    "response_template": "template for final response with placeholders"
}}"""

        try:
            response = requests.post(
                url=f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,
                    "max_tokens": 500
                }),
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            else:
                st.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return self._fallback_intent_classification(user_message)

        except Exception as e:
            st.error(f"Error calling OpenRouter: {str(e)}")
            return self._fallback_intent_classification(user_message)

    def _fallback_intent_classification(self, message):
        """Fallback rule-based classification if LLM fails"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['sales', 'revenue', 'order', 'invoice', 'sell']):
            return {
                "intent": "sales",
                "confidence": 0.8,
                "reasoning": "Detected sales-related keywords",
                "suggested_agent_method": "get_sales_summary",
                "response_template": "Based on the sales data for company {company_id}: {data}"
            }
        elif any(word in message_lower for word in ['inventory', 'stock', 'warehouse', 'quantity']):
            return {
                "intent": "inventory",
                "confidence": 0.8,
                "reasoning": "Detected inventory-related keywords",
                "suggested_agent_method": "get_inventory_summary",
                "response_template": "Here's the inventory overview for company {company_id}: {data}"
            }
        elif any(word in message_lower for word in ['cash', 'flow', 'payment', 'voucher', 'financial']):
            return {
                "intent": "cashflow",
                "confidence": 0.8,
                "reasoning": "Detected cash flow related keywords",
                "suggested_agent_method": "get_cashflow_summary",
                "response_template": "Cash flow analysis for company {company_id}: {data}"
            }
        else:
            return {
                "intent": "general",
                "confidence": 0.5,
                "reasoning": "Could not determine specific intent",
                "suggested_agent_method": "general_help",
                "response_template": "I can help you with sales, inventory, and cash flow data for company {company_id}. What specific information do you need?"
            }

    def generate_natural_response(self, user_message, data_context, intent_info, company_id):
        """Generate natural language response using LLM"""

        system_prompt = f"""You are a helpful ERP assistant for company {company_id}. 
The user asked: "{user_message}"

You have retrieved the following data:
{data_context}

Intent analysis: {intent_info.get('reasoning', 'N/A')}

Please provide a helpful, natural response that:
1. Directly answers the user's question
2. Presents the data in an easy-to-understand format
3. Highlights key insights from the data
4. Is professional but conversational
5. Mentions the company context when relevant

Keep the response concise but informative."""

        try:
            response = requests.post(
                url=f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800
                }),
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Data for company {company_id}:\n\n{data_context}"

        except Exception as e:
            return f"Data for company {company_id}:\n\n{data_context}"


# Global LLM client instance
llm_client = OpenRouterClient()