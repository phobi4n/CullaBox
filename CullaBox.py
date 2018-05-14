#!/usr/bin/python3

import sys

if sys.version_info[1] < 4:
    print("Culla requires Python 3.4 or later.")
    sys.exit(1)

import os
import os.path
import subprocess
import time
import colorsys
import dbus
from collections import namedtuple
from PIL import Image
import array


# https://github.com/obskyr/colorgram.py ------------------------
ARRAY_DATATYPE = 'l'

Rgb = namedtuple('Rgb', ('r', 'g', 'b'))
Hsl = namedtuple('Hsl', ('h', 's', 'l'))

class Color(object):
    def __init__(self, r, g, b, proportion):
        self.rgb = Rgb(r, g, b)
        self.proportion = proportion

    def __repr__(self):
        return "<colorgram.py Color: {}, {}%>".format(
            str(self.rgb), str(self.proportion * 100))

    @property
    def hsl(self):
        try:
            return self._hsl
        except AttributeError:
            self._hsl = Hsl(*hsl(*self.rgb))
            return self._hsl

def extract(f, number_of_colors):
    image = Image.open(f)
    image.thumbnail((256,256))

    if image.mode not in ('RGB', 'RGBA', 'RGBa'):
        image = image.convert('RGB')

    samples = sample(image)
    used = pick_used(samples)
    used.sort(key=lambda x: x[0], reverse=True)
    return get_colors(samples, used, number_of_colors)

def sample(image):
    top_two_bits = 0b11000000

    sides = 1 << 2 # Left by the number of bits used.
    cubes = sides ** 7

    samples = array.array(ARRAY_DATATYPE, (0 for _ in range(cubes)))
    width, height = image.size

    pixels = image.load()
    for y in range(height):
        for x in range(width):
            # Pack the top two bits of all 6 values into 12 bits.
            # 0bYYhhllrrggbb - luminance, hue, luminosity, red, green, blue.

            r, g, b = pixels[x, y][:3]
            h, s, l = hsl(r, g, b)
            # Standard constants for converting RGB to relative luminance.
            Y = int(r * 0.2126 + g * 0.7152 + b * 0.0722)

            # Everything's shifted into place from the top two
            # bits' original position - that is, bits 7-8.
            packed  = (Y & top_two_bits) << 4
            packed |= (h & top_two_bits) << 2
            packed |= (l & top_two_bits) << 0

            packed *= 4
            samples[packed]     += r
            samples[packed + 1] += g
            samples[packed + 2] += b
            samples[packed + 3] += 1
    return samples

def pick_used(samples):
    used = []
    for i in range(0, len(samples), 4):
        count = samples[i + 3]
        if count:
            used.append((count, i))
    return used

def get_colors(samples, used, number_of_colors):
    pixels = 0
    colors = []
    number_of_colors = min(number_of_colors, len(used))

    for count, index in used[:number_of_colors]:
        pixels += count

        color = Color(
            samples[index]     // count,
            samples[index + 1] // count,
            samples[index + 2] // count,
            count
        )

        colors.append(color)
    for color in colors:
        color.proportion /= pixels
    return colors

def hsl(r, g, b):
    # This looks stupid, but it's way faster than min() and max().
    if r > g:
        if b > r:
            most, least = b, g
        elif b > g:
            most, least = r, g
        else:
            most, least = r, b
    else:
        if b > g:
            most, least = b, r
        elif b > r:
            most, least = g, r
        else:
            most, least = g, b

    l = (most + least) >> 1

    if most == least:
        h = s = 0
    else:
        diff = most - least
        if l > 127:
            s = diff * 255 // (510 - most - least)
        else:
            s = diff * 255 // (most + least)

        if most == r:
            h = (g - b) * 255 // diff + (1530 if g < b else 0)
        elif most == g:
            h = (b - r) * 255 // diff + 510
        else:
            h = (r - g) * 255 // diff + 1020
        h //= 6

    return h, s, l


#---- CullaBox functions ----------------------------------------
def write_openbox_theme(high, med, low, grad):
    try:
        with open(os.path.expanduser(\
            '~/.local/share/CullaBox/themerc')) as f:
            theme = f.read()
    except:
        fatal("Unable to open Openbox theme asset.")

    theme = theme.replace("TEMPLATE1", high)
    theme = theme.replace("TEMPLATE2", med)
    theme = theme.replace("TEMPLATE3", low)
    theme = theme.replace("TEMPLATE4", grad)

    try:
        with open(os.path.expanduser(\
            '~/.themes/CullaBox/openbox-3/themerc'), 'w') as f:
            f.write(theme)
    except:
        fatal("Unable to write Openbox themerc.")

    subprocess.run(['openbox', '--reconfigure'])

def write_tint2_theme(high, med, low, fg, min):
    try:
        with open(os.path.expanduser(\
            '~/.local/share/CullaBox/tint2rc')) as f:
            theme = f.read()
    except:
        fatal("Unable to open tint2 theme asset.")

    theme = theme.replace("HIGH", high)
    theme = theme.replace("MED", med)
    theme = theme.replace("LOW", low)
    theme = theme.replace("FG", fg)
    theme = theme.replace("MIN", min)

    try:
        with open(os.path.expanduser(\
            '~/.config/tint2/tint2rc'), 'w') as f:
            f.write(theme)
    except:
        fatal("Unable to write tint2 themerc.")

    subprocess.run(['killall', '-s10', 'tint2'])

def fatal(message):
    print (message)
    sys.exit(1)

#---- CullaBox --------------------------------------------------
# Use getbg to copy the root window image to tmp.jpg
tmp_image = os.path.expanduser('~/.local/share/CullaBox/tmp.jpg')
subprocess.run(['getbg', tmp_image])

if not os.path.isfile(tmp_image):
    fatal("Could not create a copy of the root window.")

# Get three colours from temp image then delete it
colors_colorgram = extract(tmp_image, 3)
os.remove(tmp_image)

# Get the darkest of our three colours
l = 1.0
h = 1.0
s = 1.0

for i in colors_colorgram:
    h_tmp, l_tmp, s_tmp = colorsys.rgb_to_hls(i.rgb.r/255, i.rgb.g/255, i.rgb.b/255)
    
    if l_tmp <= l:
        h = h_tmp
        l = l_tmp
        s = s_tmp

#Default text colour
foreground = "#f9f9f9"

#Minimised taskbar
minimised_task = "#1f1f1f"

#Lightness threshold for dark text
if l > 0.62:
    foreground = "#1f1f1f"
    light1 = 0.0
    light2 = 0.0
    minimised_task = "#f9f9f9"

#Constant lightness and saturation per output
lightness_high = 0.85
lightness_med = 0.45
lightness_low = l
sat_high = 0.9
sat_med = 0.45
sat_low = s

#Check for monochrome
if s < 0.06:
    sat_high = 0.0
    sat_med = 0.0
    sat_low = 0.0

#Low
r2,g2,b2 = colorsys.hls_to_rgb(h, lightness_low, sat_low)
r2 = int(r2 * 255)
g2 = int(g2 * 255)
b2 = int(b2 * 255)

#High
r3,g3,b3 = colorsys.hls_to_rgb(h, lightness_high, sat_high)
r3 = int(r3 * 255)
g3 = int(g3 * 255)
b3 = int(b3 * 255)

#Medium
r4,g4,b4 = colorsys.hls_to_rgb(h, lightness_med, sat_med)
r4 = int(r4 * 255)
g4 = int(g4 * 255)
b4 = int(b4 * 255)

#Gradient Stop
r5,g5,b5 = colorsys.hls_to_rgb(h, lightness_med - 0.1, sat_med + 0.1)
r5 = int(r5 * 255)
g5 = int(g5 * 255)
b5 = int(b5 * 255)

hex_high = f'#{r3:02x}{g3:02x}{b3:02x}'
hex_med = f'#{r4:02x}{g4:02x}{b4:02x}'
hex_low = f'#{r2:02x}{g2:02x}{b2:02x}'
hex_grad = f'#{r5:02x}{g5:02x}{b5:02x}'

write_openbox_theme(hex_high, hex_med, hex_low, hex_grad)
write_tint2_theme(hex_high, hex_med, hex_low, foreground, minimised_task)
sys.exit(0)

#------------------------------------
