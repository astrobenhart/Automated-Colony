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
    assert "Family, reproduction, ancestry, children, romance, households, and pair-bond systems are deferred" in design
    assert "same-settlement social bonuses" in design
