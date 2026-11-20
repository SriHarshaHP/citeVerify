import json
from typing import List, Dict, Any
from app.schemas import (
    Claim,
    Reference,
    SourcePackage,
    EvidenceTierEnum,
    ClaimTypeEnum,
    TextChunk
)
from app.pipeline.p8_verify_guardrails import verify_claim_reference_pair

# 20 hand-labeled claim-source benchmark test cases
BENCHMARK_DATASET = [
    {
        "id": "BM01",
        "claim": "Deep neural scaling follows power laws with compute and dataset size.",
        "expected_label": "SUPPORTED",
        "source_text": "We observe that neural language model cross-entropy loss scales as a power-law with dataset size and compute.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2020
    },
    {
        "id": "BM02",
        "claim": "Real-time automated code testing improved final exam pass rates by 50%.",
        "expected_label": "PARTIALLY_SUPPORTED",  # number mismatch
        "source_text": "Students using the automated testing portal achieved an 18% improvement in final exam scores.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2021
    },
    {
        "id": "BM03",
        "claim": "Daily smartphone meditation completely resolves undergraduate academic distress across all disciplines.",
        "expected_label": "PARTIALLY_SUPPORTED",  # scope overgeneralized
        "source_text": "In our pilot of 35 female psychology students, participants reported a modest reduction in self-reported stress.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2022
    },
    {
        "id": "BM04",
        "claim": "Potassium channel selectivity filters undergo rapid voltage-gated conformational switching.",
        "expected_label": "UNSUPPORTED",  # completely unrelated paper
        "source_text": "In this paper we measure the mechanical shear deformation of synthetic dipalmitoylphosphatidylcholine bilayers.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2019
    },
    {
        "id": "BM05",
        "claim": "Quantum gradient descent speeds up matrix inversion by 120x.",
        "expected_label": "UNVERIFIABLE",  # not found
        "source_text": "",
        "tier": EvidenceTierEnum.NOT_FOUND,
        "ref_year": 2024
    },
    {
        "id": "BM06",
        "claim": "Self-supervised representations reduce reliance on extensive manual labels.",
        "expected_label": "UNCITED",  # uncited
        "source_text": "",
        "tier": EvidenceTierEnum.NOT_FOUND,
        "is_uncited": True,
        "ref_year": 2021
    },
    {
        "id": "BM07",
        "claim": "Statistical language models are bounded by finite memory footprints of 1,000 tokens.",
        "expected_label": "POSSIBLY_OUTDATED",  # outdated source
        "source_text": "Statistical language models remain severely bounded by practical n-gram memory footprints, rarely maintaining coherence beyond 1,000 tokens.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2007
    },
    {
        "id": "BM08",
        "claim": "Peptide-functionalized scaffolds accelerate osteogenesis within three weeks.",
        "expected_label": "SUPPORTED",  # retracted source, label is supported but retracted flag forced
        "source_text": "Histological evaluation demonstrated robust bone matrix deposition and mineralized osteoid formation within three weeks post-implantation.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2018,
        "is_retracted": True
    },
    {
        "id": "BM09",
        "claim": "CRISPR-Cas9 enables targeted double-strand breaks in human genome sequences.",
        "expected_label": "SUPPORTED",
        "source_text": "Cas9 can be programmed with single guide RNAs to induce site-specific double-strand breaks in genomic DNA.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2013
    },
    {
        "id": "BM10",
        "claim": "Dietary sodium reduction reduces systolic blood pressure by 25 mmHg in normotensive adults.",
        "expected_label": "PARTIALLY_SUPPORTED",  # number mismatch (5 mmHg vs 25 mmHg)
        "source_text": "A meta-analysis of sodium reduction trials demonstrated a modest reduction of 5.4 mmHg in systolic blood pressure.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2020
    },
    {
        "id": "BM11",
        "claim": "High-temperature superconductivity in cuprates operates strictly via acoustic phonon pairing.",
        "expected_label": "CONTRADICTORY",
        "source_text": "Our spectroscopic measurements rule out acoustic phonon pairing as the primary mechanism for cuprate superconductivity, pointing instead to spin fluctuations.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2017
    },
    {
        "id": "BM12",
        "claim": "The cosmic microwave background exhibits quadrupole temperature fluctuations.",
        "expected_label": "SUPPORTED",
        "source_text": "Statistical analysis of the Wilkinson Microwave Anisotropy Probe data reveals significant low-multipole quadrupole temperature fluctuations.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2011
    },
    {
        "id": "BM13",
        "claim": "Graph neural networks outperform convolutional networks on molecular solubility prediction.",
        "expected_label": "SUPPORTED",
        "source_text": "Graph neural network representations achieve higher predictive accuracy than standard convolutional architectures on molecular solubility benchmarks.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2021
    },
    {
        "id": "BM14",
        "claim": "Lithium-sulfur batteries retain 99% capacity after 5,000 deep discharge cycles.",
        "expected_label": "PARTIALLY_SUPPORTED",  # number mismatch
        "source_text": "Porous carbon cathodes demonstrated 82% capacity retention after 500 charge-discharge cycles.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2022
    },
    {
        "id": "BM15",
        "claim": "A 100% cure rate for metastatic melanoma was attained using synthetic oncolytic virus OX-40.",
        "expected_label": "UNVERIFIABLE",  # reference not found
        "source_text": "",
        "tier": EvidenceTierEnum.NOT_FOUND,
        "ref_year": 2025
    },
    {
        "id": "BM16",
        "claim": "Convolutional receptive fields expand hierarchically across layered architectures.",
        "expected_label": "SUPPORTED",
        "source_text": "We prove mathematically that effective receptive field size scales proportionally with the square root of layer depth.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2016
    },
    {
        "id": "BM17",
        "claim": "Atmospheric methane concentrations increased by 40% between 2000 and 2005.",
        "expected_label": "CONTRADICTORY",
        "source_text": "Global atmospheric methane growth plateaus between 1999 and 2006, exhibiting near-zero net accumulation during this timeframe.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2008
    },
    {
        "id": "BM18",
        "claim": "Perovskite solar cell degradation is dominated by moisture-induced phase segregation.",
        "expected_label": "SUPPORTED",
        "source_text": "In situ X-ray diffraction confirms that moisture exposure accelerates degradation through irreversible perovskite phase segregation.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2019
    },
    {
        "id": "BM19",
        "claim": "Solid-state electrolytes eliminate lithium dendrite penetration at current densities exceeding 100 mA/cm2.",
        "expected_label": "PARTIALLY_SUPPORTED",  # scope caveat
        "source_text": "Sulfide electrolytes suppressed dendrite growth under laboratory conditions at a critical current density of 10 mA/cm2.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2020
    },
    {
        "id": "BM20",
        "claim": "Deep reinforcement learning agents achieve superhuman performance in multi-agent real-time strategy games.",
        "expected_label": "SUPPORTED",
        "source_text": "The multi-agent reinforcement learning system defeated professional human grandmasters in StarCraft II with a 99.8% win rate.",
        "tier": EvidenceTierEnum.FULL_TEXT,
        "ref_year": 2019
    }
]

def run_mini_benchmark():
    print(f"Running CiteVerify Mini-Benchmark on {len(BENCHMARK_DATASET)} hand-labeled cases...")
    
    matches = 0
    results_detail = []

    for item in BENCHMARK_DATASET:
        c_id = item["id"]
        c_text = item["claim"]
        is_uncited = item.get("is_uncited", False)
        
        claim = Claim(
            id=c_id,
            verbatim_text=c_text,
            type=ClaimTypeEnum.FINDING,
            page=1,
            section="Body",
            citation_markers=["[1]"] if not is_uncited else [],
            has_citation=not is_uncited
        )
        
        ref = Reference(
            key="1",
            raw_string="[1] Benchmark Reference",
            title=c_text[:50],
            year=item["ref_year"]
        ) if not is_uncited else None

        source_text = item["source_text"]
        chunks = [TextChunk(chunk_id="c0", page=1, text=source_text)] if source_text else []
        
        pkg = SourcePackage(
            reference_key="1",
            title_match_score=95.0 if source_text else 0.0,
            text_chunks=chunks,
            full_text=source_text,
            evidence_tier=item["tier"],
            retraction_flag=item.get("is_retracted", False),
            metadata={"publication_year": item["ref_year"]}
        ) if not is_uncited else None

        verdict_res = verify_claim_reference_pair(claim, ref, pkg)
        is_match = (verdict_res.label == item["expected_label"])
        if is_match:
            matches += 1

        results_detail.append({
            "id": c_id,
            "claim": c_text,
            "expected": item["expected_label"],
            "predicted": verdict_res.label,
            "match": is_match,
            "score": verdict_res.evidence_strength_score,
            "flags": [f.value for f in verdict_res.flags]
        })

    accuracy = (matches / len(BENCHMARK_DATASET)) * 100.0
    print("\n--- Mini-Benchmark Measured Results (Section 13) ---")
    print(f"Sample Size: {len(BENCHMARK_DATASET)} hand-labeled claim-source pairs")
    print(f"Correct Matches: {matches} / {len(BENCHMARK_DATASET)}")
    print(f"Measured Exact Match Accuracy: {accuracy:.1f}%\n")

    output_path = "BENCHMARK_RESULTS.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "sample_size": len(BENCHMARK_DATASET),
            "matches": matches,
            "measured_accuracy_pct": accuracy,
            "details": results_detail
        }, f, indent=2)

    print(f"Saved benchmark results to {output_path}")
    return accuracy

if __name__ == "__main__":
    run_mini_benchmark()
