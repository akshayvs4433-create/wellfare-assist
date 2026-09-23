# WelfareAssist (വെൽഫെയർ Assist)
### Multilingual Welfare-Entitlement Screening Assistant for Plantation & Fishing Families

> **IMPORTANT DISCLAIMER**: The resource pack included in this prototype is **simulated demo data** created for demonstration purposes. It is strictly designed to be replaced with the organiser-provided verified resource pack. Potential eligibility is only a preliminary screening result based on the provided household details and demo rules; it does not guarantee approval or benefits. Final eligibility is determined solely by the concerned authority.

---

## 1. Problem Statement
Plantation labourers (tea, rubber, coffee estate workers) and coastal fishing families in Kerala often miss out on entitled government welfare schemes due to:
- Complex administrative terminology and dispersed scheme guidelines.
- Unclear eligibility thresholds (income limits, age bounds, welfare board registration rules).
- Lack of local language (Malayalam) digital tools tailored for low digital-literacy users.
- Reluctance to use digital tools that demand excessive sensitive personal documentation (e.g. passwords, bank account numbers, Aadhaar numbers) upfront.

## 2. The WelfareAssist Solution
**WelfareAssist** is a transparent, human-centred welfare-entitlement screening assistant. It allows a household to answer a few simple questions (via keyboard or browser voice input in English or Malayalam) and immediately receives:
1. **Potentially Eligible Schemes**: Transparently evaluated without external API dependencies.
2. **"Why This Was Shown"**: Clear, plain-language bullet points explaining every satisfied criterion.
3. **Required Documents Checklist**: Exactly what certificates (income certificate, welfare board passbook) are required before visiting an office.
4. **Where and How to Apply**: Specific local **Akshaya Centres** and departmental sub-offices in their district.
5. **Strict No-Guessing Policy**: If a key piece of information (such as income) is omitted, the engine **never assumes or guesses**; instead, it shows "More information needed" and explains what is missing with a direct 1-click prompt to provide it.
6. **Privacy-by-Design**: Zero passwords, zero bank accounts, zero Aadhaar numbers collected. Household data stays in the browser session.

---

## 3. Technology Stack
- **Backend**: Python 3, Flask
- **Frontend**: Semantic HTML5, accessible Kerala public-service custom CSS, Vanilla JavaScript
- **Voice Recognition**: Browser Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) supporting English (`en-IN`) and Malayalam (`ml-IN`)
- **Data & Configuration**: JSON-based simulated resource pack (`demo_resource_pack/`)
- **Audit Storage**: Lightweight SQLite database (`welfareai.db`) storing anonymous, privacy-safe screening counts (zero PII)
- **Zero Heavy Frameworks**: No React, Next.js, Bootstrap, or Tailwind—fast, lightweight, highly readable, and offline-capable.

---

## 4. Architecture

```
User (Browser / Web Speech API)
  │ (Bilingual UI: EN / ML)
  ▼
Flask Web App (app.py)
  ├── Step-by-Step Screening Questionnaire (Steps 1–4)
  ├── 1-Click Demo Household Loader
  └── Review & Edit Interface
  │
  ▼
Eligibility Engine (logic/eligibility_engine.py)
  ├── Deterministic Rules Evaluator (Match / Disqualify / Insufficient Info)
  ├── Explainability Generator ("Why this was shown")
  ├── Document Checklist Mapper
  └── District Akshaya Centre Locator
  │
  ▼
Simulated Demo Resource Pack (demo_resource_pack/)
  ├── schemes.json (12 demo schemes for fishers and plantation workers)
  ├── household_profiles.json (5 curated test personas)
  ├── akshaya_centres.json (District-level Akshaya directory)
  ├── terminology.json (English & Malayalam dictionary)
  ├── disclaimer.txt
  └── test_cases.json
  │
  ▼
SQLite Database (database/db.py)
  └── Anonymous screening audit log (timestamp, occupation, district, counts)
```

---

## 5. Simulated Demo Resource Pack (`demo_resource_pack/`)

| File | Purpose |
|---|---|
| `schemes.json` | Contains 12 fictional demo schemes covering fisheries, plantations, disability, and elder care with structured eligibility rules, bilingual titles, documents, and next steps. |
| `household_profiles.json` | 5 curated personas for 1-click demonstration during hackathon judging. |
| `akshaya_centres.json` | Directory of simulated Akshaya centres categorized across Kerala districts (Ernakulam, Wayanad, Alappuzha, Kollam, Idukki, Thiruvananthapuram, etc.). |
| `terminology.json` | Comprehensive dictionary of English (`en`) and Malayalam (`ml`) UI strings. |
| `disclaimer.txt` | Official public-service disclaimer text in English and Malayalam. |
| `test_cases.json` | Structured test cases to validate engine rules. |

---

## 6. How the Eligibility Engine Works
The engine (`logic/eligibility_engine.py`) reads `schemes.json` and evaluates each scheme independently:
1. **Explicit Disqualification**: If an applicant fails any known criterion (e.g. occupation is *fisher* but scheme requires *plantation*, or annual income exceeds the maximum threshold), the scheme is placed in `not_eligible` with an explicit reason why.
2. **Missing Information (No Guessing)**: If no criteria are violated, but a required parameter (such as annual income or age) was left blank, the scheme is placed in `more_info_needed`. The engine never assumes a household is low-income.
3. **Potential Match**: If all criteria pass, the scheme is placed in `eligible`. The engine generates plain-language reasons why (e.g. *"Occupation matches target group"*, *"Annual income ₹1,50,000 is within scheme ceiling of ₹1,80,000"*).
4. **Local Akshaya Matching**: Matches the applicant's district to the local Akshaya Centre directory.

---

## 7. How to Run Locally

### Prerequisites
- Python 3.9+ installed.

### Setup and Start
```bash
# 1. Clone or navigate to the project directory
cd welfareassist

# 2. Activate virtual environment (or create one)
source venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Start the Flask application
python3 app.py
```

Open your browser at:
```
http://127.0.0.1:5000
```

---

## 8. How to Run Automated Tests

To run the complete unit test suite (16 tests verifying resource pack, engine logic, Malayalam output, web routes, and audit database):
```bash
python3 -m unittest test_welfareai.py -v
```

To run the end-to-end 17-step hackathon demo flow simulation:
```bash
python3 test_demo_flow.py
```

---

## 9. Hackathon Judge Presentation Script (Step-by-Step)

Follow this exact 2-minute walkthrough to demonstrate the prototype to hackathon judges:

1. **Open Landing Page** (`http://127.0.0.1:5000`):
   - Highlight the clean, calm, human-centred Kerala public-service design (no flashy neon gradients or AI robot badges).
   - Point out the official prototype disclaimer and zero-PII privacy guarantee.
2. **Switch Language to Malayalam**:
   - Click **മലയാളം** in the top navigation.
   - Show that all hero copy, headings, and labels instantly switch to authentic Malayalam.
3. **Click "Try a Demo Household" (ഡെമോ കുടുംബ വിവരങ്ങൾ പരീക്ഷിക്കുക)**:
   - Click the secondary button to open the modal.
   - Select **"Demo Household 1: Coastal Fishing Family"** (Ernakulam, Fisher, Income ₹1,50,000, Age 42, Family 4).
4. **Review Prepopulated Answers**:
   - Show how the 4-step wizard has preloaded the household attributes.
   - Demonstrate the **[Edit]** links for each field.
5. **Click "Check Available Schemes" (ലഭ്യമായ പദ്ധതികൾ പരിശോധിക്കുക)**:
   - The Python eligibility engine executes deterministically.
   - Show the results page:
     - **3 matching fisheries schemes** displayed.
     - **"Why this was shown"**: Expand the bullet points verifying occupation, income threshold, and age brackets.
     - **Documents Checklist**: Aadhaar, Welfare board card, Village income certificate.
     - **Where to Apply**: Shows the Vypin / Fort Kochi Akshaya Centre in Ernakulam with address and working hours.
6. **Demonstrate Answer Modification & Dynamic Recalculation**:
   - Click **"Change Answers & Re-Screen"**.
   - Change annual income from `₹1,50,000` to `₹4,00,000`.
   - Click **Review** &rarr; **Check Available Schemes**.
   - Show that the results immediately update: 0 schemes qualify because income exceeds the ceiling, transparently explaining the failure criteria.
7. **Demonstrate the Strict No-Guessing Policy**:
   - Click "Try a Demo Household" &rarr; select **"Demo Household 4: Incomplete Household (Missing Income)"**.
   - Run screening.
   - Point out the amber **"Schemes needing more information"** section.
   - Highlight that WelfareAssist **refused to guess** income, and gave the user an **[+ Add Household Income]** button.
8. **Demonstrate Voice Input**:
   - In Step 2 or Step 3, click the microphone button (`🎤 Speak`).
   - Speak a number; watch the Web Speech API populate the field automatically for low digital-literacy users.
9. **Explain Architecture & Extensibility**:
   - Explain to the judges that the application is fully decoupled: when the organiser provides the final verified resource pack, only `demo_resource_pack/schemes.json` needs to be swapped out—zero frontend rewrites required.

