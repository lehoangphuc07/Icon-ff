from flask import Flask, request, jsonify, send_file
import struct
import re
import os
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont  # Pillow library for image processing

app = Flask(__name__)

def signed_int_to_hex(signed_int):
    return format(signed_int if signed_int >= 0 else signed_int + (1 << 32), '08X')[6:8] + ' ' + format(signed_int, '08X')[4:6] + ' ' + format(signed_int, '08X')[2:4] + ' ' + format(signed_int, '08X')[0:2]

def signed_int_to_float(signed_int):
    return struct.unpack('<f', struct.pack('<i', signed_int))[0]

def signed_int_to_signed_byte(signed_int):
    return signed_int & 0xFF if (signed_byte := signed_int & 0xFF) < 128 else signed_byte - 256

def hex_to_text(hex_str):
    return ''.join(chr(int(pair, 16)) for pair in hex_str.split())

def sanitize_text(text):
    return ''.join(c if 32 <= ord(c) < 127 else '�' for c in text)

def search_sanitized_text(filename, sanitized_text):
    if not os.path.isfile(filename):
        return []
    sanitized_text_escaped = re.escape(sanitized_text)
    with open(filename, 'r', encoding='latin-1') as file:
        text = file.read()
        return [match for match in re.findall(sanitized_text_escaped + r'[\s\S]*?Icon_([\w_]+)', text)]

def search_text(filename, text):
    if not os.path.isfile(filename):
        return []
    text_escaped = re.escape(text)
    with open(filename, 'r', encoding='latin-1') as file:
        text_content = file.read()
        results = re.findall(text_escaped + r'[\s\S]*?(Icon_[\w_]+)[\s\S]*?(T_\w+_[\w_]+)', text_content)
        formatted_results = [{'Icon': result[0], 'title': result[1]} for result in results]
        return formatted_results

def add_text_to_image(image, text):
    """Adds transparent text to the image."""
    try:
        # Create a drawing context
        draw = ImageDraw.Draw(image)

        # استخدم الخط الافتراضي
        font = ImageFont.load_default()

        # Calculate text size and position
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]  # width of the text box
        text_height = text_bbox[3] - text_bbox[1]  # height of the text box

        position = ((image.width - text_width) // 2, (image.height - text_height) // 2)

        # Add shadow effect
        shadow_offset = 10  # Adjust the shadow offset as needed
        draw.text((position[0] + shadow_offset, position[1] + shadow_offset), text, font=font, fill=(0, 0, 0, 128))

        # Add the main text
        draw.text(position, text, font=font, fill=(255, 255, 255, 255))  # White text with no transparency
    except Exception as e:
        print(f"Error adding text to image: {e}")

@app.route('/library/icons', methods=['GET'])
def get_icon():
    icon_id = request.args.get('id')
    if not icon_id:
        return jsonify({"error": "ID parameter is required"}), 400

    try:
        signed_int = int(icon_id)
    except ValueError:
        return jsonify({"error": "Invalid ID. Please enter a valid signed integer."}), 400

    # Change the path to the correct location of your assets.txt
    filename = "/root/assets.txt"  # Modify with the correct path
    hex_value = signed_int_to_hex(signed_int)
    text_value = hex_to_text(hex_value)
    sanitized_text_value = sanitize_text(text_value)

    sanitized_search_results = search_sanitized_text(filename, sanitized_text_value)
    if not sanitized_search_results:
        search_results = search_text(filename, text_value)
        if search_results:
            icon_name = search_results[0]['Icon']
        else:
            return jsonify({"error": "Text not found in the file."}), 404
    else:
        icon_name = sanitized_search_results[0]

    image_url = f"https://freefiremobile-a.akamaihd.net/common/Local/PK/FF_UI_Icon/{icon_name}.png"
    response = requests.get(image_url)
    if response.status_code == 200:
        # Load the image
        image = Image.open(BytesIO(response.content))

        # Improve image quality by resizing if needed
        image = image.convert("RGBA")  # Ensure the image is in RGBA format
        image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)  # Resize to improve sharpness

        # Add text to the image
        add_text_to_image(image, "Tanhung11231")

        # Save the modified image to a BytesIO object
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)

        # Return the modified image
        return send_file(img_io, mimetype='image/png')
    else:
        return jsonify({"error": "Image not found."}), 404

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5019)
