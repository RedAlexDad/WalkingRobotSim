# Верификация источников — Глава 3

Цель: найти и подтвердить DOI/URL для всех 13 источников списка литературы в `title.md`.
После верификации ВСЕХ источников — массово внести правки в `title.md`.

---

## Статус

| # | Источник | Статус | DOI/URL |
|---|----------|--------|---------|
| 1 | Fankhauser & Hutter — grid_map (Springer 2016) | ✅ | `10.1007/978-3-319-26054-9_5` |
| 2 | Zermas et al. — GPF (в bib: IV 2017, факт: ICRA 2017) | ✅ | `10.1109/ICRA.2017.7989591` ⚠️ конференцию поправить на ICRA |
| 3 | Marder-Eppstein — Office Marathon (ICRA 2010) | ✅ | `10.1109/ROBOT.2010.5509725` |
| 4 | Fankhauser et al. — CLAWAR 2014 | ✅ | `10.1142/9789814623353_0051` |
| 5 | Fankhauser — PhD thesis (ETH 2018) | 🔍 | не найден |
| 6 | Unitree Go2 Documentation | 📝 | URL: https://www.unitree.com/go2/ |
| 7 | ROS 2 Jazzy Documentation | ✅ | URL: https://docs.ros.org/en/jazzy/ |
| 8 | Cyclone DDS Documentation | ✅ | URL: https://cyclonedds.io/ |
| 9 | Gazebo Harmonic Documentation | ✅ | URL: https://gazebosim.org/docs/harmonic |
| 10 | NVIDIA CUDA Toolkit Documentation | 📝 | URL: https://docs.nvidia.com/cuda/ |
| 11 | Okada K. et al. — GPU-Accelerated Elevation Mapping (RA-L 2023) | 🔍 | не найден |
| 12 | Wang C. et al. — Traversability Analysis (ICRA 2023) | 🔍 | не найден |
| 13 | Macenski et al. — Marathon 2 (IROS 2020) | ✅ | `10.1109/IROS45743.2020.9341207` |

**Легенда:**
- ✅ — DOI/URL подтверждён через Crossref
- 📝 — URL известен, требуется проверка доступности
- 🔍 — в процессе поиска

---

## Детали поиска

### #5 — Fankhauser PhD thesis (ETH 2018)
- Название в bib: "Elevation Mapping for Locomotion of Rough Terrain Robots"
- Название из ссылок ICRA 2018: "Perceptive Locomotion for Legged Robots in Rough Terrain"
- Поиск в Crossref API: не найден (нет DOI в Crossref)
- ETH handle `20.500.11850/297653`: страница загружается, метаданные не извлекаются (JS-зависимая)
- ETH handle `10.3929/ethz-b-000489726` (из ссылок Miki et al. 2022): 404 в Crossref
- Что пробовать: Semantic Scholar, ResearchGate, ETH Research Collection REST

### #11 — Okada K. — GPU-Accelerated Elevation Mapping (RA-L 2023)
- Поиск в Crossref API (название+автор Okada): не найдено
- arXiv: пусто
- IEEE Xplore: login shell (JS)
- Ближайшая работа: Miki et al. "Elevation Mapping for Locomotion and Navigation using GPU" (IROS 2022, DOI `10.1109/iros47612.2022.9981507`)
- Что пробовать: Semantic Scholar, IEEE Xplore API, RA-L 2023 TOC

### #12 — Wang C. — Traversability Analysis (ICRA 2023)
- Поиск в Crossref API (название+автор Wang): не найдено
- arXiv: пусто
- IEEE Xplore: login shell (JS)
- Что пробовать: Semantic Scholar, ICRA 2023 proceedings

---

---

## Список литературы в едином формате

1.	Fankhauser, P., & Hutter, M. (2016). "A Universal Grid Map Library: Implementation and Use Case for Rough Terrain Navigation." Robot Operating System (ROS). Springer. https://doi.org/10.1007/978-3-319-26054-9_5

2.	Zermas, D., Izzat, I., & Papanikolopoulos, N. (2017). "Fast Segmentation of 3D Point Clouds for Ground Vehicles." IEEE International Conference on Robotics and Automation (ICRA). https://doi.org/10.1109/ICRA.2017.7989591 *(в оригинале bib указано IV 2017 — исправить на ICRA)*

3.	Marder-Eppstein, E., Berger, E., Foote, T., Gerkey, B., & Wise, K. (2010). "The Office Marathon: Robust Navigation in an Indoor Office Environment." IEEE International Conference on Robotics and Automation (ICRA). https://doi.org/10.1109/ROBOT.2010.5509725

4.	Fankhauser, P. et al. (2014). "Robot-Centric Elevation Mapping with Uncertainty Estimates." International Conference on Climbing and Walking Robots (CLAWAR). https://doi.org/10.1142/9789814623353_0051

5.	Fankhauser, P. (2018). "Elevation Mapping for Locomotion of Rough Terrain Robots." PhD Thesis, ETH Zurich. *(DOI не найден)*

6.	Unitree Robotics (2024). "Go2 Technical Documentation." https://www.unitree.com/go2/

7.	Open Robotics (2026). "ROS 2 Jazzy Documentation." https://docs.ros.org/en/jazzy/

8.	Eclipse Foundation (2026). "Cyclone DDS Documentation." https://cyclonedds.io/

9.	Open Robotics (2026). "Gazebo Harmonic Documentation." https://gazebosim.org/docs/harmonic

10.	NVIDIA Corporation (2024). "CUDA Toolkit Documentation." https://docs.nvidia.com/cuda/

11.	Okada, K. et al. (2023). "GPU-Accelerated Elevation Mapping for Legged Robots." IEEE Robotics and Automation Letters. *(DOI не найден)*

12.	Wang, C. et al. (2023). "Traversability Analysis for Legged Robots in Rough Terrain." IEEE International Conference on Robotics and Automation (ICRA). *(DOI не найден)*

13.	Macenski, S., Martín, F., White, R., & Clavero, J. (2020). "The Marathon 2: A Navigation System." IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). https://doi.org/10.1109/IROS45743.2020.9341207

14.	Miki, T., Wellhausen, L., Grandia, R., Jenelten, F., Homberger, T., & Hutter, M. (2022). "Elevation Mapping for Locomotion and Navigation using GPU." 2022 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). https://doi.org/10.1109/IROS47612.2022.9981507

15.	Erni, G., Frey, J., Miki, T., Mattamala, M., & Hutter, M. (2023). "MEM: Multi-Modal Elevation Mapping for Robotics and Learning." 2023 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). https://doi.org/10.1109/IROS55552.2023.10342108

16.	Dong, Y., Ma, J., Zhao, L., Li, W., & Lu, P. (2025). "MARG: MAstering Risky Gap Terrains for Legged Robots With Elevation Mapping." IEEE Transactions on Robotics. https://doi.org/10.1109/TRO.2025.3619041

17.	Belter, D., Łabecki, P., Fankhauser, P., & Siegwart, R. (2016). "RGB–D Terrain Perception and Dense Mapping for Legged Robots." International Journal of Applied Mathematics and Computer Science, Vol 26, Issue 1. https://doi.org/10.1515/amcs-2016-0006

18.	Wermelinger, M., Fankhauser, P., Diethelm, R., Krüsi, P., Siegwart, R., & Hutter, M. (2016). "Navigation Planning for Legged Robots in Challenging Terrain." 2016 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). https://doi.org/10.1109/IROS.2016.7759199

19.	Homberger, T., Wellhausen, L., Fankhauser, P., & Hutter, M. (2019). "Support Surface Estimation for Legged Robots." 2019 International Conference on Robotics and Automation (ICRA). https://doi.org/10.1109/ICRA.2019.8793646

20.	Fu, Y., Xu, M., Kong, Y., Zhang, X., Wang, C., & Song, R. (2022). "Traversability Analysis of Quadruped Robot Based on Sparse Point Cloud in Rough Terrain." 2022 IEEE International Conference on Real-time Computing and Robotics (RCAR). https://doi.org/10.1109/RCAR54675.2022.9872233

21.	Pan, Y., Xu, X., Wang, Y., Ding, X., & Xiong, R. (2019). "GPU Accelerated Real-Time Traversability Mapping." 2019 IEEE International Conference on Robotics and Biomimetics (ROBIO). https://doi.org/10.1109/ROBIO49542.2019.8961816

## Задачи
1. Найти DOI для #5, #11, #12 через Semantic Scholar / ResearchGate / IEEE Xplore API
2. Проверить доступность URL для #6 (Unitree) и #10 (CUDA)
3. После верификации всех — массово отредактировать `title.md`

## Cписок в формате ГОСТ для title.md (существующие 13 + новые 8)

1. Fankhauser P., Hutter M. A Universal Grid Map Library: Implementation and Use Case for Rough Terrain Navigation // Robot Operating System (ROS). — Springer, 2016. — DOI: 10.1007/978-3-319-26054-9_5
2. Zermas D., Izzat I., Papanikolopoulos N. Fast Segmentation of 3D Point Clouds for Ground Vehicles // IEEE International Conference on Robotics and Automation (ICRA). — 2017. — DOI: 10.1109/ICRA.2017.7989591 *(исправить с IV на ICRA)*
3. Marder-Eppstein E., Berger E., Foote T., Gerkey B., Wise K. The Office Marathon: Robust Navigation in an Indoor Office Environment // IEEE International Conference on Robotics and Automation (ICRA). — 2010. — DOI: 10.1109/ROBOT.2010.5509725
4. Fankhauser P., et al. Robot-Centric Elevation Mapping with Uncertainty Estimates // International Conference on Climbing and Walking Robots (CLAWAR). — 2014. — DOI: 10.1142/9789814623353_0051
5. Fankhauser P. Elevation Mapping for Locomotion of Rough Terrain Robots // PhD Thesis, ETH Zurich. — 2018. *(DOI не найден)*
6. Unitree Go2 Technical Documentation. — Unitree Robotics, 2024. — URL: https://www.unitree.com/go2/
7. Open Robotics. ROS 2 Jazzy Documentation [Электронный ресурс]. — Режим доступа: https://docs.ros.org/en/jazzy/ (дата обращения: 10.05.2026)
8. Eclipse Cyclone DDS Documentation [Электронный ресурс]. — Режим доступа: https://cyclonedds.io/ (дата обращения: 10.05.2026)
9. Open Robotics. Gazebo Harmonic Documentation [Электронный ресурс]. — Режим доступа: https://gazebosim.org/docs/harmonic (дата обращения: 10.05.2026)
10. NVIDIA CUDA Toolkit Documentation. — NVIDIA Corporation, 2024. — URL: https://docs.nvidia.com/cuda/
11. Okada K. et al. GPU-Accelerated Elevation Mapping for Legged Robots // IEEE Robotics and Automation Letters. — 2023. *(DOI не найден)*
12. Wang C. et al. Traversability Analysis for Legged Robots in Rough Terrain // IEEE International Conference on Robotics and Automation (ICRA). — 2023. *(DOI не найден)*
13. Macenski S., Martín F., White R., Clavero J. The Marathon 2: A Navigation System // IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). — 2020. — DOI: 10.1109/IROS45743.2020.9341207
14. Miki T., Wellhausen L., Grandia R., Jenelten F., Homberger T., Hutter M. Elevation Mapping for Locomotion and Navigation using GPU // IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). — 2022. — DOI: 10.1109/IROS47612.2022.9981507
15. Erni G., Frey J., Miki T., Mattamala M., Hutter M. MEM: Multi-Modal Elevation Mapping for Robotics and Learning // IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). — 2023. — DOI: 10.1109/IROS55552.2023.10342108
16. Dong Y., Ma J., Zhao L., Li W., Lu P. MARG: MAstering Risky Gap Terrains for Legged Robots With Elevation Mapping // IEEE Transactions on Robotics. — 2025. — DOI: 10.1109/TRO.2025.3619041
17. Belter D., Łabecki P., Fankhauser P., Siegwart R. RGB–D Terrain Perception and Dense Mapping for Legged Robots // International Journal of Applied Mathematics and Computer Science. — 2016. — DOI: 10.1515/amcs-2016-0006
18. Wermelinger M., Fankhauser P., Diethelm R., Krüsi P., Siegwart R., Hutter M. Navigation Planning for Legged Robots in Challenging Terrain // IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). — 2016. — DOI: 10.1109/IROS.2016.7759199
19. Homberger T., Wellhausen L., Fankhauser P., Hutter M. Support Surface Estimation for Legged Robots // IEEE International Conference on Robotics and Automation (ICRA). — 2019. — DOI: 10.1109/ICRA.2019.8793646
20. Fu Y., Xu M., Kong Y., Zhang X., Wang C., Song R. Traversability Analysis of Quadruped Robot Based on Sparse Point Cloud in Rough Terrain // IEEE International Conference on Real-time Computing and Robotics (RCAR). — 2022. — DOI: 10.1109/RCAR54675.2022.9872233
21. Pan Y., Xu X., Wang Y., Ding X., Xiong R. GPU Accelerated Real-Time Traversability Mapping // IEEE International Conference on Robotics and Biomimetics (ROBIO). — 2019. — DOI: 10.1109/ROBIO49542.2019.8961816
