# peek_file.py
import chardet

path = "No start snapshot.xls"

# Read first 200 bytes to see if it’s binary or text
with open(path, "rb") as f:
    start = f.read(200)
print("First 300 bytes:", start[:300])

# Detect likely text encoding
raw = open(path, "rb").read(20000)
print("Detected encoding:", chardet.detect(raw))
