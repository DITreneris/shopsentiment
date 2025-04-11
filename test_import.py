"""
Simple test script to diagnose import issues.
"""

import traceback

try:
    print("Attempting to import app...")
    from app import app
    print("Successfully imported app!")
except Exception as e:
    print(f"Error: {e}")
    print("Detailed traceback:")
    traceback.print_exc()
    
print("Test completed.") 