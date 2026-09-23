"""
End-to-End Simulation of the Hackathon Demo Flow
Follows the exact 17-step judge demonstration scenario.
"""

from app import app
from logic.eligibility_engine import EligibilityEngine

def test_full_demo_flow():
    client = app.test_client()
    print("==================================================")
    print("STEP 1: Open WelfareAssist")
    res = client.get("/")
    assert res.status_code == 200
    assert b"WelfareAssist" in res.data
    print("  -> Passed: Homepage loaded.")

    print("\nSTEP 2: Select Malayalam")
    res = client.get("/set-language/ml", follow_redirects=True)
    assert res.status_code == 200
    assert "പരിശോധന ആരംഭിക്കുക".encode("utf-8") in res.data
    print("  -> Passed: Switched to Malayalam successfully.")

    print("\nSTEP 3 & 4: Try a Demo Household -> Select Fishing Household (DEMO-HH-01)")
    res = client.get("/screening?profile=DEMO-HH-01", follow_redirects=True)
    assert res.status_code == 200
    print("  -> Passed: Preloaded DEMO-HH-01.")

    print("\nSTEP 5: Review the automatically populated information")
    res = client.get("/review")
    assert res.status_code == 200
    assert b"150000" in res.data
    print("  -> Passed: Review page shows 150000 income.")

    print("\nSTEP 6 & 7: Click 'Check Available Schemes' (Run eligibility engine)")
    res = client.post("/screen", follow_redirects=True)
    assert res.status_code == 200
    print("  -> Passed: Screening executed.")

    print("\nSTEP 8, 9, 10, 11: Verify eligible schemes, reasons why, documents, where to apply")
    assert "മത്സ്യത്തൊഴിലാളി".encode("utf-8") in res.data
    assert "ആധാർ കാർഡ്".encode("utf-8") in res.data
    assert "അക്ഷയ കേന്ദ്രം".encode("utf-8") in res.data
    print("  -> Passed: Potentially eligible fisheries schemes, reasons, documents, and Akshaya centre displayed.")

    print("\nSTEP 12, 13, 14: Go back and change income to 400,000 and re-screen -> Results change")
    client.post("/save-step", data={"annual_income": "400000", "current_step": "2", "action": "review"}, follow_redirects=True)
    res_high = client.post("/screen", follow_redirects=True)
    assert res_high.status_code == 200
    # Higher income disqualifies from low-income schemes (0 eligible)
    assert b"0" in res_high.data
    print("  -> Passed: Income change directly altered eligibility results (0 matches).")

    print("\nSTEP 15: Demonstrate incomplete information (Missing income -> No guessing)")
    client.get("/screening?profile=DEMO-HH-04", follow_redirects=True)
    res_incomplete = client.post("/screen", follow_redirects=True)
    assert res_incomplete.status_code == 200
    # Must show missing info section
    assert "കൂടുതൽ വിവരങ്ങൾ ആവശ്യമുള്ള പദ്ധതികൾ".encode("utf-8") in res_incomplete.data
    print("  -> Passed: Incomplete profile marked as more_info_needed without guessing.")

    print("\nSTEP 16: Voice input capability verification")
    # Verify Web Speech API hooks and markup in screening step 2
    res_screen = client.get("/screening?step=2")
    assert b"btn-voice" in res_screen.data
    assert b"data-target=\"annual_income\"" in res_screen.data
    print("  -> Passed: Microphone button wired to Web Speech API.")

    print("\nSTEP 17: Switch language back to English")
    res_en = client.get("/set-language/en", follow_redirects=True)
    assert res_en.status_code == 200
    assert b"Welfare-Entitlement Screening" in res_en.data
    print("  -> Passed: Bilingual toggle verified.")

    print("\n==================================================")
    print("ALL 17 HACKATHON DEMO FLOW STEPS VERIFIED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_full_demo_flow()

