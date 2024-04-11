import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont

literal = 'Pda801B69Bu; ba842C1C4f,14,204'
data = literal.split(';')
potential = int(data[0][3:-1], 16)
current = int(data[1][3:data[1].index(',') - 1], 16)
print(potential, current)


# Initialize the display
disp = Adafruit_SSD1306.SSD1306_128_64(rst=None)
disp.begin()
disp.clear()
disp.display()

# Create blank image for drawing with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some text.
font = ImageFont.load_default()
draw.text((0, 0), "Hello, Raspberry Pi!", font=font, fill=255)

# Display image.
disp.image(image)
disp.display()
