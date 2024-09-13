from flask import Flask, render_template, request, send_file
from PIL import Image
import os
from urllib.parse import quote


app = Flask(__name__)

def process_image(file, cropped_file=None):
    if cropped_file:
        # If a cropped image file is provided, use it for processing
        uploaded_image = Image.open(cropped_file)
    else:
        # If no cropped image file is provided, use the original uploaded image
        uploaded_image = Image.open(file)

    # Correct the image orientation
    uploaded_image = correct_image_orientation(uploaded_image)

    # Convert the image to RGBA mode
    uploaded_image = uploaded_image.convert("RGBA")

    # Open the frame image
    frame = Image.open("frame.png").convert("RGBA")

    # Calculate the position and size for the uploaded image in the frame
    # Assuming the frame has a white space in the middle and text at the top and bottom
    frame_width, frame_height = frame.size
    uploaded_image_width, uploaded_image_height = uploaded_image.size

    # Calculate the aspect ratio of the uploaded image
    uploaded_image_aspect_ratio = uploaded_image_width / uploaded_image_height

    # Calculate the new width and height for the uploaded image to fit the frame's white space
    # while maintaining its aspect ratio and leaving space for the text at the top and bottom
    text_height_top = 400  # Adjust this value according to the height of the text at the top in your frame
    text_height_bottom = 290  # Adjust this value according to the height of the text at the bottom in your frame
    available_height = frame_height - text_height_top - text_height_bottom

    if uploaded_image_aspect_ratio > 1:
        # Landscape image
        new_width = frame_width
        new_height = int(frame_width / uploaded_image_aspect_ratio)
        if new_height > available_height:
            new_height = available_height
            new_width = int(new_height * uploaded_image_aspect_ratio)
    else:
        # Portrait image
        new_height = available_height
        new_width = int(available_height * uploaded_image_aspect_ratio)
        if new_width > frame_width:
            new_width = frame_width
            new_height = int(new_width / uploaded_image_aspect_ratio)

    # Resize the uploaded image to fit the calculated dimensions with Lanczos anti-aliasing
    uploaded_image = uploaded_image.resize((new_width, new_height), Image.LANCZOS)

    # Calculate the position for the uploaded image in the frame
    # Adjust the vertical position to be centered between the top and bottom text
    vertical_offset = (text_height_top + ((frame_height - text_height_top - text_height_bottom - new_height) // 2))
    uploaded_image_position = ((frame_width - new_width) // 2, vertical_offset)

    # Paste the uploaded image onto the frame at the calculated position
    frame.paste(uploaded_image, uploaded_image_position)

    # Save the combined image
    frame.save("static/output.png")

    # Schedule the deletion of the locally saved image after 10 minutes
    

    # Return the path to the combined image
    return "output.png"

def correct_image_orientation(image):
    try:
        # Check the EXIF data for the image orientation
        image_exif = image._getexif()
        if image_exif:
            orientation = image_exif.get(0x0112)
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # If there's an error accessing the EXIF data, do nothing
        pass
    return image

@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        if request.files:
            # Check if the request contains the cropped image data
            if "cropped_image" in request.files:
                cropped_image = request.files["cropped_image"]
                if cropped_image.filename != "":
                    # Save the cropped image
                    cropped_image_path = "static/cropped_image.png"
                    cropped_image.save(cropped_image_path)
                    # Process the cropped image and get the path to the combined image
                    processed_image = process_image(cropped_file=cropped_image_path)
                    return render_template("result.html", image=processed_image)
            # If the request does not contain cropped image data, fallback to handling the original uploaded image
            elif "image" in request.files:
                image = request.files["image"]
                if image.filename != "":
                    # Save the uploaded image
                    image_path = "static/original_image.png"
                    image.save(image_path)
                    # Process the image and get the path to the combined image
                    processed_image = process_image(file=image_path)
                    return render_template("result.html", image=processed_image)
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
