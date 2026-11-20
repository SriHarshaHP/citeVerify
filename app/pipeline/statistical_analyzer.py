import re
from typing import Dict, Any, List
from app.schemas import StatisticalAssessment

def analyze_statistics(source_text: str, claim_text: str = "") -> StatisticalAssessment:
    """
    Evaluates statistical reliability, extracted metrics, confidence intervals,
    and methodological validity of quantitative findings (Feature 6).
    """
    if not source_text:
        return StatisticalAssessment(
            reported_metrics={},
            has_confidence_intervals=False,
            sample_size_adequate=True,
            class_balance_status="unreported",
            data_leakage_risk="low",
            statistical_limitations=["No source text available to evaluate statistical validity."],
            summary="Statistical assessment unavailable."
        )

    lower = source_text.lower()
    metrics: Dict[str, Any] = {}

    # 1. Metric Extraction via Regex
    # Accuracy
    acc_m = re.findall(r'\b(?:accuracy|acc)\s*(?:of|is|was|reached|at)?\s*[:=]?\s*(\d+(?:\.\d+)?%?)', lower)
    if acc_m:
        metrics["accuracy"] = acc_m[0]

    # Sensitivity & Specificity
    sens_m = re.findall(r'\b(?:sensitivity|tpr)\s*(?:of|is|was)?\s*[:=]?\s*(\d+(?:\.\d+)?%?)', lower)
    if sens_m:
        metrics["sensitivity"] = sens_m[0]

    spec_m = re.findall(r'\b(?:specificity|tnr)\s*(?:of|is|was)?\s*[:=]?\s*(\d+(?:\.\d+)?%?)', lower)
    if spec_m:
        metrics["specificity"] = spec_m[0]

    # AUC / ROC
    auc_m = re.findall(r'\b(?:auc|auroc|c-statistic)\s*(?:of|is|was)?\s*[:=]?\s*(0\.\d{2,4})', lower)
    if auc_m:
        metrics["auc"] = float(auc_m[0])

    # P-value
    p_m = re.findall(r'\bp\s*([<>=])\s*(0\.\d{2,4}|\d+\.\d+)', lower)
    if p_m:
        metrics["p_value"] = f"p {p_m[0][0]} {p_m[0][1]}"

    # Effect size (Cohen's d)
    d_m = re.findall(r'\bcohen\'?s\s*d\s*=\s*(0\.\d+|\d+\.\d+)', lower)
    if d_m:
        metrics["cohens_d"] = float(d_m[0])

    # Percentage changes
    pct_changes = re.findall(r'(\d+(?:\.\d+)?%)\s*(?:increase|reduction|improvement|decrease|drop|growth)', lower)
    if pct_changes:
        metrics["reported_relative_change"] = pct_changes[0]

    # 2. Confidence Intervals Check
    has_ci = bool(re.search(r'\b(?:95%?\s*ci|confidence\s*interval|\[\s*0\.\d+\s*,\s*0\.\d+\s*\])', lower))

    # 3. Sample Size Sufficiency Check
    sample_match = re.search(r'\b(?:n\s*=\s*|sample\s*of\s*)(\d+)\b', lower)
    sample_n = int(sample_match.group(1)) if sample_match else None
    sample_size_adequate = True if (not sample_n or sample_n >= 60) else False

    # 4. Statistical Limitations & Data Leakage Risk
    limitations: List[str] = []
    if not has_ci and metrics:
        limitations.append("Confidence intervals (95% CI) were not reported alongside quantitative point estimates.")
    if sample_n and sample_n < 50:
        limitations.append(f"Small sample size (N={sample_n}) increases margin of error and variance.")
    if "retrospective" in lower:
        limitations.append("Retrospective dataset analysis limits causal conclusions regarding prospective efficacy.")
    if any(k in lower for k in ["imbalanced", "rare disease", "prevalence"]):
        limitations.append("Class imbalance may inflate apparent accuracy or positive predictive value.")

    data_leakage_risk = "low"
    if "data leakage" in lower or "overlap between train and test" in lower:
        data_leakage_risk = "high"
        limitations.append("Possible data leakage between training and testing partitions noted.")
    elif "cross-validation" not in lower and "external validation" not in lower and "accuracy" in metrics:
        data_leakage_risk = "moderate"

    # Build summary
    components = []
    if metrics:
        metric_str = ", ".join([f"{k}: {v}" for k, v in metrics.items()])
        components.append(f"Extracted Metrics ({metric_str})")
    if has_ci:
        components.append("Confidence intervals reported")
    elif metrics:
        components.append("Missing confidence intervals")
    if not sample_size_adequate and sample_n:
        components.append(f"Small cohort (N={sample_n})")

    summary_text = "; ".join(components) if components else "Standard statistical reporting."

    return StatisticalAssessment(
        reported_metrics=metrics,
        has_confidence_intervals=has_ci,
        sample_size_adequate=sample_size_adequate,
        class_balance_status="imbalanced" if "imbalance" in lower else "standard",
        data_leakage_risk=data_leakage_risk,
        statistical_limitations=limitations,
        summary=summary_text
    )
