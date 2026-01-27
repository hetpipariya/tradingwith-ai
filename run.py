import os
import sys

def start_system():
    print("🚀 System Starting...")
    
    # Step 1: Python પોતે જ પાઇપલાઇન રન કરશે (Token અપડેટ કરવા)
    print("\n[1/2] Updating Tokens from Angel One...")
    os.system(f'"{sys.executable}" scripts/pipeline.py')
    
    # Step 2: Python પોતે જ Streamlit ચાલુ કરશે
    print("\n[2/2] Launching Trading Terminal...")
    # આ છે તમારો 'm-streamlit' વાળો જાદુઈ કમાન્ડ
    os.system(f'"{sys.executable}" -m streamlit run ui/app.py')

if __name__ == "__main__":
    start_system()