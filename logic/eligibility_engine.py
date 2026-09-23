"""
WelfareAssist - Transparent Eligibility Engine
Evaluates household data against simulated demo scheme rules.
Follows a strict no-guessing policy for incomplete information.
"""

import json
import os
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_DIR = os.path.join(BASE_DIR, "demo_resource_pack")


def load_json_file(filename: str) -> Any:
    filepath = os.path.join(PACK_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


class EligibilityEngine:
    def __init__(self, resource_pack_dir: Optional[str] = None):
        self.pack_dir = resource_pack_dir or PACK_DIR
        self.schemes = self._load("schemes.json")
        self.akshaya_centres = self._load("akshaya_centres.json")
        self.terminology = self._load("terminology.json")

    def _load(self, filename: str) -> Any:
        filepath = os.path.join(self.pack_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def reload(self):
        """Reloads the resource pack from disk."""
        self.schemes = self._load("schemes.json")
        self.akshaya_centres = self._load("akshaya_centres.json")
        self.terminology = self._load("terminology.json")

    def get_akshaya_for_district(self, district: Optional[str], lang: str = "en") -> List[Dict[str, Any]]:
        """Finds demo Akshaya centres in or near the user's district."""
        if not district:
            district = "Ernakulam"

        matched = [
            c for c in self.akshaya_centres
            if c.get("district", "").lower() == district.lower()
        ]

        if not matched:
            matched = [c for c in self.akshaya_centres if c.get("district") == "Other"]
            if not matched and self.akshaya_centres:
                matched = [self.akshaya_centres[0]]

        # Format bilingual representation
        results = []
        for c in matched:
            results.append({
                "id": c["id"],
                "district": c["district"],
                "name": c["name"].get(lang, c["name"].get("en")),
                "locality": c["locality"].get(lang, c["locality"].get("en")),
                "address": c["address"].get(lang, c["address"].get("en")),
                "contact_phone": c.get("contact_phone", ""),
                "working_hours": c.get("working_hours", ""),
                "available_services": c.get("available_services", [])
            })
        return results

    def screen_household(self, household: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
        """
        Screens a household against all schemes in the demo resource pack.

        Returns:
            {
                "eligible": [...],
                "more_info_needed": [...],
                "not_eligible": [...],
                "summary": { ... },
                "akshaya_centres": [...]
            }
        """
        # Parse & sanitize household inputs
        occupation = household.get("occupation")
        if occupation:
            occupation = str(occupation).strip().lower()

        # Income handling: None if omitted or empty
        raw_income = household.get("annual_income")
        annual_income: Optional[int] = None
        if raw_income is not None and str(raw_income).strip() != "":
            try:
                annual_income = int(float(str(raw_income).replace(",", "").strip()))
            except ValueError:
                annual_income = None

        raw_age = household.get("age")
        age: Optional[int] = None
        if raw_age is not None and str(raw_age).strip() != "":
            try:
                age = int(float(str(raw_age).strip()))
            except ValueError:
                age = None

        raw_fam = household.get("family_size")
        family_size: Optional[int] = None
        if raw_fam is not None and str(raw_fam).strip() != "":
            try:
                family_size = int(float(str(raw_fam).strip()))
            except ValueError:
                family_size = None

        gender = household.get("gender")
        if gender:
            gender = str(gender).strip().lower()

        raw_disability = household.get("has_disability")
        has_disability: Optional[bool] = None
        if raw_disability is not None and str(raw_disability).strip() != "":
            has_disability = str(raw_disability).lower() in ("yes", "true", "1")

        district = household.get("district")
        if district:
            district = str(district).strip()

        eligible_schemes = []
        more_info_schemes = []
        not_eligible_schemes = []

        for scheme in self.schemes:
            rules = scheme.get("eligibility_rules", {})
            reasons_why = []
            reasons_failed = []
            missing_fields = []

            # 1. Occupation Check
            req_occ = rules.get("occupation", "all").lower()
            if req_occ != "all" and req_occ != "any":
                if not occupation:
                    missing_fields.append("occupation")
                elif occupation != req_occ:
                    if lang == "ml":
                        reasons_failed.append(f"തൊഴിൽ ({occupation}) ഈ പദ്ധതിയുടെ നിബന്ധനയായ ({req_occ})-മായി യോജിക്കുന്നില്ല.")
                    else:
                        reasons_failed.append(f"Occupation ({occupation}) does not match scheme target ({req_occ}).")
                else:
                    if lang == "ml":
                        reasons_why.append(f"തൊഴിൽ യോജിക്കുന്നു ({'മത്സ്യത്തൊഴിലാളി' if req_occ == 'fisher' else 'തോട്ടം തൊഴിലാളി'})")
                    else:
                        reasons_why.append(f"Occupation matches target group ({req_occ.capitalize()})")
            else:
                if lang == "ml":
                    reasons_why.append("തൊഴിൽപരമായ മുൻഗണനാ നിബന്ധനകൾ ബാധകമല്ല (പൊതു വിഭാഗം)")
                else:
                    reasons_why.append("Open to all low-income plantation and coastal households")

            # 2. Income Check
            max_income = rules.get("max_income")
            if max_income is not None:
                if annual_income is None:
                    missing_fields.append("annual_income")
                elif annual_income > max_income:
                    if lang == "ml":
                        reasons_failed.append(f"കുടുംബ വരുമാനം (₹{annual_income:,}) പരമാവധി പരിധിയായ ₹{max_income:,}-നേക്കാൾ കൂടുതലാണ്.")
                    else:
                        reasons_failed.append(f"Annual income (₹{annual_income:,}) exceeds the maximum demo limit of ₹{max_income:,}.")
                else:
                    if lang == "ml":
                        reasons_why.append(f"വാർഷിക വരുമാനം ₹{annual_income:,} അനുവദനീയമായ പരിധിയായ ₹{max_income:,}-ൽ താഴെയാണ്")
                    else:
                        reasons_why.append(f"Annual income ₹{annual_income:,} is within the scheme ceiling of ₹{max_income:,}")

            # 3. Age Check
            min_age = rules.get("min_age")
            max_age = rules.get("max_age")
            if min_age is not None or max_age is not None:
                if age is None:
                    missing_fields.append("age")
                else:
                    if min_age is not None and age < min_age:
                        if lang == "ml":
                            reasons_failed.append(f"പ്രായം ({age}) ആവശ്യമായ കുറഞ്ഞ പ്രായമായ {min_age} വർഷത്തേക്കാൾ കുറവാണ്.")
                        else:
                            reasons_failed.append(f"Applicant age ({age}) is below minimum requirement of {min_age} years.")
                    elif max_age is not None and age > max_age:
                        if lang == "ml":
                            reasons_failed.append(f"പ്രായം ({age}) അനുവദനീയമായ പരമാവധി പ്രായമായ {max_age} വർഷത്തേക്കാൾ കൂടുതലാണ്.")
                        else:
                            reasons_failed.append(f"Applicant age ({age}) exceeds upper age limit of {max_age} years.")
                    else:
                        age_str = f"{min_age}+" if max_age is None else f"{min_age} - {max_age}"
                        if lang == "ml":
                            reasons_why.append(f"പ്രായം {age} നിബന്ധനയായ ({age_str}) വയസ്സിന് അനുയോജ്യമാണ്")
                        else:
                            reasons_why.append(f"Age {age} satisfies the required age bracket ({age_str} years)")

            # 4. Family Size Check
            min_fam = rules.get("min_family_size")
            if min_fam is not None and min_fam > 1:
                if family_size is None:
                    missing_fields.append("family_size")
                elif family_size < min_fam:
                    if lang == "ml":
                        reasons_failed.append(f"കുടുംബാംഗങ്ങളുടെ എണ്ണം ({family_size}) കുറഞ്ഞത് {min_fam} വേണം.")
                    else:
                        reasons_failed.append(f"Family size ({family_size}) is below minimum requirement of {min_fam} members.")
                else:
                    if lang == "ml":
                        reasons_why.append(f"കുടുംബാംഗങ്ങളുടെ എണ്ണം ({family_size}) ആവശ്യകതയായ കുറഞ്ഞത് {min_fam} പേർ പൂർത്തിയാക്കുന്നു")
                    else:
                        reasons_why.append(f"Household size ({family_size}) satisfies requirement (minimum {min_fam} members)")

            # 5. Gender Check
            req_gender = rules.get("gender", "all").lower()
            if req_gender != "all":
                if not gender:
                    missing_fields.append("gender")
                elif gender != req_gender:
                    if lang == "ml":
                        reasons_failed.append(f"ഈ പദ്ധതി സ്ത്രീ തൊഴിലാളികൾക്ക് മാത്രമുള്ളതാണ്.")
                    else:
                        reasons_failed.append(f"Scheme is designated exclusively for {req_gender} applicants.")
                else:
                    if lang == "ml":
                        reasons_why.append(f"ലിംഗ നിബന്ധന യോജിക്കുന്നു ({'സ്ത്രീ' if req_gender == 'female' else req_gender})")
                    else:
                        reasons_why.append(f"Applicant gender matches scheme criteria ({req_gender.capitalize()})")

            # 6. Disability Check
            disability_req = rules.get("disability_required", False)
            if disability_req:
                if has_disability is None:
                    missing_fields.append("has_disability")
                elif not has_disability:
                    if lang == "ml":
                        reasons_failed.append("ഈ പദ്ധതി അംഗീകൃത ഭിന്നശേഷിയുള്ള കുടുംബാംഗങ്ങൾക്കായി നിശ്ചയിച്ചിട്ടുള്ളതാണ്.")
                    else:
                        reasons_failed.append("Scheme requires certified disability status (UDID / Medical Certificate).")
                else:
                    if lang == "ml":
                        reasons_why.append("അംഗീകൃത ഭിന്നശേഷി വിഭാഗം മാനദണ്ഡം പൂർത്തിയാക്കി")
                    else:
                        reasons_why.append("Certified disability support criteria fulfilled")

            # 7. District Check
            req_districts = rules.get("districts", ["all"])
            if "all" not in req_districts:
                if not district:
                    missing_fields.append("district")
                elif district not in req_districts:
                    dist_list = ", ".join(req_districts)
                    if lang == "ml":
                        reasons_failed.append(f"ഈ പദ്ധതി {dist_list} ജില്ലകളിൽ മാത്രമുള്ളതാണ് (നിങ്ങൾ നൽകിയത്: {district}).")
                    else:
                        reasons_failed.append(f"Scheme is active specifically in: {dist_list} (Your district: {district}).")
                else:
                    if lang == "ml":
                        reasons_why.append(f"പദ്ധതി നിലവിലുള്ള ജില്ലയിലാണ് താമസിക്കുന്നത് ({district})")
                    else:
                        reasons_why.append(f"Resident in designated priority district ({district})")

            # Format scheme for presentation
            scheme_display = {
                "id": scheme["id"],
                "name": scheme["name"].get(lang, scheme["name"].get("en")),
                "target_group": scheme["target_group"].get(lang, scheme["target_group"].get("en")),
                "description": scheme["description"].get(lang, scheme["description"].get("en")),
                "required_documents": scheme.get("required_documents", {}).get(lang, scheme.get("required_documents", {}).get("en", [])),
                "application_location": scheme.get("application_location", {}).get(lang, scheme.get("application_location", {}).get("en")),
                "application_method": scheme.get("application_method", {}).get(lang, scheme.get("application_method", {}).get("en")),
                "what_to_do_next": scheme.get("what_to_do_next", {}).get(lang, scheme.get("what_to_do_next", {}).get("en", [])),
                "reasons_why": reasons_why,
                "reasons_failed": reasons_failed,
                "missing_fields": missing_fields
            }

            # DETERMINATION LOGIC (Transparent & Non-guessing)
            # If any rule is explicitly failed, it's NOT_ELIGIBLE.
            if len(reasons_failed) > 0:
                not_eligible_schemes.append(scheme_display)
            # Else if any fields are missing, we CANNOT guess -> MORE_INFO_NEEDED
            elif len(missing_fields) > 0:
                # Add human-friendly explanation of what is missing
                missing_explanations = []
                for mf in missing_fields:
                    if mf == "annual_income":
                        missing_explanations.append(
                            "വാർഷിക കുടുംബ വരുമാനം ആവശ്യമാണ്." if lang == "ml"
                            else "Annual household income is required to verify the income threshold."
                        )
                    elif mf == "age":
                        missing_explanations.append(
                            "പ്രായം രേഖപ്പെടുത്തേണ്ടതുണ്ട്." if lang == "ml"
                            else "Applicant age is required to check age criteria."
                        )
                    elif mf == "occupation":
                        missing_explanations.append(
                            "തൊഴിൽ വിവരം ആവശ്യമാണ്." if lang == "ml"
                            else "Occupation is required to identify sector-specific entitlement."
                        )
                    elif mf == "district":
                        missing_explanations.append(
                            "ജില്ല രേഖപ്പെടുത്തേണ്ടതുണ്ട്." if lang == "ml"
                            else "District is required to check regional scheme eligibility."
                        )
                    elif mf == "has_disability":
                        missing_explanations.append(
                            "ഭിന്നശേഷി വിവരങ്ങൾ വ്യക്തമാക്കുക." if lang == "ml"
                            else "Disability status needs to be clarified."
                        )
                scheme_display["missing_explanations"] = missing_explanations
                more_info_schemes.append(scheme_display)
            # Else all criteria satisfied -> POTENTIALLY_ELIGIBLE
            else:
                eligible_schemes.append(scheme_display)

        akshaya_list = self.get_akshaya_for_district(district, lang)

        return {
            "eligible": eligible_schemes,
            "more_info_needed": more_info_schemes,
            "not_eligible": not_eligible_schemes,
            "summary": {
                "eligible_count": len(eligible_schemes),
                "more_info_count": len(more_info_schemes),
                "not_eligible_count": len(not_eligible_schemes),
                "total_schemes_checked": len(self.schemes)
            },
            "akshaya_centres": akshaya_list,
            "household_echo": {
                "occupation": occupation or ("ലഭ്യമല്ല" if lang == "ml" else "Not provided"),
                "annual_income": f"₹{annual_income:,}" if annual_income is not None else ("ലഭ്യമല്ല" if lang == "ml" else "Not provided"),
                "annual_income_raw": annual_income,
                "age": age if age is not None else ("ലഭ്യമല്ല" if lang == "ml" else "Not provided"),
                "family_size": family_size if family_size is not None else ("ലഭ്യമല്ല" if lang == "ml" else "Not provided"),
                "district": district or ("ലഭ്യമല്ല" if lang == "ml" else "Not provided"),
                "gender": gender or ("ലഭ്യമല്ല" if lang == "ml" else "Not provided"),
                "has_disability": ("ഉണ്ട്" if lang == "ml" else "Yes") if has_disability else (("ഇല്ല" if lang == "ml" else "No") if has_disability is not None else ("ലഭ്യമല്ല" if lang == "ml" else "Not provided"))
            }
        }

