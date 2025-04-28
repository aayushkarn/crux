from io import BytesIO
import re
import uuid
from PIL import Image
import os

import requests

from config import ALLOWED_IMAGE_EXTENSION



# def image_upload(file, upload_path, root_dir, thumbnail=True):
#     if file.lower().startswith(("http","https")):
#         response = requests.get(file)
#         if response.status_code==200:
#             # Ensure the content is an image
#             content_type = response.headers.get('Content-Type')
#             if 'image' in content_type:
#                 image = Image.open(BytesIO(response.content))
#                 clean_url = re.sub(r'\?.*$', '', file)
#                 filename = f"{uuid.uuid4().hex}_{os.path.basename(clean_url)}"
#                 upload_file_path = os.path.join(root_dir, upload_path.lstrip(os.sep), filename)
#                 os.makedirs(os.path.dirname(upload_file_path), exist_ok=True)
#                 image.save(upload_file_path)
#                 relative_path = os.path.relpath(upload_file_path, root_dir)
#                 return relative_path
#         else:
#             print(f"Failed to download image from {file}.Status Code {response.status_code}")
#             return None
#     else:
#         if file.split(".")[-1].lower() in ALLOWED_IMAGE_EXTENSION:
#             image = Image.open(file)
#             if thumbnail:
#                 image.thumbnail((200,200))
#             filename = f"{uuid.uuid4().hex}_{os.path.basename(file)}"
#             upload_file_path = os.path.join(root_dir, upload_path.lstrip(os.sep), filename)
#             os.makedirs(os.path.dirname(upload_file_path), exist_ok=True)
#             image.save(upload_file_path)
#             relative_path = os.path.relpath(upload_file_path, root_dir)
#             return relative_path
#     return None

def remove_image(upload_path, root_dir):
    path=os.path.join(root_dir,upload_path)
    if os.path.exists(path):
        os.remove(path)

def image_upload(file, upload_path, root_dir, thumbnail=True):
    if not file:
        return None  # Handle None case early and safely

    if isinstance(file, str) and file.lower().startswith(("http", "https")):
        response = requests.get(file)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type')
            if 'image' in content_type:
                image = Image.open(BytesIO(response.content))
                clean_url = re.sub(r'\?.*$', '', file)
                filename = f"{uuid.uuid4().hex}_{os.path.basename(clean_url)}"
                upload_file_path = os.path.join(root_dir, upload_path.lstrip(os.sep), filename)
                os.makedirs(os.path.dirname(upload_file_path), exist_ok=True)
                image.save(upload_file_path)
                relative_path = os.path.relpath(upload_file_path, root_dir)
                return relative_path
        else:
            print(f"Failed to download image from {file}. Status Code {response.status_code}")
            return None

    elif isinstance(file, str) and file.split(".")[-1].lower() in ALLOWED_IMAGE_EXTENSION:
        image = Image.open(file)
        if thumbnail:
            image.thumbnail((200, 200))
        filename = f"{uuid.uuid4().hex}_{os.path.basename(file)}"
        upload_file_path = os.path.join(root_dir, upload_path.lstrip(os.sep), filename)
        os.makedirs(os.path.dirname(upload_file_path), exist_ok=True)
        image.save(upload_file_path)
        relative_path = os.path.relpath(upload_file_path, root_dir)
        return relative_path

    return None


def image_exists(file, upload_path):
    # TODO: Fix for DB
    file_path = os.path.join(upload_path, os.path.basename(file))   
    if os.path.exists(file_path):
        return True
    return False