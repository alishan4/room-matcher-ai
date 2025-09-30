from typing import List, Dict
import datetime

def generate_compact(profile_a: Dict, profile_b: Dict, reasons: List[str], conflicts: List[Dict]) -> Dict:
    """
    Drafts a roommate compact from match data.
    In production: upload to Google Docs/Drive, share link.
    """
    text_lines = []
    text_lines.append("Roommate Compact / روم میٹ معاہدہ")
    text_lines.append(f"Date: {datetime.date.today().isoformat()}")
    text_lines.append(f"Between: {profile_a.get('name')} and {profile_b.get('name')}")
    text_lines.append("")
    text_lines.append("✔ Why this works:")
    for r in reasons[:3]:
        text_lines.append(f"- {r}")
    text_lines.append("")
    text_lines.append("⚠ Potential conflicts:")
    for f in conflicts:
        text_lines.append(f"- {f.get('details','')}")

    compact_text = "\n".join(text_lines)
    return {
        "title": "Roommate Compact",
        "participants": [profile_a.get("id"), profile_b.get("id")],
        "content": compact_text,
        "pdf_url": None  # placeholder: link after Google Docs integration
    }
