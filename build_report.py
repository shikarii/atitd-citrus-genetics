"""Fill report_template.html with the comparison table, the raw data and the code -> report.html."""
import html
from pathlib import Path
import pandas as pd

HERE = Path(__file__).parent
SHOW = [  # (model name in results/model_comparison.csv, label on the page)
    ("CLAIM: 1 of 8 genes, uniform +-150", "Proposed: 1 of 8 genes nudged, flat ±150"),
    ("uniform +-160", "Nudge flat ±160"),
    ("uniform +-200", "Nudge flat ±200"),
    ("uniform +-140", "Nudge flat ±140"),
    ("triangular +-150", "Nudge triangular ±150 (small nudges likelier)"),
    ("each gene nudged independently, p=0.14", "Each gene nudged independently (best rate, 14%)"),
    ("length shown as min", "Length shown as lower gene"),
    ("sweet shown as max", "Sweet shown as higher gene"),
    ("sweet shown as mean", "Sweet shown as average"),
    ("size shown as mean", "Size shown as average"),
    ("color shown as min", "Color shown as lower gene"),
    ("color shown as g1", "Color shown as gene 1 only"),
    ("1 gene per trait (no hidden genes)", "One gene per trait, no hidden genes"),
]

res = pd.read_csv(HERE / "results" / "model_comparison.csv").set_index("model")
base = res.loc[SHOW[0][0], "fit_ll"]
rows = []
for key, label in SHOW:
    r = res.loc[key]
    d = r.fit_ll - base
    cls = ' class="claim"' if key == SHOW[0][0] else ""
    dcls = "neg" if d < 0 else ("pos" if d > 0 else "")
    rows.append(f'<tr{cls}><td>{label}</td><td class="n">{r.fit_ll:,.1f}</td>'
                f'<td class="n {dcls}">{d:+,.1f}</td><td class="n">{int(r.children_impossible)}</td></tr>')

page = (HERE / "report_template.html").read_text(encoding="utf-8")
page = page.replace("%%COMPARE_ROWS%%", "\n".join(rows))
PKG = HERE / "python" / "citrus_genetics"
for tag, f in (
    ("CSV", "data/children.csv"),
    ("MODEL", PKG / "core" / "model.py"),
    ("COMPARE", PKG / "pipelines" / "compare.py"),
    ("SIM", PKG / "pipelines" / "sim_checks.py"),
    ("EXTRACT", PKG / "io" / "extract.py"),
):
    path = HERE / f if isinstance(f, str) else f
    page = page.replace(f"%%{tag}%%", html.escape(path.read_text(encoding="utf-8")))
(HERE / "report.html").write_text(page, encoding="utf-8")
print("report.html", len(page) // 1024, "KB")
