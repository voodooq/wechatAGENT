import sys
import os
import traceback

print("--- Diagnostic Start ---")
print(f"Current Directory: {os.getcwd()}")
sys.path.insert(0, os.getcwd())

try:
    print("Step 1: Importing core.config")
    import core.config
    print("Successfully imported core.config")
    
    print("Step 2: Accessing core.config.conf")
    from core.config import conf
    print(f"Successfully accessed conf: {conf}")
    
    print("Step 3: Importing utils.logger")
    import utils.logger
    print("Successfully imported utils.logger")
    
    print("Step 4: Importing main (partially)")
    import main
    print("Successfully imported main")
    
except ImportError as e:
    print(f"\n!!! ImportError detected: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"\n!!! Unexpected error: {e}")
    traceback.print_exc()

print("--- Diagnostic End ---")
