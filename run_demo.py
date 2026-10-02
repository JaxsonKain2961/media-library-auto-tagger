import json
import os
import struct
import zlib

from src.media_tagger import InfraiClient, MediaTagger


def demo_png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
            + chunk(b"IEND", b""))


def main() -> None:
    client = InfraiClient(os.environ.get("INFRAI_API_KEY"))
    result = MediaTagger(client).tag_asset("concert_stage.png", demo_png())
    print(json.dumps({"image_id": result.image_id, "filename": result.filename, "tags": result.tags}))


if __name__ == "__main__":
    main()
