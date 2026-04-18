import unittest

from jedeschule.fallback_school_id import (
    baden_wuerttemberg_school_id,
    km_grid_indices,
    normalize_address_for_id,
    normalize_school_name_for_id,
    normalize_zip_for_id,
    stable_no_coord_fallback_id,
    stable_fallback_id,
)


class TestFallbackSchoolId(unittest.TestCase):
    def test_km_grid_nearby_same_cell(self):
        """Points a few hundred metres apart stay in the same ~1 km cell."""
        self.assertEqual(
            km_grid_indices(48.0001, 9.0001),
            km_grid_indices(48.0004, 9.0004),
        )

    def test_name_normalization_collapses_punctuation(self):
        self.assertEqual(
            normalize_school_name_for_id("  ABC – Test  "),
            "abc test",
        )

    def test_address_and_zip_normalization(self):
        self.assertEqual(normalize_address_for_id("Königstr. 49"), "konigstr 49")
        self.assertEqual(normalize_zip_for_id(" 70 173 "), "70173")

    def test_stable_fallback_deterministic(self):
        a = stable_fallback_id("BW", 48.725, 9.307, "Musterschule", "education")
        b = stable_fallback_id("BW", 48.725, 9.307, "Musterschule", "education")
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("BW-FB-"))

    def test_bw_prefers_disch(self):
        sid = baden_wuerttemberg_school_id(
            "04144952",
            48.0,
            9.0,
            "X",
            "education",
            "A 1",
            "70173",
            "uuid-here",
        )
        self.assertEqual(sid, "BW-04144952")

    def test_bw_fb_without_disch(self):
        sid = baden_wuerttemberg_school_id(
            None,
            48.725,
            9.307,
            "Musterschule",
            "education",
            "Musterweg 1",
            "70173",
            "wfs-uuid",
        )
        self.assertTrue(sid.startswith("BW-FB-"))

    def test_bw_fba_without_coords(self):
        sid = baden_wuerttemberg_school_id(
            None,
            None,
            None,
            "Musterschule",
            "education",
            "Musterweg 1",
            "70173",
            "wfs-uuid",
        )
        self.assertTrue(sid.startswith("BW-FBA-"))

    def test_stable_no_coord_fallback_guardrails(self):
        self.assertIsNone(
            stable_no_coord_fallback_id("BW", "", "education", "Musterweg 1", "70173")
        )
        self.assertIsNone(
            stable_no_coord_fallback_id("BW", "Musterschule", "education", "", "")
        )

    def test_bw_uuid_only_without_coords(self):
        sid = baden_wuerttemberg_school_id(
            None,
            None,
            None,
            "X",
            "y",
            "",
            "",
            "abc-123",
        )
        self.assertEqual(sid, "BW-UUID-abc-123")


if __name__ == "__main__":
    unittest.main()
