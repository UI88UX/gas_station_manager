from PIL import Image, ImageDraw

# ساخت یک آیکون ساده 32x32
img = Image.new('RGB', (32, 32), color='blue')
draw = ImageDraw.Draw(img)
draw.circle([8, 8, 24, 24], fill='red')
img.save('gas_station.ico', format='ICO')