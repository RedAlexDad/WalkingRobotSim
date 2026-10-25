# AGENTS.md — Hard Requirements for the Ergonomics Course Project (KR)

**Scope:** any AI agent or human-AI workflow working on the ergonomics course project (KR) in this directory.  
**Status:** binding. These rules override convenience, prior drafts, article deadlines, and the agent's own interpretation.  
**Language of the KR:** Russian.  
**Language of this file:** English, deliberately directive.  
**Russian version:** `AGENT_RU.md` (same requirements; if they diverge, this file prevails).

---

## 0. Working mode (2026-10-25)

- Work **autonomously, without the advisor**. Consultation transcripts are historical context and design input, not blocking approval.
- The agent selects the topic, object, characteristics, and assumptions; decisions are recorded in `2026-10-25_topic-selection.md`.
- After each completed stage, **commit only that stage’s files**, without separate user approval. Do not push.
- Do not include unrelated working-tree changes in a commit.

---

## 0.1. One-sentence verdict

The existing model-selection report is a **technical study**, not an ergonomics KR. It remains a technical layer and data source, not the KR core. Renaming it “ergonomic” is forbidden.

---

## 0.2. Current working topic (2026-10-25)

**Working title:**

> **Ergonomic Support of Operator Activity in Detecting Anomalies of a Walking Robot**  
> «Эргономическое обеспечение деятельности оператора при обнаружении аномалий шагающего робота».

**Status:** selected autonomously; recorded in `2026-10-25_topic-selection.md`; formal model in `2026-10-25_formal-model.md`; no external approval required.

**Object:** the system “operator — information model of anomalies — walking robot”.

**Ergonomic core:** the joint activity of the operator and the technical subsystem in detecting an anomaly, assessing the situation, and deciding on a response. The information model must provide sufficient evidence for detection and action without false alarms or overload.

**KR path:** 1 — engineering/analytical.

**Working characteristics:**

1. Detection probability `P_det = 1 - Φ((λ - μ_S) / σ)`; acceptance `P_det ≥ P_req`.
2. False-alarm probability `P_fa = 1 - Φ((λ - μ_N) / σ)`; acceptance `P_fa ≤ α`.
3. Detection/response time `T_det = T_lat + T_search + T_dec + T_act`; acceptance `T_det ≤ T_req`.
4. Operator workload `K_load = (N_anom * T_det + N_fa * T_check) / T_shift`; acceptance `K_load ≤ K_req`.

**Selection rule:** all four constraints must hold; among admissible variants, maximize `P_det`, then minimize `T_det`, then minimize `P_fa`. Weights, expert scores, and Pareto are forbidden.

**Old report:** technical layer — `P_D`, `P_FA`, latency, confidence calibration, frames and scenes. It does not define the ergonomic characteristics.

---

## 1. Non-negotiable context

- The discipline is **“Ergonomics Analysis”** (эргономический анализ).
- The course project is a **course project in ergonomics**, not a course project in computer vision, machine learning, or model benchmarking.
- The advisor has explicitly rejected the substitution of technical model-selection metrics for ergonomic analysis.
- The advisor historically rejected attaching ergonomics through a screen, interface, hands, vision, or anthropometry. This is treated as a wording constraint, not as a blocking approval.
- The agent MUST NOT force the old topic if it cannot be made genuinely ergonomic.
- The agent MUST decompose claims to formulas, units, data, and measurable effects.

Key advisor formulations (cleaned from the 20.10.2026 transcript):

> “This is a normal technical analysis. Where is the ergonomics?”

> “The model has no screen. What are you confusing?”

> “Find ergonomic characteristics inside the machine-learning model.”

> “Performance/throughput lies on the surface. Calculate the performance of the ML model. Decompose it into atoms first.”

> “If you keep this topic, think carefully about which characteristics you will defend.”

> “Choose another topic. I do not object.”

---

## 1A. Study and confirmation materials (authoritative)

The course has a body of authoritative ergonomics materials. Before proposing a topic, an object, or an ergonomic characteristic, the agent MUST study them.

**Path:**

`/home/redalexdad/GitHub/BMSTU/1_семестр/ЭА_СОиОИ`

**Contents:**

- `Горячкин КР/КР по эргономике.pdf` — 22-slide KR methodology: two KR paths, stages, RPK milestones, RPZ structure, source requirements, formatting, and defense.
- `Горячкин КР/Темы КР 2026-2027.docx` — approved 2026–2027 topics, including AI, robotics, computer vision, and human-oriented AI directions.
- `Горячкин лекции/` — lectures 2–16 on ergonomics and human-machine systems: human-operator activity, functional diagnostics, information reception, visual and hearing analyzers, anthropometry, information models, interface structure, usability, expert evaluation, ergonomic expertise, and related topics.
- `Горячкин лекции/*.md` — RAG-ready text of the lectures, one file per lecture, with per-slide headings and Mermaid reconstructions of the schemes. The source PPSX remains authoritative for photographs, raster images, and exact visual layout.
- `Горячкин КР.zip`, `Горячкин лекции.zip` — archives; use the extracted files as the working copies.

**Authority hierarchy:**

1. The current user instruction: autonomous work and stage commits.
2. The KR methodology PDF and the approved topics DOCX.
3. The lecture materials.
4. Advisor consultations and the technical report — historical context, data, and constraints, not blocking approval.

The technical report/article MUST NOT override the methodology or the current topic decision.

**Approved AI/robotics-adjacent topics from the themes file** (candidates; the choice is recorded in the concept):

- «Место подсистем ИИ в контуре управления АСОИУ».
- «Подсистемы и звенья искусственного интеллекта, ориентированные на человека».
- «Эргономические датасеты как эффективный инструмент на ранних стадиях проектирования АСОИУ».
- «Коллаборативные роботы».
- «Интеллектуализация пользовательского интерфейса».
- «Оценка достоверности компьютерного зрения в системах контроля и управления доступом».
- «Системный анализ методов распределения функций между человеком и машиной».

These topics are evidence that the course accepts AI/robotics subjects only when they are framed through human activity, ergonomic support, information models, or operator interaction. They are not permission to submit a purely technical model comparison.

**Selected working topic (2026-10-25):** “Ergonomic Support of Operator Activity in Detecting Anomalies of a Walking Robot.” It concretizes approved topics #1 “Development of operator activity algorithms in the control loop,” #4 “Search and evaluation of new criteria and indicators of ergonomic support,” and #18 “The place of AI subsystems in the control loop.” Status: selected autonomously and recorded in the concept.

**Formal KR requirements from the methodology:**

- Choose and state the KR path:
  - **Path 1** — engineering/analytical: problem → task formalization → model/characteristics → evaluation → ergonomic expertise/certificate.
  - **Path 2** — system analysis/review: problem → literature/source base → analysis of methods and tools → conclusions → article for publication.
- RPZ volume: **25–30 pages** of A4 printed text, excluding appendices.
- Formatting: Times New Roman 14 pt, 1.5 spacing, paragraph indent 1.25 cm, margins 30/10/20/20 mm, 1800–2000 characters per page.
- For the review/article path: **25–30 sources**, internet sources no more than half, at least **20 in-text references**, at least **5 sources not older than 5 years**, 2–5 sources by BMSTU authors, DOI preferred, no more than 2 non-English sources.
- Milestones: RPK-1 week 3, RPK-2 week 6, RPK-3 week 8, RPK-4 week 14, RPK-5 week 16; stage control weeks 8 and 16; DZ week 15; defense weeks 16–17.
- RPZ structure must follow the chosen path; do not invent a different structure.
  - Path 1: title page, contents, introduction (software analysis), research part, evaluation/expertise, conclusion, sources, justification of results, appendices.
  - Path 2: title page, contents, introduction, methods/approaches, results/discussion, conclusion, sources, article prepared for publication.

The agent MUST use these materials to **confirm** that a proposed characteristic is ergonomic in the course’s sense, not merely to decorate a technical metric with an ergonomic label.

---

## 2. Definitions that MUST be used

### 2.1. Ergonomics

Ergonomics is the study of a **human–machine–environment system**: human activity, workload, tempo, errors, safety, comfort, and performance of the joint system. It is not a property of a model in isolation.

### 2.2. Object of analysis

The object MUST be one of the following and explicitly recorded in the concept:

1. **Operator–model–robot system**: the model is a component that changes the operator’s or robot’s activity.
2. **Operator–interface system**: the object is the interaction with detection results, alerts, or displays. This is allowed if the topic is explicitly framed as ergonomics of operator activity, not as ergonomics of the model.
3. **A narrowly defined model property that has a demonstrated human or robot effect** (for example, response tempo or reliability), with the mechanism stated explicitly.

The object “the model by itself, without a human or robot effect” is NOT a valid ergonomic object.

An “operator–information model–robot” system is treated as a concrete form of the operator–interface system; the topic must be explicitly named and justified in the concept.

### 2.3. Ergonomic characteristic

An ergonomic characteristic MUST satisfy all of the following:

- it is a number;
- it has a definition, a formula (or a measurement procedure), and units;
- it has a stated direction (“higher is better” or “lower is better”);
- it has an acceptability criterion or a comparison rule;
- it has a stated effect on human activity, operator workload, decision-making, trust, safety, or robot control;
- it is not merely a renamed technical metric;
- its data source is known (analytical model, experiment, or both).

If any item is missing, the characteristic is not ready for the KR.

---

## 3. Hard MUST / MUST NOT rules

### 3.1. Title and framing

- The title MUST contain an explicit ergonomic framing, for example:
  - “Эргономическое обоснование выбора модели машинного обучения…”
  - “Эргономические требования к модели обнаружения объектов…”
- The title MUST be ergonomically explicit and recorded in the concept before large-scale writing.
- The agent MUST NOT simply add the word “эргономическое” to the existing technical title without changing the content.
- The agent MUST NOT present the current technical report as the KR.

### 3.2. What is forbidden as “ergonomics”

The following MUST NOT be presented as ergonomic characteristics of the model:

- mAP, F1, precision, recall, IoU, ECE, FLOPs, parameter count, memory, latency, throughput, or Φ **by themselves**;
- “readability” of a screen or output;
- “convenience” of a user interface;
- hand position, vision, anthropometry, or workplace layout;
- model weight or file size as “performance”;
- expert scores, subjective weights, pairwise preference scores, or Pareto frontiers.

These may be used only as **technical constraints, inputs, or proxies**, and only when the ergonomic mechanism is separately defined and justified in the concept.

### 3.3. Required separation of layers

The KR MUST keep three layers separate:

1. **Technical layer** — architecture, FLOPs, parameters, memory, latency, mAP/F1, model constraints.
2. **Ergonomic layer** — human/robot effect, tempo, workload, reliability, decision certainty, safety, trust.
3. **Selection/decision layer** — the rule that converts the recorded characteristics into one choice.

The technical layer MUST NOT be used as a substitute for the ergonomic layer. The decision layer MUST NOT use subjective weights, expert scores, or Pareto frontiers.

### 3.4. Analytical-first rule

- The analytical calculation MUST come first.
- The experiment is a **confirmation/validation**, not the basis for selecting the model.
- The agent MUST show formulas and substitutions, not only measured tables.
- If the experiment contradicts the analytical result, the agent MUST report the contradiction and revise the analysis; it MUST NOT hide it.

### 3.5. No subjective aggregation

- Weights are forbidden.
- Pareto is forbidden as the selection method.
- Expert scores are forbidden.
- A deterministic rule with equal treatment of the recorded characteristics is required.
- If a criterion cannot be justified without subjective weights, it MUST be removed or reformulated.

### 3.6. Scope discipline

- Use 5–10 ready models, not “all AI”.
- Do not train models as part of the selection.
- Narrow the object to a specific task and a specific human/robot context.
- Do not expand into general philosophy of “human and technology”.

---

## 4. Mandatory pre-writing gate

Before writing KR chapters, the agent MUST produce a concept and pass the self-check in this section. No external approval is required.

The one-page concept MUST contain:

1. Working title.
2. Object of analysis (one of the three types in §2.2).
3. Human/robot role and the activity that is affected.
4. 3–5 candidate ergonomic characteristics.
5. For each candidate: definition, formula, units, direction, data source, and why it is ergonomic.
6. The proposed selection rule without weights/Pareto.
7. The proposed experiment/validation.
8. Open questions, assumptions, and how they will be checked.

The agent MUST NOT proceed to full chapters until the concept passes the self-check and is recorded in a commit.

### 4.1. One-page concept template

```text
Working title:
Object:
Human/robot role:
Affected activity:

Candidate characteristics:
| # | Name | Definition | Formula | Units | Direction | Data source | Why ergonomic | Acceptance |
|---|------|------------|---------|-------|-----------|-------------|---------------|------------|

Selection rule (no weights/Pareto):
Analytical calculation:
Experiment/validation:
Open questions:
```

### 4.2. Concept self-check

Before chapters, verify: the object is human–machine; each characteristic has a formula, units, direction, criterion, and effect; no weights/Pareto/expert scores; analytical calculation comes first; technical metrics are separated; the old report is not presented as the KR. Record the result in the concept and commit it.

---

## 5. Required KR structure

The KR MUST follow a structure in which ergonomics is the core, not a decoration.

1. **Introduction**
   - problem, relevance, object, subject, goal, tasks;
   - human/robot context;
   - practical significance;
   - explicit statement of what is ergonomic about the work.

2. **Ergonomic analysis of the activity/system**
   - operator/robot role;
   - workflow and decision points;
   - constraints, errors, workload, tempo, safety;
   - justification of the chosen ergonomic characteristics.

3. **Technical basis and model constraints**
   - models, architecture, FLOPs, memory, latency;
   - filters and technical limits;
   - explicit label: “technical layer, not the ergonomic rationale”.

4. **Ergonomic characteristics**
   - 3–5 characteristics only;
   - definition, formula, units, direction, acceptability criterion;
   - human/robot effect;
   - data source and calculation procedure;
   - distinction from technical proxies.

5. **Method of selection**
   - analytical calculation;
   - deterministic rule without weights/Pareto;
   - robustness checks;
   - explanation of why the rule matches the ergonomic objective.

6. **Experiment**
   - hypothesis and analytical baseline;
   - protocol, scenes/data, sample sizes;
   - metrics, confidence intervals, paired comparisons where possible;
   - limitations and domain dependence;
   - explicit separation of “confirmed”, “not confirmed”, and “not tested”.

7. **Results and discussion**
   - answer the research question;
   - compare analytical and experimental results;
   - report contradictions;
   - state applicability boundaries.

8. **Conclusion**
   - what was selected and why;
   - what was confirmed and what was not;
   - what remains for future work.

9. **Appendices**
   - calculations, tables, data paths, transcripts, additional plots.

---

## 6. Required specification for each ergonomic characteristic

Each characteristic MUST be documented with this template:

```text
Name:
Definition:
Formula / measurement procedure:
Units:
Direction:
Acceptance criterion:
Human/robot effect:
Why this is ergonomic (not merely technical):
Data source:
Calculation / measurement steps:
Relation to technical metrics:
Limitations:
```

The agent MUST reject a characteristic if the “Why this is ergonomic” field cannot be filled with a concrete mechanism.

---

## 7. Experiment rules

- The experiment MUST have a pre-stated hypothesis and an analytical baseline.
- The sample size, ground truth, and selection criteria MUST be reported.
- Report medians and p95/p99 for latency, not only the mean.
- Report confidence intervals where possible.
- Report paired comparisons when the same scenes/cases are used.
- Report domain splits; do not average incompatible domains silently.
- Report negative and null results.
- Do not claim “confirmed” when:
  - confidence intervals overlap and the sample is small;
  - the experiment does not cover the analytical scenarios;
  - the result reverses on another domain.
- Use precise wording:
  - “confirmed for the target scenes”;
  - “consistent with”;
  - “not tested”;
  - “not confirmed”;
  - “domain-dependent”.

Current experimental facts that MUST be respected:

- The Gazebo experiment covers 4 synthetic scenes with 16 objects each, 340 GT total.
- The 5/20/50 object scenarios were **not** run; the corresponding criteria remain analytical.
- F1, ECE, and p95 were measured only on `showroom`.
- The mean mAP@0.5 values are 0.475 (YOLO11n), 0.406 (YOLOv8s), 0.376 (YOLOv8n); 95% CIs overlap.
- The café and COCO128 domains produce different winners (YOLOv8n and YOLOv8s, respectively).
- Energy was not measured (RAPL unavailable); η and EDP are not verified.
- The experiment covers YOLO models only; CNN+LSTM, RT-DETR, and Faster R-CNN are analytical only.
- YOLOv8s analytical latency is 0.288 s at Π = 100 Gop/s; the README contains a conflicting 0.14 s value. Do not silently choose one; state the assumption.

---

## 8. Evidence and data rules

- Every number MUST have a traceable source: a formula, a table, a CSV/JSON path, or a citation.
- Never invent data, citations, or experimental results.
- Distinguish:
  - analytical estimate;
  - measured value;
  - proxy;
  - assumption;
  - unverified claim.
- Do not quote raw ASR as fact. The transcripts contain recognition errors and repetitions. Cross-check key statements across the chunked ASR, full ASR, and the provided Google DOCX.
- The private transcripts and audio are personal data. Do not publish them; cite only cleaned working formulations.

---

## 9. Topic decision gates

The topic is checked against the gates; the decision is recorded in the concept. No external approval is required.

### Gate 1 — Object

- If the object is “the model alone”, STOP: there is no ergonomic property without a human/robot relation.
- If the object is “operator–model–robot” or “operator–information model–robot”, proceed to Gate 2.
- If the object is “operator–interface”, it is allowed if the topic is explicitly framed as ergonomics of operator activity, not as ergonomics of the model.
- If the object is unclear, narrow it independently and record the assumption in the concept.

### Gate 2 — Characteristics

- If a characteristic has no formula/units/acceptance criterion, STOP.
- If its “why ergonomic” is only “it is convenient” or “it is readable”, STOP.
- If it is only a technical metric renamed, STOP.

### Gate 3 — Method

- If the method uses weights, expert scores, or Pareto, STOP.
- If the analytical calculation is missing and only experiments remain, STOP.

### Gate 4 — Experiment

- If the experiment does not test the recorded characteristics, label it as “technical validation” only.
- If the experiment covers only 16-object scenes, do not claim 5/20/50 validation.

### Gate 5 — Text

- Do not write full chapters before Gates 1–3 are passed.
- Record decisions and assumptions in the concept; commit the stage.
- No external approval is required.

---

## 10. Prohibited patterns (hard fail)

The following are automatic failures:

- Calling the current technical model-selection report an ergonomics KR.
- Adding “эргономическое” to the title without changing the content.
- Calling mAP/F1/FLOPs/Φ “ergonomic characteristics”.
- Using screen/UI/readability/anthropometry as model ergonomics without an explicit topic change recorded in the concept.
- Using “model weight” as performance.
- Using subjective weights, expert scores, or Pareto.
- Claiming “the experiment fully confirmed the analysis”.
- Claiming 5/20/50 scenarios were tested when they were not.
- Hiding overlapping confidence intervals or domain reversals.
- Inventing numbers, sources, or facts.
- Publishing private audio/transcripts.

---

## 11. Current artifacts: status

| Artifact | Status | Use |
| --- | --- | --- |
| `2026-10-25_topic-selection.md` | Working topic, ergonomic core, and concept | KR basis; selected autonomously |
| `2026-10-25_formal-model.md` | Formal core model and characteristics | Stage 2; calculation basis |
| `2026-10-13_model-selection.md` | Technical report; not a KR | Technical appendix and source of IM frames |
| `2026-10-13_model-selection.html` | Printable technical report | Technical appendix only |
| `2026-10-19_consultation-brief.*` | Technical summary | Not an ergonomics plan |
| `docs/publications/IIASU_2026/article.*` | Technical article | Separate publication; not the KR |
| `2026-10-13_consultation-goryachkin.md` | Prior consultation summary with a 20.10 correction note | Context |
| `2026-10-20_consultation-goryachkin.md` | Consultation analysis | Historical context and requirements |
| `private/2026-10-20/` | Audio and raw transcripts | Evidence; do not publish |

---

## 12. Definition of done

The KR is not done until all of the following are true:

- [ ] The topic, object, and characteristics are recorded in the concept and pass the self-check.
- [ ] The ergonomic characteristics (3–5) have formulas, units, and criteria.
- [ ] The analytical calculation is present and reproducible.
- [ ] The selection rule contains no weights, expert scores, or Pareto.
- [ ] The experiment is described as validation, not as the basis.
- [ ] The experiment’s limitations and domain dependence are explicit.
- [ ] The text states what was confirmed, what was not, and what was not tested.
- [ ] Technical metrics are clearly separated from ergonomic characteristics.
- [ ] No prohibited pattern from §10 is present.
- [ ] Historical advisor feedback is addressed or explicitly rejected with a rationale.

---

## 13. Stop conditions and procedure

If any of the following occurs, the agent does NOT wait for external approval:

- the only proposed characteristics are technical metrics;
- the object of analysis is unclear;
- the topic must be changed;
- the available data cannot support the claimed ergonomic effect;
- the agent is asked to “just rename” the technical report;
- the agent is asked to use weights/Pareto/expert scores;
- the agent cannot distinguish measured, calculated, and assumed values.

Procedure: stop, record the problem in the concept, narrow the object or choose a conservative solution, add a validation experiment if needed, and commit the stage. Inventing an ergonomic rationale is forbidden.

---

## 14. Stage commits

After each completed stage:

1. Verify that only files for this stage are changed.
2. Commit them without separate user approval, following the project commit rules.
3. Do not push without a separate instruction.
4. Do not include unrelated working-tree changes.

Stages: topic and core → formal model and characteristics → calculation/experiment → KR text → final check and defense.
