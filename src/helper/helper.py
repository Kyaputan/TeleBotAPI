import logging
from pathlib import Path
import base64
from typing import Literal

logger = logging.getLogger(__name__)


    
def to_data_url(input_path: str | Path, mime: Literal["image/jpeg","image/png","image/webp"] | None = None) -> str:
    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError(f"ไม่พบไฟล์ภาพ: {p.resolve()}")
    ext = p.suffix.lower()
    if mime is None:
        mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }.get(ext, "image/jpeg")
    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"