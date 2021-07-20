from PIL import Image
import numpy as np
from chacha import chacha20_byte_generator

im = np.array(Image.open('lena_enc.png'))

shape = im.shape

im = im.reshape(-1)

keystream = np.fromiter(chacha20_byte_generator(bytes(32), 1, bytes(12)), np.uint8, count=im.size)

im = np.bitwise_xor(im, keystream)

im = im.reshape(shape)

pil_img = Image.fromarray(im)
print(pil_img.mode)
# RGB

pil_img.save('lena_deenc.png')