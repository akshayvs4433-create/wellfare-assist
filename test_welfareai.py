"""
WelfareAssist - Automated Verification Test Suite
Tests resource pack integrity, transparent eligibility engine, Flask web routes, and database logging.
"""

import unittest
import json
import os
from logic.eligibility_engine import EligibilityEngine, load_json_file
from database.db import log_screening_event, get_screening_stats, init_db
from app import app


class TestDemoResourcePack(unittest.TestCase):
    """Verifies simulated demo resource pack structure and content."""

    def test_schemes_count_and_fields(self):
        schemes = load_json_file("schemes.json")
        self.assertGreaterEqual(len(schemes), 10, "Resource pack must contain at least 10 demo schemes")
        for s in schemes:
            self.assertIn("id", s)
            self.assertIn("name", s)
            self.assertIn("target_group", s)
            self.assertIn("description", s)
            self.assertIn("eligibility_rules", s)
            self.assertIn("required_documents", s)
            self.assertIn("application_location", s)
            self.assertIn("application_method", s)
            self.assertIn("what_to_do_next", s)

    def test_household_profiles(self):
        profiles = load_json_file("household_profiles.json")
        self.assertGreaterEqual(len(profiles), 4, "Must provide sample demo household profiles")
        # Ensure fisher and plantation profiles exist
        occupations = [p["data"]["occupation"] for p in profiles]
        self.assertIn("fisher", occupations)
        self.assertIn("plantation", occupations)

    def test_akshaya_centres(self):
        centres = load_json_file("akshaya_centres.json")
        self.assertGreaterEqual(len(centres), 5)
        districts = [c["district"] for c in centres]
        self.assertIn("Ernakulam", districts)
        self.assertIn("Wayanad", districts)

    def test_terminology(self):
        terms = load_json_file("terminology.json")
        self.assertIn("app_name", terms)
        self.assertIn("en", terms["app_name"])
        self.assertIn("ml", terms["app_name"])


class TestEligibilityEngine(unittest.TestCase):
    """Tests deterministic screening logic and strict no-guessing policy."""

    def setUp(self):
        self.engine = EligibilityEngine()

    def test_fishing_household(self):
        household = {
            "occupation": "fisher",
            "annual_income": 150000,
            "age": 42,
            "family_size": 4,
            "district": "Ernakulam",
            "gender": "male",
            "has_disability": "no"
        }
        res = self.engine.screen_household(household, lang="en")
        self.assertGreaterEqual(res["summary"]["eligible_count"], 2)
        eligible_ids = [s["id"] for s in res["eligible"]]
        self.assertIn("DEMO-FSH-001", eligible_ids)
        # Check reasons why
        first_scheme = next(s for s in res["eligible"] if s["id"] == "DEMO-FSH-001")
        self.assertGreater(len(first_scheme["reasons_why"]), 0)
        self.assertGreater(len(first_scheme["required_documents"]), 0)

    def test_plantation_household_wayanad(self):
        household = {
            "occupation": "plantation",
            "annual_income": 120000,
            "age": 35,
            "family_size": 3,
            "district": "Wayanad",
            "gender": "female",
            "has_disability": "no"
        }
        res = self.engine.screen_household(household, lang="en")
        self.assertGreaterEqual(res["summary"]["eligible_count"], 3)
        eligible_ids = [s["id"] for s in res["eligible"]]
        self.assertIn("DEMO-PLT-001", eligible_ids)
        self.assertIn("DEMO-PLT-002", eligible_ids)
        self.assertIn("DEMO-PLT-003", eligible_ids)

    def test_high_income_disqualification(self):
        household = {
            "occupation": "fisher",
            "annual_income": 400000,
            "age": 48,
            "family_size": 5,
            "district": "Alappuzha",
            "gender": "male",
            "has_disability": "no"
        }
        res = self.engine.screen_household(household, lang="en")
        # Income exceeds 2.5L max limit across fisheries schemes
        self.assertEqual(res["summary"]["eligible_count"], 0)
        self.assertGreater(res["summary"]["not_eligible_count"], 0)
        # Verify reason failed is clear
        first_fail = res["not_eligible"][0]
        self.assertTrue(any("exceeds" in r or "കൂടുതലാണ്" in r for r in first_fail["reasons_failed"]))

    def test_incomplete_profile_never_guesses(self):
        """CRITICAL REQUIREMENT: If income is missing, do NOT guess. Mark more_info_needed."""
        household = {
            "occupation": "plantation",
            "annual_income": None,  # Intentionally missing
            "age": 40,
            "family_size": 4,
            "district": "Idukki",
            "gender": "male",
            "has_disability": "no"
        }
        res = self.engine.screen_household(household, lang="en")
        self.assertGreater(res["summary"]["more_info_count"], 0)
        # Find a plantation scheme in more_info_needed
        more_info_ids = [s["id"] for s in res["more_info_needed"]]
        self.assertIn("DEMO-PLT-001", more_info_ids)
        target = next(s for s in res["more_info_needed"] if s["id"] == "DEMO-PLT-001")
        self.assertIn("annual_income", target["missing_fields"])

    def test_senior_disability_screening(self):
        household = {
            "occupation": "fisher",
            "annual_income": 95000,
            "age": 63,
            "family_size": 2,
            "district": "Kollam",
            "gender": "male",
            "has_disability": "yes"
        }
        res = self.engine.screen_household(household, lang="en")
        eligible_ids = [s["id"] for s in res["eligible"]]
        self.assertIn("DEMO-SHR-001", eligible_ids)
        self.assertIn("DEMO-SHR-002", eligible_ids)

    def test_malayalam_output(self):
        household = {
            "occupation": "fisher",
            "annual_income": 150000,
            "age": 42,
            "family_size": 4,
            "district": "Ernakulam"
        }
        res = self.engine.screen_household(household, lang="ml")
        self.assertGreater(len(res["eligible"]), 0)
        # Check Malayalam text in scheme name
        first_scheme = res["eligible"][0]
        self.assertTrue(any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in first_scheme["name"]))

    def test_all_curated_test_cases(self):
        cases = load_json_file("test_cases.json")
        for tc in cases:
            tcid = tc["id"]
            res = self.engine.screen_household(tc["input"])
            if "expected_eligible_min" in tc:
                self.assertGreaterEqual(
                    res["summary"]["eligible_count"], tc["expected_eligible_min"],
                    f"{tcid}: eligible count too low"
                )
            if "expected_eligible_ids" in tc:
                actual_ids = [s["id"] for s in res["eligible"]]
                for eid in tc["expected_eligible_ids"]:
                    self.assertIn(eid, actual_ids, f"{tcid}: expected {eid} to be eligible")
            if "expected_eligible_count" in tc:
                self.assertEqual(
                    res["summary"]["eligible_count"], tc["expected_eligible_count"],
                    f"{tcid}: count mismatch"
                )
            if "expected_more_info_min" in tc:
                self.assertGreaterEqual(
                    res["summary"]["more_info_count"], tc["expected_more_info_min"],
                    f"{tcid}: more_info_count too low"
                )
            if "expected_more_info_fields" in tc:
                all_missing = set()
                for s in res["more_info_needed"]:
                    all_missing.update(s.get("missing_fields", []))
                for mf in tc["expected_more_info_fields"]:
                    self.assertIn(mf, all_missing, f"{tcid}: expected {mf} missing")


class TestFlaskApplication(unittest.TestCase):
    """Tests Flask web endpoints, session flows, and JSON API."""

    def setUp(self):
        self.client = app.test_client()

    def test_homepage(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"WelfareAssist", res.data)

    def test_screening_steps(self):
        for step in [1, 2, 3, 4]:
            res = self.client.get(f"/screening?step={step}")
            self.assertEqual(res.status_code, 200)

    def test_preloaded_demo_profile(self):
        res = self.client.get("/screening?profile=DEMO-HH-01", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        # Review answers should now be populated
        res_review = self.client.get("/review")
        self.assertEqual(res_review.status_code, 200)
        self.assertIn(b"150000", res_review.data)

    def test_api_screen_endpoint(self):
        payload = {
            "occupation": "fisher",
            "annual_income": 150000,
            "age": 42,
            "family_size": 4,
            "district": "Ernakulam",
            "lang": "en"
        }
        res = self.client.post("/api/screen", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("eligible", data)
        self.assertIn("summary", data)
        self.assertGreater(data["summary"]["eligible_count"], 0)

    def test_language_switch_route(self):
        res = self.client.get("/set-language/ml", follow_redirects=True)
        self.assertEqual(res.status_code, 200)

    def test_open_redirect_prevention(self):
        res = self.client.get("/set-language/en?next=https://malicious-site.com")
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get("Location"), "/")

    def test_invalid_screening_step(self):
        res = self.client.get("/screening?step=invalid")
        self.assertEqual(res.status_code, 200)
        res_overflow = self.client.get("/screening?step=999")
        self.assertEqual(res_overflow.status_code, 200)

    def test_screening_submission_to_results(self):
        """Verifies clicking 'Check Available Schemes' directly displays results without redirecting to home."""
        # 1. Enter household attributes through wizard steps
        self.client.post("/save-step", data={"current_step": "1", "action": "next", "occupation": "plantation"})
        self.client.post("/save-step", data={"current_step": "2", "action": "next", "annual_income": "120000"})
        self.client.post("/save-step", data={"current_step": "3", "action": "next", "age": "35", "family_size": "3", "gender": "female"})
        self.client.post("/save-step", data={"current_step": "4", "action": "review", "district": "Wayanad", "has_disability": "no"})

        # 2. Submit form to /screen
        res = self.client.post("/screen", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        # Must display results page, NOT redirect to home
        self.assertNotIn(b"hero-box", res.data)
        self.assertIn(b"results-container", res.data)
        self.assertIn(b"DEMO-PLT-001", res.data)
        self.assertIn(b"Not Currently Matching Schemes", res.data)
        self.assertIn(b"Download PDF Report", res.data)

    def test_download_report_endpoint(self):
        """Verifies report generation route renders cleanly with print capability."""
        self.client.get("/screening?profile=DEMO-HH-01", follow_redirects=True)
        res = self.client.get("/download-report")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"WelfareAssist", res.data)
        self.assertIn(b"window.print()", res.data)
        self.assertIn(b"DEMO-FSH-001", res.data)


class TestDatabaseAudit(unittest.TestCase):
    """Tests anonymous audit storage."""

    def test_audit_logging(self):
        init_db()
        row_id = log_screening_event(
            occupation="fisher",
            district="Ernakulam",
            eligible_count=3,
            more_info_count=1,
            language="en"
        )
        self.assertGreater(row_id, 0)
        stats = get_screening_stats()
        self.assertGreaterEqual(stats["total_screenings"], 1)


if __name__ == "__main__":
    unittest.main()

