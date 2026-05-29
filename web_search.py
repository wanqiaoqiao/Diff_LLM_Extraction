from __future__ import annotations

from .models import CommercialMethodSignal


def infer_commercial_signals(target_cell_type: str) -> list[CommercialMethodSignal]:
    """Return hand-curated commercial/public method signals.

    This function is intentionally explicit rather than magical:
    the package keeps commercial influence auditable.
    """
    target = target_cell_type.lower().strip()
    signals: list[CommercialMethodSignal] = []

    if "dopaminergic" in target:
        signals.extend(
            [
                CommercialMethodSignal(
                    company="Aspen Neuroscience",
                    program="ANPD001 / sasineprocel",
                    target_cell_type=target_cell_type,
                    method_module="dopaminergic neuronal precursor product state",
                    details="Public materials emphasize iPSC-derived dopaminergic neuronal precursor cells with proprietary manufacturing and strong QC.",
                    public_evidence_url="https://aspenneuroscience.com/technology-overview/",
                    confidence="medium",
                ),
                CommercialMethodSignal(
                    company="BlueRock Therapeutics",
                    program="Bemdaneprocel",
                    target_cell_type=target_cell_type,
                    method_module="midbrain dopaminergic progenitor / floor-plate-like product logic",
                    details="Commercial Parkinson's cell therapy programs repeatedly center a progenitor-stage graft rather than a fully mature neuron.",
                    public_evidence_url="https://bluerocktx.com/",
                    confidence="medium",
                ),
            ]
        )
    elif "beta" in target or "pancreatic" in target:
        signals.extend(
            [
                CommercialMethodSignal(
                    company="STEMCELL Technologies",
                    program="STEMdiff Pancreatic Progenitor Kit",
                    target_cell_type=target_cell_type,
                    method_module="4-stage pancreatic progenitor route before beta maturation",
                    details="Public kit materials explicitly reinforce the staged path through definitive endoderm, primitive gut tube, posterior foregut, and pancreatic progenitor.",
                    public_evidence_url="https://www.stemcell.com/products/stemdiff-pancreatic-progenitor-kit.html",
                    confidence="high",
                ),
                CommercialMethodSignal(
                    company="ViaCyte",
                    program="PEC-01 / pancreatic endoderm",
                    target_cell_type=target_cell_type,
                    method_module="pancreatic endoderm / progenitor stage as manufacturable intermediate",
                    details="Public clinical materials repeatedly emphasize a pancreatic progenitor/endoderm intermediate rather than directly manufacturing fully mature beta cells in vitro.",
                    public_evidence_url="https://academic.oup.com/stcltm/article/4/8/927/6397291",
                    confidence="high",
                ),
            ]
        )
    elif "cardiomyocyte" in target:
        signals.extend(
            [
                CommercialMethodSignal(
                    company="STEMCELL Technologies",
                    program="STEMdiff Ventricular Cardiomyocyte Differentiation Kit",
                    target_cell_type=target_cell_type,
                    method_module="defined staged media with maintenance switch",
                    details="Public kit materials reinforce a defined staged media schedule and maintenance medium switch rather than exposing all components.",
                    public_evidence_url="https://www.stemcell.com/products/stemdiff-cardiomyocyte-kit.html",
                    confidence="high",
                ),
                CommercialMethodSignal(
                    company="Ncardia",
                    program="Ncyte vCardiomyocytes",
                    target_cell_type=target_cell_type,
                    method_module="scale-ready ventricular cardiomyocyte manufacturing and QC emphasis",
                    details="Public product materials emphasize large-batch reproducibility, purity, and controlled bioreactor manufacturing rather than exploratory factor screening.",
                    public_evidence_url="https://www.ncardia.com/discovery-services/modeling/ncyte-cardiomyocytes",
                    confidence="medium",
                ),
            ]
        )
    return signals


def commercial_anchor_rules() -> list[str]:
    return [
        "Prioritize publicly repeated commercial stage modules when they are explicit enough to reproduce.",
        "Prefer manufacturable modules for the anchor protocol: serum-free, feeder-free, defined media, scalable cluster or bioreactor-compatible stages.",
        "Prefer product-state logic that companies repeatedly expose publicly, such as progenitor harvest windows or maintenance-medium switches.",
    ]


def commercial_doe_deprioritization_rules() -> list[str]:
    return [
        "Do not put proprietary supplements, undisclosed kit contents, or closed-formulation commercial tweaks into first-pass DOE factors.",
        "If a company signal is only high-level and not factor-explicit, use it to bias the anchor protocol narrative but not DOE screening factors.",
        "Only promote a commercial method factor into DOE when it is both publicly described and independently repeated in academic articles.",
    ]
