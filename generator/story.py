"""Erzeugt aus einem 4:5-Bild (1080x1350) eine 9:16-Story (1080x1920).
Aufruf: python3 generator/story.py images/<datei>.jpg   ->  stories/<datei>.jpg"""
import sys
from PIL import Image
src = sys.argv[1]
im = Image.open(src).convert('RGB')
c = Image.new('RGB', (1080, 1920), im.getpixel((20, 20)))
c.paste(im, (0, 285))
c.paste(Image.new('RGB', (1080, 285), im.getpixel((20, 1340))), (0, 1635))
out = src.replace('images/', 'stories/')
c.save(out, 'JPEG', quality=90, optimize=True, progressive=True)
print(out)
