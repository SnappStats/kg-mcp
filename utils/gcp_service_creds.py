import os

def load_service_credentials():
  sa_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
  if sa_json:
    try:
      creds_path = os.path.join(os.getcwd(), "gcp_creds_key.json")
      with open(creds_path, 'w') as f:
        f.write(sa_json)
      os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
      print("✅ Service account credentials configured from environment")
    except Exception as e:
      print(f"⚠️ Failed to setup service account credentials: {e}")