"""Synthetic fixture with Bondora's column names, used ONLY to test the harness.

Nothing produced from this fixture is evidence about Bondora, the bureau or
Mainkai. Known properties are planted so tests can check the code finds them:
  * rating grades map to PDs with a deliberate under-prediction in grade F
  * the 18-24 age band defaults at 1.5x its predicted PD
  * model version 2 is introduced in 2022 and shifts the rating mix
"""
from __future__ import annotations

import numpy as np
import pandas as pd

GRADE_PD = {"AA": 0.02, "A": 0.04, "B": 0.07, "C": 0.11, "D": 0.16, "E": 0.23, "F": 0.32, "HR": 0.45}


def make_fixture(n: int = 40_000, seed: int = 11) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    years = rng.integers(2019, 2025, n)
    loan_date = pd.to_datetime([f"{y}-{m:02d}-15" for y, m in zip(years, rng.integers(1, 13, n))])
    mv = np.where(years >= 2022, 2, 1)
    p_grade = np.where(mv[:, None] == 2,
                       [0.10, 0.18, 0.20, 0.18, 0.14, 0.10, 0.06, 0.04],
                       [0.06, 0.12, 0.18, 0.20, 0.18, 0.12, 0.08, 0.06])
    grades = np.array(list(GRADE_PD))
    rating = np.array([rng.choice(grades, p=row) for row in p_grade])
    pd_model = np.array([GRADE_PD[g] for g in rating]) * rng.uniform(0.85, 1.15, n)
    age = rng.integers(18, 70, n)
    true_p = pd_model.copy()
    true_p[rating == "F"] *= 1.35
    true_p[age <= 24] *= 1.5
    bad = rng.uniform(size=n) < np.clip(true_p, 0, 0.95)
    default_date = pd.Series(pd.NaT, index=range(n))
    lag = pd.to_timedelta(rng.integers(30, 360, n), unit="D")
    default_date[bad] = (loan_date[bad] + lag[bad])
    return pd.DataFrame({
        "LoanId": [f"SYN{i:06d}" for i in range(n)],
        "LoanDate": loan_date, "DefaultDate": default_date.values,
        "ProbabilityOfDefault": np.round(pd_model, 4), "Rating": rating,
        "ModelVersion": mv, "Age": age,
        "Country": rng.choice(["EE", "FI", "ES"], n), "Gender": rng.choice([0, 1, 2], n),
    })
