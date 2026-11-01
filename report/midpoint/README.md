# Midpoint report

ACM double-column (`acmart`, `sigconf`), 7 pages. The abstract, introduction and Section 2 (Related Work) are from Vedant's draft, updated for the midpoint. Sections 3 and 4 are new.

| File | Contents |
|---|---|
| `main.tex` | Title, abstract, introduction, Section 2 (Related Work), Figure 1 |
| `sec3_method_progress.tex` | Section 3, Method and Progress (#15): Version 0, Figure 2, Table 1 (P1–P10), check validation, harness, pilot (Table 2), remaining work, challenges |
| `sec4_expected_findings.tex` | Section 4, Expected Findings and Evaluation Plan (#14) |
| `refs.bib` | References |

## Build

```bash
brew install tectonic        # once
cd report/midpoint && tectonic main.tex
```

## Student IDs

The repository is public, so the IDs are not committed. To print them in the title block, create `ids.tex` in this folder (it is git-ignored):

```latex
\renewcommand{\vedantid}{ (Vedant's ID)}
\renewcommand{\yashid}{ (Yash's ID)}
```

Without it, the PDF shows names only. Built PDFs are git-ignored for the same reason.

## Where the numbers come from

- Version 0 stability, 5/5 runs: `results/v0/` (`harness/evaluate.py`)
- Planted faults, 5 of 6 caught (functional tests catch 1): `results/mutants/` (`harness/mutants.sh`)
- Pilot, Claude Code on changes 01–02: `results/pilot/claude-code/run1/` (`harness/pilot.md`)
