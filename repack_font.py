import codecs
from PIL import Image
from hacktools import common, ws
import game


def run(data):
    fontfile = data + "font.png"
    fontconfigfile = data + "fontconfig.txt"
    infont = data + "font_output.png"
    outfont = data + "font_input.png"
    outtable = data + "table.txt"
    bankfile = data + "repack/bank_10.bin"

    common.logMessage("Repacking font ...")
    # List of characters and positions in the font.png file
    chars = {}
    positions = {}
    with codecs.open(fontconfigfile, "r", "utf-8") as f:
        fontconfig = common.getSection(f, "")
        x = 0
        for c in fontconfig:
            chars[c] = int(fontconfig[c][0])
            positions[c] = x
            if chars[c] > 7:
                x += 15
            else:
                x += 7
    glyphs = game.readFontGlyphs(fontconfigfile)
    skipcodes = [0x0, 0x40, 0x80, 0xc0]

    # Open the images
    img = Image.open(infont).convert("RGB")
    pixels = img.load()
    font = Image.open(fontfile).convert("RGB")
    fontpixels = font.load()

    # Generate the image and table
    fontx = 0
    fonty = 0xc0 * 16 + 1
    fontwidths = []
    x = 0x20
    tablestr = ""
    for item in glyphs:
        while x in skipcodes:
            fontx += 16
            if fontx == 16 * 4:
                fontx = 0
                fonty += 16
            x += 1
            fontwidths.append(0)
        for i2 in range(15 if chars[item] > 7 else 7):
            for j2 in range(15):
                pixels[fontx + i2, fonty + j2] = fontpixels[positions[item] + i2, j2]
        if chars[item] <= 7:
            for i2 in range(8):
                for j2 in range(15):
                    pixels[fontx + 7 + i2, fonty + j2] = fontpixels[positions[" "], j2]
        fontwidths.append(chars[item] + 1)
        fontx += 16
        if fontx == 16 * 4:
            fontx = 0
            fonty += 16
        tablestr += (item + "=" + common.toHex(x) + "\n")
        x += 1
        if fonty >= img.height:
            break
    with codecs.open(outtable, "w", "utf-8") as f:
        f.write(tablestr)
    img.save(outfont, "PNG")

    # Put the font back in the bank and set the font widths
    with common.Stream(bankfile, "rb+") as f:
        ws.repackImage(f, outfont, 16 * 4, 16 * 244)
        f.seek((0xc0 * 4) * 64)
        for i in range(len(fontwidths)):
            if 0x20 + i not in skipcodes:
                f.writeByte(fontwidths[i])
            else:
                f.seek(1, 1)
            f.seek(63, 1)

    common.logMessage("Done!")
