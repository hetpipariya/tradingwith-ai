import os
from dotenv import load_dotenv
from SmartApi import SmartConnect
import pyotp

# 1. Try to load .env file
print("🔍 Reading .env file...")
loaded = load_dotenv()
if not loaded:
    print("❌ ERROR: Could not find .env file!")
    print("👉 Make sure .env file exists in this folder.")
else:
    print("✅ .env file found!")

# 2. Check Variables
api_key = os.getenv("TRADING_API_KEY")
client_id = os.getenv("CLIENT_ID")
pwd = os.getenv("TRADING_PWD")
totp_key = os.getenv("TOTP_KEY")

print(f"\n🔑 Checking Keys:")
print(f"   API Key Found?   : {'YES' if api_key else '❌ NO'}")
print(f"   Client ID Found? : {'YES' if client_id else '❌ NO'}")
print(f"   Password Found?  : {'YES' if pwd else '❌ NO'}")
print(f"   TOTP Key Found?  : {'YES' if totp_key else '❌ NO'}")

if not (api_key and client_id and pwd and totp_key):
    print("\n❌ STOPPING: Some keys are missing in .env file.")
    exit()

# 3. Try to Login
print("\n📡 Connecting to Angel One...")
try:
    obj = SmartConnect(api_key=api_key)
    totp = pyotp.TOTP(totp_key).now()
    data = obj.generateSession(client_id, pwd, totp)
    
    if data['status']:
        print("✅✅ SUCCESS! Login Worked Perfectly.")
        print(f"👤 User: {data['data']['clientcode']}")
    else:
        print("❌ Login Failed!")
        print(f"⚠️ Message: {data['message']}")
        
except Exception as e:
    print(f"\n❌ EXCEPTION (Real Error): {e}")