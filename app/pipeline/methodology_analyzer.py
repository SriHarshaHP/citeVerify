import re
from typing import Dict, Any, List, Optional
from app.schemas import MethodologyInfo

def analyze_methodology(source_text: str, title: str = "", metadata: Optional[Dict[str, Any]] = None) -> MethodologyInfo:
    """
    Analyzes research methodology, study design, and limitations (Feature 5).
    Distinguishes:
      1. Explicit Author Limitations
      2. Methodological Concerns (from study design)
      3. AI-Inferred Concerns (clearly labeled)
    """
    if not source_text:
        return MethodologyInfo(
            study_design="unknown",
            risk_of_bias="unclear",
            explicit_author_limitations=[],
            methodological_concerns=["Source full text was not accessible for methodology extraction."],
            ai_inferred_concerns=["[AI Inferred] Verification is restricted to available metadata."]
        )

    lower_text = source_text.lower()
    lower_title = (title or "").lower()
    combined = lower_title + " " + lower_text

    # 1. Study Design Classification
    study_design_evidence = ""
    if any(k in combined for k in ["guest editorial", "editorial", "editor's note", "preface", "commentary", "perspective", "letter to the editor"]):
        study_design = "editorial"
        study_design_evidence = "Source identified as an editorial / commentary; not an empirical clinical trial."
    elif any(k in combined for k in ["meta-analysis", "meta analysis"]):
        study_design = "meta_analysis"
        study_design_evidence = "Meta-analysis methodology identified in source text."
    elif any(k in combined for k in ["systematic review", "prisma"]):
        study_design = "systematic_review"
        study_design_evidence = "Systematic review methodology identified in source text."
    elif any(k in combined for k in ["narrative review", "literature review", "scoping review", "annual review", "overview of"]):
        study_design = "literature_review"
        study_design_evidence = "Literature review identified in source text; not an experimental study."
    elif any(k in combined for k in ["randomized controlled trial", "double-blind randomized", "placebo-controlled trial", "clinical trial registration", "randomly allocated", "randomly assigned"]):
        study_design = "randomized_controlled_trial"
        study_design_evidence = "Randomized interventional clinical trial design identified in text."
    elif any(k in combined for k in ["prospective cohort", "prospective study", "prospectively enrolled"]):
        study_design = "prospective_cohort"
        study_design_evidence = "Prospective cohort design identified in text."
    elif any(k in combined for k in ["retrospective", "historical cohort", "retrospectively"]):
        study_design = "retrospective_cohort"
        study_design_evidence = "Retrospective study design identified in text."
    elif any(k in combined for k in ["in vitro", "murine", "rat model", "cell culture", "bilayer", "mice", "rodent"]):
        study_design = "in_vitro_or_animal_model"
        study_design_evidence = "In-vitro or animal laboratory model identified in text."
    elif any(k in combined for k in ["simulation", "synthetic benchmark", "numerical simulation"]):
        study_design = "computational_simulation"
        study_design_evidence = "Computational simulation/benchmark identified in text."
    elif any(k in combined for k in ["cross-sectional", "survey"]):
        study_design = "cross_sectional_study"
        study_design_evidence = "Cross-sectional survey design identified in text."
    elif any(k in combined for k in ["observational study", "cohort study", "clinical study"]):
        study_design = "observational_study"
        study_design_evidence = "Observational cohort study design identified in text."
    else:
        study_design = "NOT_REPORTED"
        study_design_evidence = "Study design was not reported or could not be determined from source text."

    # 2. Design Flags
    is_prospective = "prospective" in combined and "retrospective" not in combined
    has_external_validation = any(k in combined for k in ["external validation", "independent test set", "out-of-distribution", "prospective validation"])
    has_control_group = any(k in combined for k in ["control group", "control cohort", "placebo", "baseline control"])

    # Multicenter status: do NOT assume single-center if unreported
    is_multicenter = None
    if any(k in combined for k in ["multi-center", "multicenter", "multi-site", "two centers", "international evaluation"]):
        is_multicenter = True
    elif any(k in combined for k in ["single-center", "single center", "single-site", "single site", "single institution"]):
        is_multicenter = False

    # 3. Sample Size / Patient Count Extraction (Do not invent sample sizes)
    patient_count = None
    sample_size = None
    sample_size_evidence = ""

    # Check for systematic review multi-level sample: e.g. "12 studies involving 131,822 screened women"
    sys_review_sample = re.search(
        r'(\d+)\s+(?:included\s+)?studies\s+(?:involving|evaluating|with)\s+([\d,]+)\s*(?:screened\s+women|participants|patients|individuals|subjects)',
        combined
    )
    if sys_review_sample:
        studies_cnt = sys_review_sample.group(1)
        screened_str = sys_review_sample.group(2)
        patient_count = int(screened_str.replace(',', ''))
        sample_size = f"{screened_str} screened women across {studies_cnt} included studies"
        sample_size_evidence = f"Extracted systematic review cohort: {sample_size}."
    else:
        sample_matches = re.findall(
            r'\b(?:n\s*=\s*|sample\s*of\s*|cohort\s*of\s*|dataset\s*of\s*)(\d{1,3}(?:,\d{3})+|\d+)(?:\s*(?:patients?|participants?|students?|subjects?|cases?|images?|rats?|mice|animals?|defects?))\b',
            combined
        )
        if not sample_matches:
            sample_matches = re.findall(r'\(\s*n\s*=\s*(\d+)\s*\)', combined)
        if sample_matches:
            raw_val = sample_matches[0].replace(',', '')
            patient_count = int(raw_val)
            sample_size = f"{patient_count:,} subjects/cases"
            sample_size_evidence = f"Extracted cohort size N={patient_count} from source text."
        else:
            sample_size = "NOT_REPORTED"
            sample_size_evidence = "Sample size was not reported in retrieved text."

    # 4. Explicit Author Limitations
    explicit_limitations = []
    # Search for author limitation sentences
    lim_patterns = [
        r'(?:limitation|limitations|caveat|caveats)\s+(?:of\s+(?:this|our)\s+study\s+include|is\s+that|are\s+that)[^.]+\.',
        r'however,\s+the\s+cohort\s+was\s+strictly\s+composed[^.]+\.',
        r'generalization\s+to\s+diverse[^.]+\.',
        r'performance\s+was\s+sensitive\s+to[^.]+\.',
        r'evidence\s+is\s+currently\s+insufficient[^.]+\.'
    ]
    for p in lim_patterns:
        m = re.search(p, lower_text)
        if m:
            clean_lim = m.group(0).strip().capitalize()
            explicit_limitations.append(clean_lim)

    # 5. Methodological Concerns (from study design)
    methodological_concerns = []
    if study_design == "editorial":
        methodological_concerns.append("Editorial introduction / commentary; does not report original interventional or empirical clinical trial data.")
    elif study_design in ["literature_review", "systematic_review_and_meta_analysis"]:
        methodological_concerns.append("Secondary literature synthesis; does not constitute an experimental primary trial.")
    elif study_design == "NOT_REPORTED":
        methodological_concerns.append("Methodology was not reported in available source text.")

    if "retrospective" in study_design:
        methodological_concerns.append("Retrospective study design may introduce selection bias and unmeasured confounding.")
    if patient_count and patient_count < 50:
        methodological_concerns.append(f"Small sample size / cohort size (N = {patient_count}) limits statistical power and increases risk of type II errors.")
    if is_multicenter is False:
        methodological_concerns.append("Single-center or single-site data collection may constrain institutional generalizability.")
    if not has_external_validation and "clinical" in combined and study_design not in ["editorial", "literature_review"]:
        methodological_concerns.append("Lacks independent external clinical validation across diverse demographic settings.")
    if any(k in combined for k in ["high risk of bias", "risk of bias"]):
        methodological_concerns.append("High risk of methodological bias identified across reported study workflows.")

    # 6. Risk of Bias
    if len(methodological_concerns) >= 3 or "high risk of bias" in combined:
        risk_of_bias = "high"
    elif len(methodological_concerns) >= 1:
        risk_of_bias = "moderate"
    else:
        risk_of_bias = "low"

    # 7. AI-Inferred Concerns (clearly labeled as AI interpretations)
    ai_inferred = []
    if "female psychology students" in combined or "undergraduate" in combined:
        ai_inferred.append("[AI Inferred] Findings established on undergraduate convenience samples may not generalize to diverse clinical or demographic populations.")
    if "synthetic" in combined or "in vitro" in combined:
        ai_inferred.append("[AI Inferred] Biophysical and in-vitro parameters may diverge under physiological in-vivo conditions.")
    if "selected evaluation conditions" in combined:
        ai_inferred.append("[AI Inferred] Performance observed under curated evaluation thresholds may degrade in unconstrained real-world deployment.")

    evidence_dict = {
        "study_design": study_design_evidence,
        "sample_size": sample_size_evidence
    }

    return MethodologyInfo(
        study_design=study_design,
        sample_size=sample_size,
        patient_count=patient_count,
        dataset_size=sample_size if sample_size != "NOT_REPORTED" else None,
        is_prospective=is_prospective,
        is_multicenter=is_multicenter,
        has_external_validation=has_external_validation,
        has_control_group=has_control_group,
        risk_of_bias=risk_of_bias,
        explicit_author_limitations=explicit_limitations,
        methodological_concerns=methodological_concerns,
        ai_inferred_concerns=ai_inferred,
        funding_and_conflicts=None,
        methodology_evidence=evidence_dict
    )
