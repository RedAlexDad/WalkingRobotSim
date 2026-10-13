#!/usr/bin/env python3
"""Выбор модели МО для распознавания объектов оператору мобильного робота.

Единый расчётный скрипт: считает все величины и таблицы отчёта
`docs/ergonomics-methodology/2026-10-13_model-selection.md`
(§9 «Расчёты», §10 «Варианты выигрыша II и III», §11 «Итоговый расчёт»).

Запуск:
    .venv-model-selection/bin/python model-selection.py
или:
    uv run --with numpy --with pandas python model-selection.py

Все входные данные — из источников (спецификации Ultralytics) либо
аналитика; «на глаз» числа не задаются.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from tabulate import tabulate

# ----------------------------------------------------------------------------
# Параметры (модельные допущения — вынесены отдельно, чтобы было видно)
# ----------------------------------------------------------------------------
Pi = 100.0    # производительность вычислителя робота, Гоп./с
P_pow = 10.0  # мощность вычислителя, Вт
alpha = 1e-3  # стоимость постобработки, Г на объект^2
T_max = 0.1   # порог задержки (реальное время), с
M_max = 64.0  # лимит памяти борта, МБ
tau = 0.1     # такт робота (для DF), с
states = [5, 20, 50]  # объектов в сцене theta1/theta2/theta3

# ----------------------------------------------------------------------------
# Данные моделей (источники: спецификации Ultralytics / расчёт)
# ----------------------------------------------------------------------------
rows = [
    # model,        family,          P(млн), F(Г),  mAP,  layers, out
    ("YOLO11n",     "1-stage CNN",    2.62,   6.6,   39.5, 181,    "box"),
    ("YOLOv8n",     "1-stage CNN",    3.16,   8.9,   37.3, 129,    "box"),
    ("YOLO11s",     "1-stage CNN",    9.46,  21.7,   47.0, 181,    "box"),
    ("YOLOv8s",     "1-stage CNN",   11.17,  28.8,   44.9, 129,    "box"),
    ("RT-DETR-l",   "transformer",   32.0,  103.5,   53.0, np.nan, "box"),
    ("Faster R-CNN", "2-stage CNN",  41.5,  180.0,   37.4, 100,    "box"),
    ("CNN+LSTM",    "CNN+recurrent",  3.15,   6.61,  39.5, 181,    "box"),
]
df = pd.DataFrame(rows, columns=["model", "family", "P", "F", "mAP", "layers", "out"])
df = df.set_index("model")

# Базовая задержка T = F/Pi; у рекуррентной модели — штраф за
# последовательную обработку во времени (см. отчёт, §9.0).
T_base = df["F"] / Pi
T_base["CNN+LSTM"] = 0.070

# Производные характеристики (§9.0)
df["M"] = 4.0 * df["P"]          # память весов, МБ (при float32)
df["T"] = T_base                 # задержка на кадр, с
df["f"] = 1.0 / T_base           # частота, Гц
df["E"] = 1.0 / df["F"]          # эффективность, 1/Г
df["Q"] = P_pow * T_base         # энергия на кадр, Дж


def md_table(frame: pd.DataFrame, index_name: str = "Модель") -> str:
    """Таблица (markdown) через tabulate (для вставки в отчёт)."""
    t = frame.reset_index()
    t.columns = [index_name, *list(t.columns[1:])]
    return tabulate(t, headers="keys", tablefmt="github", floatfmt=".3f",
                    missingval="—", disable_numparse=False)


def show(title: str, frame: pd.DataFrame, index_name: str = "Модель") -> None:
    print(f"\n### {title}")
    print(md_table(frame, index_name))


# ============================================================================
# §9.0. Производные характеристики
# ============================================================================
show(
    "§9.0. Производные характеристики",
    df[["P", "F", "M", "T", "f", "E", "Q"]].round(3),
    index_name="Модель",
)

# ============================================================================
# §9.1. Фильтры
# ============================================================================
df["pass_T"] = df["T"] <= T_max
df["pass_M"] = df["M"] <= M_max
df["pass_out"] = df["out"] == "box"
admissible = df.index[df[["pass_T", "pass_M", "pass_out"]].all(axis=1)].tolist()
print(f"\n### §9.1. Допустимые модели: {admissible}")

sub = df.loc[admissible]

# ============================================================================
# §9.2. Матрица выигрышей (частота по сценам)
# ============================================================================
def payoff(frame: pd.DataFrame) -> pd.DataFrame:
    """f = 1 / (T_base + alpha*N^2/Pi)."""
    return pd.DataFrame(
        {f"theta={N}": 1.0 / (T_base[frame.index] + alpha * N**2 / Pi) for N in states},
        index=frame.index,
    )


A = payoff(sub)
show("§9.2. Матрица выигрышей (частота, Гц)", A.round(3))

# ============================================================================
# §8 / §9.3. Критерии принятия решений
# ============================================================================
def laplace(a: pd.DataFrame) -> pd.Series:
    return a.mean(axis=1)


def optimism(a: pd.DataFrame) -> pd.Series:
    return a.max(axis=1)


def wald(a: pd.DataFrame) -> pd.Series:
    return a.min(axis=1)


def regret(a: pd.DataFrame) -> pd.Series:
    return (a.max(axis=0) - a).max(axis=1)


def hurwitz(a: pd.DataFrame, al: float) -> pd.Series:
    return al * a.max(axis=1) + (1 - al) * a.min(axis=1)


lap, opt, wal, reg = laplace(A), optimism(A), wald(A), regret(A)
crit = pd.DataFrame({
    "Лаплас": lap, "Оптимизм": opt, "Вальд": wal,
    "Сэвидж": reg, "Гурвиц(a=0.5)": hurwitz(A, 0.5),
})
show("§8/§9.3. Критерии (значения)", crit.round(3))

# ============================================================================
# §9.4. Подсчёт баллов
# ============================================================================
def points(values: pd.Series, lower_is_better: bool = False) -> pd.Series:
    r = values.rank(ascending=lower_is_better, method="min")
    return len(values) - r + 1


total = (points(lap) + points(opt) + points(wal)
         + points(reg, lower_is_better=True) + points(hurwitz(A, 0.5)))
points_tbl = total.astype(int).sort_values(ascending=False).to_frame("Баллы")
show("§9.4. Сумма баллов (по 5 критериям)", points_tbl)

# ============================================================================
# §10.1. Вариант II — баланс «скорость/точность»
# ============================================================================
B = A.mul(sub["mAP"], axis=0) / 100.0
show("§10.1. Вариант II (mAP*f/100)", B.round(3))

crit_B = pd.DataFrame({
    "Лаплас": laplace(B), "Оптимизм": optimism(B), "Вальд": wald(B),
    "Сэвидж": regret(B), "Гурвиц(a=0.5)": hurwitz(B, 0.5),
})
show("§10.1. Вариант II — критерии", crit_B.round(3))

# ============================================================================
# §10.2. Вариант III — показатель Phi
# ============================================================================
phi_chars = [("P", False), ("F", False), ("M", False), ("T", False),
             ("f", True), ("E", True), ("Q", False)]


def phi(frame: pd.DataFrame) -> pd.Series:
    z = pd.DataFrame(index=frame.index)
    for name, bigger in phi_chars:
        x = frame[name]
        lo, hi = x.min(), x.max()
        z[name] = (x - lo) / (hi - lo) if bigger else (hi - x) / (hi - lo)
    return z.mean(axis=1)


phi_vals = phi(sub).sort_values(ascending=False).to_frame("Phi")
show("§10.2. Показатель Phi", phi_vals.round(3))

# ============================================================================
# §10.3. Новые формулы (литература + авторская)
# ============================================================================
dM = (M_max - sub["M"]) / M_max
met103 = pd.DataFrame({
    "eta, Гц/Вт (f/P_pow)": (sub["f"] / P_pow),
    "EDP, Дж*с (Q*T)": (sub["Q"] * sub["T"]),
    "rho, ед./Г (mAP/F)": (sub["mAP"] / sub["F"]),
    "BF ((f/Q)*(dM/M_max))": (sub["f"] / sub["Q"]) * dM,
}, index=sub.index)
show("§10.3. Новые формулы", met103.round(3))

# ============================================================================
# §10.4. Комбинированные метрики «точность на ресурс»
# ============================================================================
met104 = pd.DataFrame({
    "Q1 = mAP/F": (sub["mAP"] / sub["F"]),
    "Q2 = mAP/P": (sub["mAP"] / sub["P"]),
    "Q3 = mAP/(F*P)": (sub["mAP"] / (sub["F"] * sub["P"])),
    "Q4 = mAP*f/F": (sub["mAP"] * sub["f"] / sub["F"]),
}, index=sub.index)
show("§10.4. Комбинированные метрики Q1..Q4", met104.round(3))

# ============================================================================
# §10.5. Авторские метрики (проверяемые в Gazebo)
# ============================================================================
met105 = pd.DataFrame(index=sub.index)
met105["DF"] = np.exp(-sub["T"] / tau)
met105["AR"] = sub["mAP"] * met105["DF"]
met105["APM, ед./МБ"] = sub["mAP"] / sub["M"]
met105["FPG, Гц/Гфлоп"] = sub["f"] / sub["F"]
met105["IDD, ед./с"] = sub["mAP"] * sub["f"]
# SR — по масштабу семейства (n -> s); у CNN+LSTM парного s-варианта нет
met105["SR"] = pd.Series({
    "YOLO11n": (47.0 / 39.5) / (21.7 / 6.6),
    "YOLOv8n": (44.9 / 37.3) / (28.8 / 8.9),
}).reindex(sub.index)
show("§10.5. Авторские метрики", met105.round(3))

# ============================================================================
# §11. Итоговый расчёт по всем методам
# ============================================================================
methods = [
    ("Лаплас (§8.1)",        True,  lap),
    ("Оптимизм (§8.2)",      True,  opt),
    ("Вальд (§8.3)",         True,  wal),
    ("Сэвидж (§8.4)",        False, reg),
    ("Гурвиц (§8.5)",        True,  hurwitz(A, 0.5)),
    ("Баллы (§9.4)",         True,  total),
    ("Вариант II (§10.1)",   True,  laplace(B)),
    ("Вариант III (§10.2)",  True,  phi_vals["Phi"]),
    ("eta (§10.3.1)",        True,  met103["eta, Гц/Вт (f/P_pow)"]),
    ("EDP (§10.3.2)",        False, met103["EDP, Дж*с (Q*T)"]),
    ("rho (§10.3.3)",        True,  met103["rho, ед./Г (mAP/F)"]),
    ("BF (§10.3.4)",         True,  met103["BF ((f/Q)*(dM/M_max))"]),
    ("Q1 (§10.4.1)",         True,  met104["Q1 = mAP/F"]),
    ("Q2 (§10.4.2)",         True,  met104["Q2 = mAP/P"]),
    ("Q3 (§10.4.3)",         True,  met104["Q3 = mAP/(F*P)"]),
    ("Q4 (§10.4.4)",         True,  met104["Q4 = mAP*f/F"]),
    ("DF (§10.5.1)",         True,  met105["DF"]),
    ("AR (§10.5.2)",         True,  met105["AR"]),
    ("APM (§10.5.3)",        True,  met105["APM, ед./МБ"]),
    ("FPG (§10.5.4)",        True,  met105["FPG, Гц/Гфлоп"]),
    ("SR (§10.5.5)",         True,  met105["SR"]),
    ("IDD (§10.5.6)",        True,  met105["IDD, ед./с"]),
]
models = list(sub.index)
Psi = pd.Series(0.0, index=models)
cnt = pd.Series(0, index=models)
Borda = pd.Series(0.0, index=models)
rsum = pd.Series(0.0, index=models)
rcnt = pd.Series(0, index=models)
rows_w = []
for name, bigger, s in methods:
    s = s.reindex(models).dropna()
    lo, hi = s.min(), s.max()
    z = (s - lo) / (hi - lo) if hi > lo else pd.Series(1.0, index=s.index)
    if not bigger:
        z = 1.0 - z
    Psi[z.index] += z
    cnt[z.index] += 1
    n = len(s)
    r = s.rank(ascending=not bigger, method="average")
    Borda[s.index] += n - r + 1
    rsum[s.index] += r
    rcnt[s.index] += 1
    best = s.idxmax() if bigger else s.idxmin()
    rows_w.append((name, " | ".join(f"{v:.3f}" for v in s.reindex(models).fillna(np.nan)),
                   best))

summary = pd.DataFrame({
    "Psi": (Psi / cnt).round(3),
    "Борда": Borda.astype(int),
    "Средний ранг": (rsum / rcnt).round(3),
})
show("§11.2. Итоговое сведение (нормировка + среднее, Борда, ср. ранг)", summary)

print("\n### §11.1. Победитель по каждому способу")
for name, vals, best in rows_w:
    print(f"{name:22} | {vals} | {best}")
