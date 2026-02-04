import base64
import os

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_path = "ia/static/logo.png"
if os.path.exists(logo_path):
    print(f"data:image/png;base64,{get_base64_of_bin_file(logo_path)}")
else:
    print("Logo not found")
