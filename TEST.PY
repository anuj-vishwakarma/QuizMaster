from PIL import Image
import pytesseract

from PIL import Image


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
image = Image.open("static/login_background.jpg")
print(pytesseract.image_to_string(image))