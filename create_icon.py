from PIL import Image, ImageDraw
import base64
import io

def create_icon_base64(draw_func):
    """Creates a 16x16 PNG image and returns it as a base64 encoded string."""
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw)

    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def draw_new_file(draw):
    draw.line((8, 3, 8, 12), fill="white", width=2)
    draw.line((3, 8, 12, 8), fill="white", width=2)

def draw_open_file(draw):
    draw.rectangle((1, 4, 15, 13), fill="#FFD700", outline="black")
    draw.rectangle((0, 2, 6, 5), fill="#FFD700", outline="black")

def draw_save(draw):
    draw.rectangle((2, 2, 14, 14), fill="blue", outline="white")
    draw.rectangle((4, 8, 12, 14), fill="white")
    draw.line((6, 2, 6, 6), fill="white", width=2)
    draw.line((10, 2, 10, 6), fill="white", width=2)

def draw_cut(draw):
    draw.line((3, 3, 13, 13), fill="red", width=2)
    draw.line((3, 13, 13, 3), fill="red", width=2)
    draw.ellipse((2, 8, 6, 12), fill="white", outline="red")
    draw.ellipse((10, 8, 14, 12), fill="white", outline="red")

def draw_copy(draw):
    draw.rectangle((2, 2, 10, 10), fill="white", outline="black")
    draw.rectangle((6, 6, 14, 14), fill="white", outline="black")

def draw_paste(draw):
    draw.rectangle((2, 2, 10, 14), fill="lightblue", outline="black")
    draw.rectangle((6, 4, 14, 6), fill="white", outline="black")
    draw.rectangle((6, 8, 14, 10), fill="white", outline="black")
    draw.rectangle((6, 12, 14, 14), fill="white", outline="black")

def draw_undo(draw):
    draw.arc((2, 2, 14, 14), 90, 270, fill="blue", width=2)
    draw.polygon([(2, 8), (6, 12), (6, 4)], fill="blue")

def draw_redo(draw):
    draw.arc((2, 2, 14, 14), 270, 90, fill="blue", width=2)
    draw.polygon([(14, 8), (10, 12), (10, 4)], fill="blue")

def draw_format_code(draw):
    draw.line((3, 4, 8, 4), fill="white", width=2)
    draw.line((3, 8, 13, 8), fill="white", width=2)
    draw.line((3, 12, 8, 12), fill="white", width=2)

def draw_calendar(draw):
    draw.rectangle((2, 2, 14, 14), fill="white", outline="black")
    draw.line((2, 6, 14, 6), fill="black", width=1)
    draw.line((5, 2, 5, 6), fill="black", width=1)
    draw.line((8, 2, 8, 6), fill="black", width=1)
    draw.line((11, 2, 11, 6), fill="black", width=1)

if __name__ == "__main__":
    icons = {
        "new-file": draw_new_file,
        "open-file": draw_open_file,
        "save": draw_save,
        "cut": draw_cut,
        "copy": draw_copy,
        "paste": draw_paste,
        "undo": draw_undo,
        "redo": draw_redo,
        "format-code": draw_format_code,
        "calendar": draw_calendar,
    }

    for name, func in icons.items():
        print(f'"{name}": "{create_icon_base64(func)}",')
