# Верификация источников — Глава 2

Цель: подтвердить DOI/URL для всех 20 источников списка литературы в `title.md` (НИР-3, глава 2 «Методы»).
Проверка выполнена 12.11.2026 через Crossref REST API (`api.crossref.org/works/<DOI>`) и doi.org Handle API (`doi.org/api/handles/<DOI>`); названия и издания сверены с ответом API.

---

## Статус

| # | Источник | Статус | DOI/URL |
|---|----------|--------|---------|
| 1 | Belter et al. — RGB–D Terrain Perception and Dense Mapping (IJAMCS 2016) | ✅ | `10.1515/amcs-2016-0006` |
| 2 | Dong et al. — MARG (IEEE Transactions on Robotics 2025) | ✅ | `10.1109/TRO.2025.3619041` |
| 3 | Erni et al. — MEM (IROS 2023) | ✅ | `10.1109/IROS55552.2023.10342108` |
| 4 | Fankhauser — PhD Thesis (ETH Zurich 2018) | 🔍 | DOI не найден (см. детали) |
| 5 | Fankhauser & Hutter — grid_map (Springer 2016) | ✅ | `10.1007/978-3-319-26054-9_5` |
| 6 | Fankhauser et al. — Robot-Centric Elevation Mapping (CLAWAR 2014) | ✅ | `10.1142/9789814623353_0051` |
| 7 | Fu et al. — Traversability Analysis of Quadruped Robot (RCAR 2022) | ✅ | `10.1109/RCAR54675.2022.9872233` |
| 8 | Himmelsbach et al. — Fast Segmentation of 3D Point Clouds for Ground Vehicles (IV 2010) | ✅ | `10.1109/IVS.2010.5548059` |
| 9 | Homberger et al. — Support Surface Estimation for Legged Robots (ICRA 2019) | ✅ | `10.1109/ICRA.2019.8793646` |
| 10 | Macenski et al. — The Marathon 2 (IROS 2020) | ✅ | `10.1109/IROS45743.2020.9341207` |
| 11 | Marder-Eppstein et al. — The Office Marathon (ICRA 2010) | ✅ | `10.1109/ROBOT.2010.5509725` |
| 12 | Miki et al. — Elevation Mapping for Locomotion and Navigation using GPU (IROS 2022) | ✅ | `10.1109/IROS47612.2022.9981507` |
| 13 | Pan et al. — GPU Accelerated Real-Time Traversability Mapping (ROBIO 2019) | ✅ | `10.1109/ROBIO49542.2019.8961816` |
| 14 | Wermelinger et al. — Navigation Planning for Legged Robots in Challenging Terrain (IROS 2016) | ✅ | `10.1109/IROS.2016.7759199` |
| 15 | Zermas et al. — Fast Segmentation of 3D Point Clouds: A Paradigm on LiDAR Data… (ICRA 2017) | ✅ | `10.1109/ICRA.2017.7989591` |
| 16 | Unitree Go2 Technical Documentation (2024) | 📝 | URL: https://www.unitree.com/go2/ |
| 17 | ROS 2 Jazzy Documentation | 📝 | URL: https://docs.ros.org/en/jazzy/ |
| 18 | Eclipse Cyclone DDS Documentation | 📝 | URL: https://cyclonedds.io/ |
| 19 | Gazebo Harmonic Documentation | 📝 | URL: https://gazebosim.org/docs/harmonic |
| 20 | NVIDIA CUDA Toolkit Documentation (2024) | 📝 | URL: https://docs.nvidia.com/cuda/ |

**Легенда:**

- ✅ — DOI подтверждён по Crossref, название и издание сверены с ответом API; для №2 подтверждён сам номер DOI через реестр doi.org, метаданные сверены не полностью (см. детали);
- 📝 — URL известен, доступность и дата обращения проверяются при сборке ВКР;
- 🔍 — DOI не найден.

---

## Детали поиска

### №15 — Zermas et al. (ICRA 2017): исправлены название и конференция

В списке НИР-2 работа была указана как «Fast segmentation of 3D point clouds for ground vehicles», IEEE Intelligent Vehicles Symposium (IV), 2017. По данным Crossref точное название статьи — **«Fast segmentation of 3D point clouds: A paradigm on LiDAR data for autonomous vehicle applications»**, издание — **2017 IEEE International Conference on Robotics and Automation (ICRA)**, DOI `10.1109/ICRA.2017.7989591`. В библиографию НИР-3 внесены исправленные название и конференция.

### №8 — Himmelsbach et al. (IV 2010): подтверждено

По данным Crossref: «Fast segmentation of 3D point clouds for ground vehicles», издание — **2010 IEEE Intelligent Vehicles Symposium (IV)**, год 2010, DOI `10.1109/IVS.2010.5548059`. Название, авторы и издание совпадают со списком.

### №2 — Dong et al. (TRO 2025): DOI резолвится, Crossref API не ответил

DOI `10.1109/TRO.2025.3619041` зарегистрирован в doi.org (Handle API, регистрация 07.10.2025) и резолвится на `https://ieeexplore.ieee.org/document/11196002/`. Запрос метаданных Crossref API по этому DOI в сеансе проверки завершался без ответа (HTTP 000) при повторных попытках, поэтому название и авторы приняты по исходному списку: статус ✅ для №2 подтверждает номер DOI и его резолвинг, а не сверку метаданных. При сборке ВКР рекомендуется повторная сверка карточки IEEE Xplore.

### №4 — Fankhauser, PhD Thesis (ETH Zurich 2018): DOI не найден

- DOI в Crossref не присвоен: поиск по bibliographic-запросу совпадений не дал.
- Название **«Perceptive Locomotion for Legged Robots in Rough Terrain»** восстановлено по вторичным источникам (списки литературы работ лаборатории; в списке НИР-2 фигурировало название «Elevation Mapping for Locomotion of Rough Terrain Robots»).
- ETH Research Collection: handle `20.500.11850/297653` (страница загружается, метаданные без JS не извлекаются — по данным `sources_verify_ch3.md`).
- Для ВКР рекомендуется ссылка на ETH Research Collection без DOI.

### №1, 3, 5–7, 9–14 — подтверждены по Crossref

Названия, авторы, годы и издания совпадают со списком НИР-3. Уточнения по изданиям:

- №5 — глава в книге Robot Operating System (ROS), Springer, 2016; в Crossref контейнер указан как Studies in Computational Intelligence (том 625);
- №6 — глава в сборнике Mobile Service Robotics (труды CLAWAR 2014), 2014;
- №3 — IROS 2023, страницы 11011–11018.

### №16–20 — документация и веб-ресурсы

DOI не присвоен; в списке указаны URL. Статус 📝: адреса известны, доступность и дата обращения (10.05.2026) подлежат проверке при сборке ВКР.

---

## Исключённые источники

Из библиографии НИР-3 исключены две позиции, присутствовавшие в списке НИР-2 и не подтверждённые при верификации:

- **Okada K. et al.** GPU-Accelerated Elevation Mapping for Legged Robots // IEEE Robotics and Automation Letters. — 2023. — DOI не найден, совпадений в Crossref и arXiv не обнаружено (по данным `sources_verify_ch3.md`).
- **Wang C. et al.** Traversability Analysis for Legged Robots in Rough Terrain // IEEE ICRA. — 2023. — DOI не найден, совпадений в Crossref не обнаружено (по данным `sources_verify_ch3.md`).

Ближайшие по теме подтверждённые работы — Miki et al. [12] и Fu et al. [7]; в главе 2 используются они.

---

## О нумерации

Нумерация источников в НИР-3 локальная (1–20) и относится только к главе 2. При сборке ВКР нумерация будет унифицирована по сквозному списку литературы; ссылки в тексте главы ([5], [12], [15], [18] и др.) на данном этапе соответствуют локальному списку из `title.md`.
