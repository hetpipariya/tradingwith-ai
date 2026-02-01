import os
import sys

def start_system():
    print("🚀 System Starting...")
    
    
    print("\n[1/2] Updating Tokens from Angel One...")
    os.system(f'"{sys.executable}" scripts/pipeline.py')
    
    
    print("\n[2/2] Launching Trading Terminal...")
    
    os.system(f'"{sys.executable}" -m streamlit run ui/app.py')

if __name__ == "__main__":
    start_system()