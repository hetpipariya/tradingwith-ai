import requests
import json
import pyotp
import socket
import uuid


api_key = "CWBI5fnF"
client_code = "AACB794689"
password = "7310"
totp_secret = "ZJH6GT6X64G7K5SJFK42OO73JA"


totp = pyotp.TOTP(totp_secret).now()


client_local_ip = socket.gethostbyname(socket.gethostname())
client_public_ip = requests.get('https://api.ipify.org').text
mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])

url = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword"

payload = {
    "clientcode": client_code,
    "password": password,
    "totp": totp
}

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-UserType': 'USER',
    'X-SourceID': 'WEB',
    'X-ClientLocalIP': client_local_ip,
    'X-ClientPublicIP': client_public_ip,
    'X-MACAddress': mac_address,
    'X-PrivateKey': api_key
}

try:
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data['status']:
            print("--- LOGIN SUCCESS! ---")
            print(f"JWT Token: {data['data']['jwtToken'][:20]}...") 
        else:
            print(f"Login Failed: {data['message']}")

except Exception as e:
    print(f"Error occurred: {e}")