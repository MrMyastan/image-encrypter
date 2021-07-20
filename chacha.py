from typing import Generator

def rotate(a: int, b: int) -> int:
    return (((a) << (b)) | ((a) >> (32 - (b)))) & ((2**32) - 1)

def add_mod_32(a: int, b: int) -> int:
    return (a + b) % (2**32)

def quarter_round(state: "list[int]", a: int, b: int, c: int, d: int) -> None:
    state[a] = add_mod_32(state[a], state[b])
    state[d] ^= state[a]
    state[d] = rotate(state[d], 16)

    state[c] = add_mod_32(state[c], state[d])
    state[b] ^= state[c]
    state[b] = rotate(state[b], 12)

    state[a] = add_mod_32(state[a], state[b])
    state[d] ^= state[a]
    state[d] = rotate(state[d], 8)

    state[c] = add_mod_32(state[c], state[d])
    state[b] ^= state[c]
    state[b] = rotate(state[b], 7)

def double_round(state: list) -> None:
    quarter_round(state, 0, 4, 8,12)
    quarter_round(state, 1, 5, 9,13)
    quarter_round(state, 2, 6,10,14)
    quarter_round(state, 3, 7,11,15)
    quarter_round(state, 0, 5,10,15)
    quarter_round(state, 1, 6,11,12)
    quarter_round(state, 2, 7, 8,13)
    quarter_round(state, 3, 4, 9,14)

def ext_int(array: bytes, i: int) -> int:
    return int.from_bytes(array[i * 4:(i * 4) + 4], 'little')

def construct_state(key: bytes, counter: int, nonce: bytes) -> "list[int]":
    state = [
        0x61707865,      0x3320646e,        0x79622d32,        0x6b206574,
        ext_int(key, 0), ext_int(key, 1),   ext_int(key, 2),   ext_int(key, 3),
        ext_int(key, 4), ext_int(key, 5),   ext_int(key, 6),   ext_int(key, 7),
        counter,         ext_int(nonce, 0), ext_int(nonce, 1), ext_int(nonce, 2),
    ]
    return state

def chacha20_block_statewise(initial_state: "list[int]") -> "list[int]":
    state = initial_state.copy()
    for i in range(0, 20, 2):
        double_round(state)
    for i, num in enumerate(initial_state):
        state[i] = add_mod_32(state[i], num)
    return state

def chacha20_block(key: bytes, counter: int, nonce: bytes) -> "list[int]":
    return chacha20_block_statewise(construct_state(key, counter, nonce))

def chacha20_generator(key: bytes, counter: int, nonce: bytes) -> Generator[int, None, None]:
    state = construct_state(key, counter, nonce)
    while state[12] <= (2 ** 32) - 1:
        block = chacha20_block_statewise(state)
        for int in block:
            yield int
        state[12] += 1

def chacha20_byte_generator(key: bytes, counter: int, nonce: bytes) -> Generator[int, None, None]:
    for x in chacha20_generator(key, counter, nonce):
        while x:
            yield (x & 255)
            x = x >> 8

# numpy.fromiter(chacha.chacha20_generator(bytes(32), 1, bytes(12)), numpy.uint32, count=10) 