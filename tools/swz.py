"""PS2 텍스처 스위즐(PSMT8 / PSMT4) 풀기·걸기 — 표준 unswizzle 공식."""
import numpy as np
def _map8(w, h):
    y, x = np.mgrid[0:h, 0:w]
    block = (y & ~0xf) * w + (x & ~0xf) * 2
    swap = (((y + 2) >> 2) & 1) * 4
    posy = (((y & ~3) >> 1) + (y & 1)) & 7
    col = posy * w * 2 + ((x + swap) & 7) * 4
    byte = ((y >> 1) & 1) + ((x >> 2) & 2)
    return block + col + byte
def unswizzle8(buf, w, h):
    return np.frombuffer(buf, np.uint8)[_map8(w, h)]
def swizzle8(img):
    h, w = img.shape
    out = np.zeros(w*h, np.uint8); out[_map8(w, h)] = img; return out.tobytes()

# --- 4bpp: CT32(w/2 x h/4)로 올린 GS 메모리를 PSMT4 로 읽는 방식 ---
import functools
@functools.lru_cache(maxsize=64)
def _map4(w, h):
    import gsmem
    bw32 = max(1, (w // 2) // 64)
    W32, H32 = w // 2, h // 4
    a32 = np.array([[gsmem.addr32(0, bw32, x, y) for x in range(W32)] for y in range(H32)], np.int64)   # CT32 픽셀 i 의 바이트 주소
    a4 = np.array([[gsmem.addr4(0, bw32 * 2, x, y) for x in range(w)] for y in range(h)], np.int64)     # 니블 주소
    return a32, a4
def unswizzle4(buf, w, h):
    a32, a4 = _map4(w, h)
    size = int(max(a32.max(), (a4.max() >> 1)) + 4)
    vm = np.zeros(size, np.uint8)
    src = np.frombuffer(buf[:w * h // 2], np.uint8).reshape(-1, 4)
    flat = a32.ravel()
    for k in range(4): vm[flat + k] = src[:, k]
    b = vm[a4 >> 1]
    return np.where(a4 & 1, b >> 4, b & 15).astype(np.uint8)
def swizzle4(img):
    h, w = img.shape
    a32, a4 = _map4(w, h)
    size = int(max(a32.max(), (a4.max() >> 1)) + 4)
    vm = np.zeros(size, np.uint8)
    lo = (a4 & 1) == 0
    byte = a4 >> 1
    np.add.at(vm, byte[lo], img[lo] & 15)
    np.add.at(vm, byte[~lo], (img[~lo] & 15) << 4)
    flat = a32.ravel()
    return np.stack([vm[flat + k] for k in range(4)], 1).ravel().tobytes()
