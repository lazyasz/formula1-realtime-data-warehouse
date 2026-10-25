# Class Label Definitions (Target Formulation)

## 1. Selected Classification Targets

The project evaluates four supervised classification targets and one secondary regression target:

### Primary Classification Target:
* **`target_is_win` ($Y \in \{0, 1\}$)**:
  * Mathematical definition:
    $$Y_i = \begin{cases} 1 & \text{if } \text{finish\_position}_i = 1 \\ 0 & \text{if } \text{finish\_position}_i > 1 \text{ or DNF} \end{cases}$$
  * Domain Significance: Predicts the single overall winner of the Grand Prix.
  * Prevalence: **4.67%** (577 wins out of 12,358 race starts). Exactly 1 winner per race.

### Secondary Multi-Target Classification Hierarchy:
* **`target_is_podium` ($Y \in \{0, 1\}$)**:
  * Definition: $Y_i = 1$ if $\text{finish\_position}_i \le 3$, else 0.
  * Prevalence: **14.01%** (1,731 podium finishes out of 12,358 starts). Exactly 3 per race.
* **`target_is_points` ($Y \in \{0, 1\}$)**:
  * Definition: $Y_i = 1$ if $\text{finish\_position}_i \le 10$, else 0.
  * Prevalence: **46.69%** (5,770 point-scoring entries).
* **`target_is_dnf` ($Y \in \{0, 1\}$)**:
  * Definition: $Y_i = 1$ if driver failed to complete the race due to mechanical failure, hydraulics, engine blowout, gearbox failure, or racing collision.
  * Prevalence: **28.05%** (3,467 DNF entries).

### Secondary Task: Position Regression:
* **`target_finish_position` ($y \in [1, 20]$)**:
  * Numerical final classified finish position, clipped to 20.
  * Kept strictly separate from the binary winner classification task.

## 2. Zero-Leakage Information Isolation Policy

To guarantee academic and empirical validity:
* Post-race finishing positions, race points scored in that event, total race time, fastest lap times in the Grand Prix, and official classified status are **used strictly as target labels during training**.
* They are **never used as feature inputs** for predicting that same race.
* Pre-race features rely strictly on historical rolling forms ($t-1, t-2, \dots$) accumulated before the race started.
