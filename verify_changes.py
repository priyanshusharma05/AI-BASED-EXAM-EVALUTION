
import sys
import os

# Add backend directory to path
sys.path.append(r"d:\Final\backend")

print("Verifying imports...")

try:
    from routes import ai_routes
    print("✅ Successfully imported routes.ai_routes")
except ImportError as e:
    print(f"❌ Failed to import routes.ai_routes: {e}")
except Exception as e:
    print(f"❌ Error importing routes.ai_routes: {e}")

try:
    from models import extraction_service
    print("✅ Successfully imported models.extraction_service")
except ImportError as e:
    print(f"❌ Failed to import models.extraction_service: {e}")
except Exception as e:
    print(f"❌ Error importing models.extraction_service: {e}")

print("Verification complete.")
