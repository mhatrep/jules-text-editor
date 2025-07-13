from PIL import Image, ImageDraw

def create_new_file_icon():
    """Creates a 16x16 PNG image with a plus sign."""
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a white plus sign
    draw.line((8, 3, 8, 12), fill="white", width=2)
    draw.line((3, 8, 12, 8), fill="white", width=2)

    img.save("assets/icons/new-file.png", "PNG")

if __name__ == "__main__":
    create_new_file_icon()
