# test_fixed_agents.py
from agents.sales_agent import SalesAgent
from agents.inventory_agent import InventoryAgent

print("Testing FIXED Agents...")
print("=" * 60)

company_id = 922

print("\n1. Testing SalesAgent.get_sales_summary():")
sales_agent = SalesAgent()
sales_result = sales_agent.get_sales_summary(company_id)
print(f"   Result length: {len(sales_result)}")
print(f"   First 300 chars:\n{sales_result[:300]}")
print(f"   Contains 'Error': {'Error' in sales_result}")

print("\n2. Testing InventoryAgent.get_inventory_summary():")
inv_agent = InventoryAgent()
inv_result = inv_agent.get_inventory_summary(company_id)
print(f"   Result length: {len(inv_result)}")
print(f"   First 300 chars:\n{inv_result[:300]}")
print(f"   Contains 'Error': {'Error' in inv_result}")

print("\n" + "=" * 60)
if "Error" not in sales_result and "Error" not in inv_result:
    print("🎉 SUCCESS! Agents are now working!")
else:
    print("❌ Still having issues - check the error messages")