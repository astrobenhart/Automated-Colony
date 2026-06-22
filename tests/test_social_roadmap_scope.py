from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_roadmap_uses_identity_and_social_bond_language():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")

    assert "Settlement identity and belonging" in roadmap
    assert "Optional Social Bond Labels" in roadmap
    assert "Social behavior shaped by settlement membership" not in roadmap
    assert "Optional pair/family labels" not in roadmap


def test_design_defers_family_reproduction_and_romance_systems():
    design = (ROOT / "DESIGN.md").read_text(encoding="utf-8")

    assert "Social bonds should describe familiarity before they imply family." in design
    assert "Household foundations now exist as village-unit membership, not family simulation." in design
    assert "Family, reproduction, ancestry, children, romance, inheritance, and pair-bond systems are deferred" in design
    assert "same-settlement social bonuses" in design


def test_roadmap_includes_household_foundation_milestone():
    roadmap = (ROOT / "ROADMAP.md").read_text(encoding="utf-8")

    assert "v0.7.1 - Living Village" in roadmap
    assert "v0.8 - Generational Village" in roadmap
    assert "Reproduction, inheritance, children, family continuity, and generational history remain upcoming priorities" in roadmap
