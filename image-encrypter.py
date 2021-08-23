from PIL import Image
import numpy as np
from argon2.low_level import hash_secret_raw, Type

import sys
import os
from secrets import token_bytes
from math import ceil

from chacha import chacha20_byte_generator

if sys.argv[1] == "help" or sys.argv[1] == "-h" or sys.argv[1] == "--help":
    print(f"Usage for {sys.argv[0]}: [encrypt || decrypt] [photo file] [key]")
    sys.exit()

if len(sys.argv) != 4:
    raise SystemExit(f"Usage for {sys.argv[0]}: [encrypt || decrypt] [photo file] [key]")

try:
    image = Image.open(sys.argv[2])
except FileNotFoundError:
    raise SystemExit(f"{sys.argv[2]} could not be found.")

if image.mode != "RGB" or image.mode != "RGBA":
    image = image.convert("RGBA")

im = np.array(image)

if sys.argv[1] != "encrypt" and sys.argv[1] != "decrypt":
    raise SystemExit(f"Unknown argument {sys.argv[1]}: should be encrypt or decrypt.")

decrypting = sys.argv[1] == "decrypt"

bytes_per_row = 1
for size in im.shape[1:]:
    bytes_per_row *= size
rows_for_nonce = ceil(12 / bytes_per_row)


if decrypting:
    # gets the first 12 bytes of the last rows of the image
    nonce = im[-rows_for_nonce:].tobytes()[:12]
    # and then promptly deletes them
    im = np.delete(im, np.s_[-rows_for_nonce:], axis=0)
else:
    nonce = token_bytes(12)

shape = im.shape

im = im.reshape(-1)

key = hash_secret_raw(os.fsencode(sys.argv[3]), b"nothing up my sleeve", 2, 102400, 8, 32, Type.ID)
keystream = np.fromiter(chacha20_byte_generator(key, 1, nonce), np.uint8, count=im.size)

im = np.bitwise_xor(im, keystream)

if not decrypting:
    meta_data = np.zeros(bytes_per_row * rows_for_nonce, dtype=np.uint8)
    for index, byte in enumerate(nonce):
        meta_data[index] = byte
    im = np.append(im, meta_data)    


im = im.reshape((-1, *shape[1:]))

pil_img = Image.fromarray(im)

pil_img.save(f"{sys.argv[2].rpartition('.')[0]}_{'denc' if decrypting else 'enc'}.png")