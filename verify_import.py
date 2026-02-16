try:
    from core.config import VOICE_MESSAGES_DIR, PROJECT_ROOT
    print(f"✅ Success: VOICE_MESSAGES_DIR imported: {VOICE_MESSAGES_DIR}")
    print(f"✅ PROJECT_ROOT: {PROJECT_ROOT}")
except ImportError as e:
    print(f"❌ Failed: {e}")
except Exception as e:
    print(f"❌ Unknown Error: {e}")
