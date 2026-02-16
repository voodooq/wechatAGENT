import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

try:
    from core.config import conf
    print(f"Config loaded. LLM Provider: {conf.llm_provider}")
    
    # Check deepseek key specifically since that was the error
    print(f"Deepseek Key in Conf: {getattr(conf, 'deepseek_api_key', 'MISSING')[:4]}...")

    from core.agent import create_llm
    print("Attempting to create LLM...")
    llm = create_llm()
    print(f"LLM Created: {type(llm)}")
    
    # Check if key is set in the LLM instance (depending on type)
    if hasattr(llm, 'openai_api_key'):
        key = llm.openai_api_key
        if hasattr(key, 'get_secret_value'):
            print(f"LLM API Key: {key.get_secret_value()[:4]}...")
        else:
            print(f"LLM API Key: {str(key)[:4]}...")
    elif hasattr(llm, 'google_api_key'):
        # Google GLM might hide it, but let's see
        print(f"LLM API Key set (Google)")
        
    print("✅ Verification Successful")
except Exception as e:
    print(f"❌ Verification Failed: {e}")
    import traceback
    traceback.print_exc()
