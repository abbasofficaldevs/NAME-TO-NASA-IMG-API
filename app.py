from flask import Flask, request, jsonify
from PIL import Image
import os
import random
import requests
import traceback

app = Flask(__name__)

# use local uploads folder from project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# output must still use /tmp for vercel
OUTPUT_FILE = "/tmp/nasa_name.png"

LETTERS = "abcdefghijklmnopqrstuvwxyz"


def get_random_letter_image(letter):
    available = []

    for folder in ["0", "1", "2"]:
        path = os.path.join(UPLOAD_DIR, folder, f"{letter}.jpg")

        if os.path.exists(path):
            available.append(path)

    if not available:
        return None

    try:
        return Image.open(random.choice(available))
    except Exception as e:
        print("Image open error:", e)
        return None


def generate_name_image(name):
    images = []

    for ch in name.lower():
        if ch in LETTERS:
            img = get_random_letter_image(ch)

            if img:
                images.append(img)

    if not images:
        return None

    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)

    final = Image.new("RGB", (total_width, max_height))

    x = 0
    for img in images:
        final.paste(img, (x, 0))
        x += img.width

    final.save(OUTPUT_FILE)

    return OUTPUT_FILE


def upload_to_tmpfiles(filepath):
    try:
        with open(filepath, "rb") as f:
            files = {"file": f}

            r = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files=files,
                timeout=30
            )

        data = r.json()

        if data.get("status") == "success":
            url = data["data"]["url"]
            return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")

    except Exception as e:
        print("Upload error:", e)

    return None


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "NASA Name API Running",
        "endpoint": "/nasa?name=abbas"
    })


@app.route("/nasa")
def nasa():
    try:
        name = request.args.get("name", "").strip()

        if not name:
            return jsonify({
                "success": False,
                "error": "name parameter required"
            }), 400

        image_path = generate_name_image(name)

        if not image_path:
            return jsonify({
                "success": False,
                "error": "image generation failed"
            }), 500

        url = upload_to_tmpfiles(image_path)

        if not url:
            return jsonify({
                "success": False,
                "error": "tmpfiles upload failed"
            }), 500

        return jsonify({
            "success": True,
            "name": name,
            "image_url": url
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500


app = app
