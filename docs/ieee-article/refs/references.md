# Ссылки статьи (источник истины) — PIERE 2026 / IEEE

**Обновлено:** 2026-09-13
**Связано с:** `docs/ieee-article/draft-article.md` (раздел References)

Ниже — все ссылки статьи с каноническими линками (arXiv / DOI / URL) и
отметкой наличия локальной копии в этой папке.

## Локальные копии (скачаны)

| № | Работа | Линк | Локально |
|---|---|---|---|
| 8 | Isaac Gym: GPU-based Physics Simulation for Robot Learning | arXiv:2108.10470 · DOI:10.48550/arXiv.2108.10470 | `2108.10470.full.md` |
| 12 | Benchmarking MPC and RL for Legged Robot Locomotion in MuJoCo | arXiv:2501.16590 · DOI:10.48550/arXiv.2501.16590 | `2501.16590.full.md` |
| 13 | Kine2Go: A kinematic dataset for the Unitree Go2 | arXiv:2606.14433 · DOI:10.48550/arXiv.2606.14433 | `2606.14433.full.md` |
| 14 | Isaac Sim-to-Real: RL-based Locomotion for Quadrupeds | arXiv:2607.18135 · DOI:10.48550/arXiv.2607.18135 | `2607.18135.full.md` |

## Классические работы (книги/журналы/конференции, без локальной копии)

| № | Работа | Линк |
|---|---|---|
| 1 | M. H. Raibert, *Legged Robots That Balance*, MIT Press, 1986 | ISBN 978-0262181171 |
| 2 | B. Katz, J. Di Carlo, S. Kim, "Mini Cheetah...", ICRA 2019 | DOI:10.1109/ICRA.2019.8793868 |
| 3 | J. Hwangbo et al., "Learning agile and dynamic motor skills...", Science Robotics 4(26), 2019 | DOI:10.1126/scirobotics.aau5872 |
| 4 | J. Lee et al., "Learning quadrupedal locomotion over challenging terrain", Science Robotics 5(47), 2020 | DOI:10.1126/scirobotics.abc5986 |
| 5 | T. Miki et al., "Learning robust perceptive locomotion...", Science Robotics 7(62), 2022 | DOI:10.1126/scirobotics.abk2822 |
| 6 | N. Rudin et al., "Learning to walk in minutes...", CoRL 2021 | arXiv:2109.11978 |
| 7 | J. M. Jimeno, "CHAMP", GitHub, 2021 | https://github.com/chvmp/champ |
| 15 | G. Bledt et al., "MIT Cheetah 3...", IROS 2018 | DOI:10.1109/IROS.2018.8593885 |

## Документация

| № | Источник | Линк |
|---|---|---|
| 9 | NVIDIA Isaac Lab | https://isaac-sim.github.io/IsaacLab |
| 10 | NVIDIA Isaac Sim | https://docs.isaacsim.omniverse.nvidia.com |
| 11 | Unitree Go2 / SDK | https://www.unitree.com/go2 |

## Как получить локальные копии

```bash
python3 scripts/fetch_arxiv_refs.py --out docs/ieee-article/refs \
  2108.10470 2501.16590 2606.14433 2607.18135
```

## Примечания

- DOI классических работ приведены по каноническим изданиям; при подаче
  сверить с Crossref.
- ID `2607.18135` необычен (код года `2607`), но страница arXiv
  открывается; перед цитированием проверить.
- Классические работы (Raibert, Science Robotics, ICRA/IROS) в открытом
  доступе отсутствуют — локальные копии не хранятся.
