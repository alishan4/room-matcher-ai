# app/utils/num.py
import re
from typing import Optional, Any

def as_int(x: Any) -> Optional[int]:
    """Convert strings like '18k'/'18,000' or numbers to int; else None."""
    if x is None:
        return None
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, (int, float)):
        return int(x)
    if isinstance(x, str):
        s = x.strip().lower()
        m = re.match(r"([\d,._ ]+)\s*k$", s)
        if m:
            base = re.sub(r"[,_ ]", "", m.group(1))
            try:
                return int(base) * 1000
            except:
                return None
        s = re.sub(r"[,_ ]", "", s)
        if s.isdigit():
            try:
                return int(s)
            except:
                return None
    return None
