from flask import Flask, request, jsonify
from PIL import Image
import os
import random
import requests

app = Flask(__name__)

BASE = "https://science.nasa.gov/specials/your-name-in-landsat/images/"
UPLOAD_DIR = "uploads"
OUTPUT_FILE = "nasa_name.png"
LETTERS = "abcdefghijklmnopqrstuvwxyz"


def ensure_images():
    for folder in ["0", "1", "2"]:
        os.makedirs(os.path.join(UPLOAD_DIR, folder), exist_ok=True)

    if os.path.exists(os.path.join(UPLOAD_DIR, "0", "a.jpg")):
        return

    for variant in range(3):
        folder_path = os.path.join(UPLOAD_DIR, str(variant))

        for ch in LETTERS:
            url = f"{BASE}{ch}_{variant}.jpg"
            save_path = os.path.join(folder_path, f"{ch}.jpg")

            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    with open(save_path, "wb") as f:
                        f.write(r.content)
            except:
                pass


def get_random_letter_image(letter):
    available = []

    for folder in ["0", "1", "2"]:
        path = os.path.join(UPLOAD_DIR, folder, f"{letter}.jpg")
        if os.path.exists(path):
            available.append(path)

    if not available:
        return None

    return Image.open(random.choice(available))


def generate_name_image(name):
    ensure_images()
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
        # direct download link
        return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")

    return None


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "endpoint": "/nasa?name=demo"
    })


@app.route("/nasa")
def nasa():
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


if __name__ == "__main__":
    app.run(debug=True)