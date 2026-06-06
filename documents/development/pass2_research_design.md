# Pass 2 Research Design: Adversity Response Elasticity

## 1. Project Overview & Conceptual Reframe
**Goal:** Transition from game-level descriptive statistics (Pass 1) to a within-game behavioral event study (Pass 2). 

Instead of asking "Is this player a choker?", we are asking: **"Conditional on within-game adversity, does a player preserve, increase, or reduce offensive ownership?"** 

We are measuring *revealed competitive style* and *response to negative feedback*, not unobservable mental states. We observe this by measuring who keeps taking possessions, attacking, initiating, and accepting late-clock responsibility when things go badly.

## 2. The Taxonomy of Adversity Response
Pass 2 will classify bad stretches into three observable archetypes:

### A. Forcing Collapse (e.g., Kobe archetype)
*   **Signature:** Own shot volume stable or up, efficiency tanks, shot difficulty rises, keeps authorship.
*   **Psychology:** Counterpunching / imposing will.

### B. Contractive Collapse (e.g., Harden archetype)
*   **Signature:** Own shot volume down, drives down, FT-generation down, creation down, touches down. Late-clock responsibility ceded.
*   **Psychology:** Disappearance / role abandonment.

### C. Redistributive Adjustment (e.g., CP3 archetype)
*   **Signature:** Own shots down, but assists/potential assists stable or up. Touch role preserved. Team offense still flows through the player.
*   **Psychology:** Adaptive deference / role-shifting.

*Crucial Identification Trap:* We must distinguish **adaptive deference** (Redistributive) from **contractive disappearance** (Contractive). If a player's usage drops but teammate shot quality/potential assists stay high, it's adaptation. If usage drops and creation/attacks also drop, it's contraction.

## 3. Study Design: The Event Study
The core of Pass 2 is an event study. The unit of analysis is **the possession window after an adversity event occurs.**

### Step 1: Define Adversity Events
Needs to be observable and repeatable using Play-By-Play (PBP) data.
*   *MVP Event:* Player starts the game 1-for-5 or worse, OR has a first-half TS% below a specific threshold.
*   *Granular Events:* 2 consecutive scoring attempts ending empty; turnover followed by a miss; missed at-rim attempt without FTs.

### Step 2: Define the Response Window
*   *MVP Window:* The next 8 on-court team possessions (excluding garbage time).
*   *Alternative:* Next 6 minutes of game time, or the remainder of the stint before benching.

### Step 3: Measure Deltas Relative to Baseline
We do not compare raw numbers across players. We compare a player's behavior *after adversity* to *that same player's baseline behavior* in matched game contexts (score margin, quarter, lineup context, opponent strength).

## 4. Developer Next Steps & Data Pipeline

To implement this, the new developer needs to build a pipeline to extract and calculate four buckets of variables during the **Response Window**:

### Bucket 1: Possession Ownership (The "Shrink vs. Force" Proxy)
*   **Metrics:** Share of team possessions ended by the player (FGA, drawn fouls, TOVs), usage rate over the next N possessions, touch time / time of possession, late-clock (final 5 seconds) possession ownership.

### Bucket 2: Attack Persistence
*   **Metrics:** Drives per touch, rim attempts per touch, FT-generating actions per touch, pull-up 3 attempt rate. *(Requires tracking data integration where possible).*

### Bucket 3: Redistribution vs. Disappearance
*   **Metrics:** Potential assists, passes leading to paint touches, teammate usage increase while on the floor, team expected points generated.

### Bucket 4: Coach Trust / Role Retention (Confound Check)
*   **Metrics:** Minutes lost after adversity, probability of benching after a negative sequence, 4th-quarter minutes in close games. *(Does the player shrink, or does the staff shrink him?)*

## 5. Technical Implementation Roadmap
1.  **Sample Selection:** Limit to high-usage playoff stars in the modern tracking era (Harden, Durant, Curry, Westbrook, Lillard, Luka, Booker, Tatum, Trae). *Note: Kobe lacks rich prime PBP/tracking data, so he should be used as a qualitative/motivating archetype rather than a primary empirical subject.*
2.  **Data Ingestion:** Upgrade the pipeline to ingest NBA Play-By-Play and Tracking data (Second Spectrum / NBA API tracking endpoints) to get possession-level granularity.
3.  **Event Detection Script:** Write a module to parse PBP data and flag "Adversity Events" and define the N-possession "Response Windows".
4.  **Delta Calculation:** Calculate baseline expected values for the 4 metric buckets, and compute the residual (Elasticity) during the Response Windows.
5.  **Clustering:** Run a clustering algorithm on the elasticity metrics to group players into the Forcer, Contracter, and Redistributor archetypes.

## 6. Tone & Vocabulary Guide for Code/Outputs
When writing code comments, feature names, or outputs, replace moral language with behavioral language.
*   **Avoid:** shrinks, quits, killer, scared, passive, choke.
*   **Use:** contracts, preserves role, assumes authorship, redistributes, relinquishes possessions, attack persistence, adversity response elasticity.
