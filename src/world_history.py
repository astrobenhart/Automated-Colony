from dataclasses import dataclass, field
from pathlib import Path
import re

from src.generations import BIRTH, FAMILY, SUCCESSION


ENVIRONMENT = "ENVIRONMENT"
SEASON = "SEASON"
WILDLIFE = "WILDLIFE"
SETTLEMENT = "SETTLEMENT"
HOUSEHOLD = "HOUSEHOLD"
WORKPLACE = "WORKPLACE"
POPULATION = "POPULATION"
LOCAL_STORY = "LOCAL_STORY"
MYSTERY = "MYSTERY"
DEATH = "DEATH"
DEFAULT_CHRONICLE_ROOT = "saves"
SEASON_ORDER = ("Spring", "Summer", "Autumn", "Winter")

HISTORY_CATEGORIES = {
    ENVIRONMENT,
    SEASON,
    WILDLIFE,
    SETTLEMENT,
    HOUSEHOLD,
    WORKPLACE,
    POPULATION,
    LOCAL_STORY,
    MYSTERY,
    BIRTH,
    FAMILY,
    SUCCESSION,
    DEATH,
}


@dataclass(frozen=True)
class HistoryEntry:
    day: int
    year: int
    season: str
    category: str
    title: str
    description: str


@dataclass
class WorldHistory:
    entries: list[HistoryEntry] = field(default_factory=list)
    village_name: str = "Village"
    chronicle_path: Path | None = field(default=None, repr=False)
    last_chronicle_error: str | None = field(default=None, repr=False)

    def configure_chronicle(self, village_name: str, save_root: str | Path = DEFAULT_CHRONICLE_ROOT) -> Path:
        self.village_name = village_name or "Village"
        self.chronicle_path = Path(save_root) / slugify(self.village_name) / "chronicle.md"
        self.write_chronicle()
        return self.chronicle_path

    def record(
        self,
        *,
        day: int,
        year: int,
        season: str,
        category: str,
        title: str,
        description: str,
    ) -> HistoryEntry:
        entry = HistoryEntry(
            day=day,
            year=year,
            season=season,
            category=category,
            title=title,
            description=description,
        )
        self.entries.append(entry)
        self.write_chronicle()
        return entry

    def recent(self, limit: int):
        if limit <= 0:
            return []
        return self.entries[-limit:]

    def by_category(self, category: str):
        return [entry for entry in self.entries if entry.category == category]

    def count(self) -> int:
        return len(self.entries)

    def write_chronicle(self) -> None:
        if self.chronicle_path is None:
            return
        try:
            self.chronicle_path.parent.mkdir(parents=True, exist_ok=True)
            self.chronicle_path.write_text(self.to_markdown(), encoding="utf-8")
            self.last_chronicle_error = None
        except OSError as exc:
            self.last_chronicle_error = str(exc)

    def to_markdown(self) -> str:
        lines = [
            f"# Chronicle of {self.village_name}",
            "",
            f"This is the written history of {self.village_name}, recorded as the village lives.",
            "",
            "---",
            "",
        ]
        if not self.entries:
            lines.extend(["_No notable events have been recorded yet._", ""])
            return "\n".join(lines)

        for year, year_entries in grouped_by_year(self.entries):
            lines.extend([f"# Year {year}", ""])
            for season, season_entries in grouped_by_season(year_entries):
                lines.extend([f"## {season}", ""])
                for entry in season_entries:
                    lines.append(f"- {entry_prose(entry)}")
                lines.append("")
        return "\n".join(lines)


def grouped_by_year(entries: list[HistoryEntry]) -> list[tuple[int, list[HistoryEntry]]]:
    years = sorted({entry.year for entry in entries})
    return [(year, sorted((entry for entry in entries if entry.year == year), key=lambda item: (item.day, item.title))) for year in years]


def grouped_by_season(entries: list[HistoryEntry]) -> list[tuple[str, list[HistoryEntry]]]:
    season_index = {season: index for index, season in enumerate(SEASON_ORDER)}
    seasons = sorted({entry.season for entry in entries}, key=lambda season: (season_index.get(season, len(SEASON_ORDER)), season))
    return [(season, [entry for entry in entries if entry.season == season]) for season in seasons]


def entry_prose(entry: HistoryEntry) -> str:
    text = (entry.description or entry.title or "An event was recorded.").strip()
    replacements = {
        "Construction completed.": "A new home was completed.",
        "Construction Completed": "A new home was completed.",
        "Birth event.": "A child was born.",
        "Birth Event": "A child was born.",
    }
    text = replacements.get(text, text)
    if text and text[-1] not in ".!?":
        text += "."
    return text


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "village"
