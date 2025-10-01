import unittest

from app.agents.wingman import wingman


class WingmanTipTests(unittest.TestCase):
    def test_deduplication_and_anchor_role_tips(self):
        reasons = ["Great same city vibes", "Anchor overlap", "Anchor overlap"]
        flags = [
            {"type": "role_lifestyle_gap"},
            {"type": "anchor_commute_heavy"},
            {"type": "anchor_commute_heavy"},
        ]
        profile = {"role": "student", "anchor_location": {"label": "FAST NUCES"}}
        other = {"role": "professional", "anchor_location": {"label": "Packages Mall"}}

        tips = wingman(reasons, flags, profile=profile, other=other)

        self.assertEqual(len(tips), len(set(tips)), "Wingman tips should be de-duplicated")
        self.assertTrue(any("FAST NUCES" in t for t in tips), "Anchor labels should be surfaced")
        self.assertTrue(any("commute" in t.lower() for t in tips), "Commute mitigation should appear")
        self.assertTrue(
            any("calendar" in t.lower() or "routines" in t.lower() for t in tips),
            "Role lifestyle gap mitigation expected",
        )


if __name__ == "__main__":
    unittest.main()
