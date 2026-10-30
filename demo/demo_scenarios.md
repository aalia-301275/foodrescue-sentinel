# FoodRescue Sentinel — Demo Scenarios

*All scenarios below are synthetic test cases created for demonstrating the prototype. They are not real food-safety assessments.*

## Scenario 1 — Complete Batch

**Purpose:** Test whether the agent can extract all the relevant information when the donor provides a complete description.

**Input:**

"We have prepared 200 portions of vegetable biryani on 30 October 2026 at 4:00 AM. The food was immediately placed in refrigerated storage at 4°C and has remained refrigerated since preparation. The packaging is intact, properly sealed and shows no visible damage. Please assess this batch using the available food-safety rules and identify any required human-review steps."

## Scenario 2 — Missing Temperature Record

**Purpose:** Test whether the agent identifies missing evidence instead of assuming the food was stored correctly.

**Input:**

"We have prepared 150 portions of vegetable pulao on 30 October 2026 at 5:00 AM. The food was transferred to refrigerated storage immediately after preparation. However, the refrigerator temperature was not recorded, so we cannot confirm the actual storage temperature. The food has remained in the refrigerator since preparation, and the packaging appears intact. Please assess the batch and identify what information is still needed."

## Scenario 3 — Damaged Packaging

**Purpose:** Test whether the agent identifies packaging concerns and routes the case for human review.

**Input:**

"We have prepared 100 portions of cooked vegetable rice on 30 October 2026 at 5:30 AM. The food was immediately refrigerated at 4°C and has remained refrigerated since preparation. During inspection, we noticed that some of the food containers had cracked lids and damaged seals. We cannot confirm whether the affected food was exposed to contamination. Please assess the batch, identify the concerns and recommend the appropriate next steps."