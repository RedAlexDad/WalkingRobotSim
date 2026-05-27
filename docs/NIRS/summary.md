# Summary — Bibliographic Workflow

## Goal
Find correct DOIs/URLs for all bibliography references, expand from 13 to 21 sources, and insert `[14]–[21]` square-bracket citations into chapter 3 .md files.

## Progress

### Done
- **Expanded bibliography** from 13 → 21 sources (8 new via Crossref):
  - #14 Miki et al. (2022) IROS — GPU elevation mapping. DOI: `10.1109/IROS47612.2022.9981507`
  - #15 Erni et al. (2023) IROS — Multi-modal elevation mapping. DOI: `10.1109/IROS55552.2023.10342108`
  - #16 Dong et al. (2025) TRO — MARG risky gap terrains for legged robots. DOI: `10.1109/TRO.2025.3619041`
  - #17 Belter et al. (2016) — RGB-D terrain perception for legged robots. DOI: `10.1515/amcs-2016-0006`
  - #18 Wermelinger et al. (2016) IROS — Navigation planning in challenging terrain. DOI: `10.1109/IROS.2016.7759199`
  - #19 Homberger et al. (2019) ICRA — Support surface estimation. DOI: `10.1109/ICRA.2019.8793646`
  - #20 Fu et al. (2022) RCAR — Traversability from sparse point cloud (Wang C co-author). DOI: `10.1109/RCAR54675.2022.9872233`
  - #21 Pan et al. (2019) ROBIO — GPU accelerated traversability mapping. DOI: `10.1109/ROBIO49542.2019.8961816`
- **Created tracking files:** `sources_verify_ch12.md` (4 sources), `sources_verify_ch3.md` (21 sources, uniform + GOST lists).
- **Inserted `[14]–[21]` citations** into 9 chapter 3 files:
  - `ch3_06_filtering.md` — [14] added to parameters (line 9) and visibility cleanup (line 25)
  - `ch3_07_ground_seg.md` — [17] added to ground segmentation (line 11)
  - `ch3_08_dem.md` — [14, 15] to DEM construction (line 9); [14, 19] to GPU performance (line 47)
  - `ch3_09_cost.md` — [16, 18, 20, 21] to traversability concept (line 9); [16, 18] to weight tuning (line 39)
  - `ch3_10_gait.md` — [16] to gait adaptation (line 9)
  - `ch3_13_conclusions.md` — [17] to ground segmentation summary (line 17)
- **Two commits made:**
  - `dc0e6e0` — tracking files + summary
  - `8d13813` — expanded bibliography to 21 sources
- All 21 sources now have DOIs/URLs except 3 still in search (#5, #11, #12).

### Remaining Issues
- **#5 Fankhauser PhD thesis** ETH handle — no DOI found.
- **#11 Okada RA-L 2023** — no Crossref match by exact title.
- **#12 Wang C ICRA 2023** — no Crossref match; Fu et al. (2022) #20 has Wang C co-author but different paper.
- **Web search tool** (parallel.ai) returns 403 — cannot use Semantic Scholar / Google Scholar.
- **Batch edit of `title.md`** is pending — update GOST entries with DOIs/URLs, and insert 8 new entries in correct GOST format with proper numbering.
