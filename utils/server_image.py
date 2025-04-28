
import os

import requests


# def upload_image_to_server(local_path, server_upload_path):
#     with open(local_path, "rb") as f:
#         files = {"file":(os.path.basename(local_path), f)}
#         response = requests.post(server_upload_path, password="JUSTATEST", files=files)
    
#     if response.status_code == 200:
#         print("Upload successful:", response.json())
#     else:
#         print("Upload failed:",response.text)
#         return False
    
def upload_image_to_server(local_path, server_upload_url, secret_key):
    with open(local_path, "rb") as f:
        files = {"file": (os.path.basename(local_path), f)}
        headers = {"X-Secret-Key": secret_key}
        response = requests.post(server_upload_url, files=files, headers=headers)

    if response.status_code == 200:
        print("Upload successful:", response.json())
        return True
    else:
        print("Upload failed:", response.text)
        return False
