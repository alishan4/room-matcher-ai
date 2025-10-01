import unittest

from app.agents.red_flag import red_flags


class RedFlagRuleTests(unittest.TestCase):
    def _anchors(self, lat_a, lon_a, lat_b, lon_b, label_a="Campus", label_b="Tech Park"):
        a = {
            "role": "student",
            "anchor_location": {"lat": lat_a, "lng": lon_a, "label": label_a},
        }
        b = {
            "role": "professional",
            "anchor_location": {"lat": lat_b, "lng": lon_b, "label": label_b},
        }
        return red_flags(a, b)

    def test_role_lifestyle_gap_flagged_with_medium_severity(self):
        flags = red_flags(
            {"role": "student"},
            {"role": "professional"},
        )
        role_flags = [f for f in flags if f["type"] == "role_lifestyle_gap"]
        self.assertTrue(role_flags, "Expected role_lifestyle_gap flag to trigger")
        self.assertTrue(all(f["severity"] == "medium" for f in role_flags))
        self.assertTrue(any("student" in f["details"].lower() for f in role_flags))

    def test_anchor_commute_notice_low_severity(self):
        # ~15 km apart
        flags = self._anchors(31.5, 74.3, 31.63, 74.45)
        commute_flag = next(f for f in flags if f["type"] == "anchor_commute_notice")
        self.assertEqual(commute_flag["severity"], "low")
        self.assertIn("PKR", commute_flag["details"])

    def test_anchor_commute_heavy_medium_severity(self):
        # ~26 km apart
        flags = self._anchors(31.5, 74.3, 31.74, 74.34)
        commute_flag = next(f for f in flags if f["type"] == "anchor_commute_heavy")
        self.assertEqual(commute_flag["severity"], "medium")
        self.assertIn("PKR", commute_flag["details"])

    def test_anchor_too_far_high_severity(self):
        # ~75 km apart
        flags = self._anchors(31.5, 74.3, 32.1, 75.2)
        commute_flag = next(f for f in flags if f["type"] == "anchor_too_far")
        self.assertEqual(commute_flag["severity"], "high")
        self.assertIn("PKR", commute_flag["details"])

    def test_anchor_city_mismatch_uses_labels(self):
        flags = red_flags(
            {
                "anchor_location": {"lat": 31.5, "lng": 74.3, "label": "Lahore, PK"},
            },
            {
                "anchor_location": {"lat": 33.7, "lng": 73.1, "label": "Islamabad, PK"},
            },
        )
        city_flags = [f for f in flags if f["type"] == "anchor_city_mismatch"]
        self.assertTrue(city_flags)
        self.assertTrue(all("lahore" in f["details"].lower() for f in city_flags))


if __name__ == "__main__":
    unittest.main()
