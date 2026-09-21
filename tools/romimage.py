"""把一个十六进制镜像（一行一个 32 位字）写成 hwsrc/RomImage.bs。

镜像是构建时的常数，进 BH 包之后由 RomTable.fill 在编译期补零、查长度；换镜像就是重跑这个脚本，
生成产物的摘要随之变，价目表要重测，这正是想要的：换镜像就是换了逻辑。

`python3 tools/romimage.py image/boot.hex > hwsrc/RomImage.bs`
"""
import pathlib
import sys

src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "image/boot.hex")
words = []
for n, line in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
    s = line.split("#", 1)[0].strip()
    if not s:
        continue
    v = int(s, 16)
    if not 0 <= v < 1 << 32:
        raise SystemExit(f"{src}:{n}: {s} 不是 32 位字")
    words.append(v)

body = "".join(f"  Cons 0x{w:08X} (\n" for w in words) + "  Nil" + ")" * len(words)
print(f"""package RomImage where

-- 由 tools/romimage.py 从 {src.as_posix()} 生成，勿手改。

image :: List (Bit 32)
image =
{body}""")
