# Construction Cost Calculator
### A local-first construction estimator for people who have been personally wronged by Excel, cloud dashboards, and “quick estimates” that somehow take three days.

---

## What Is This?

This is a **desktop construction cost calculator** built in **Python + PyQt5** for doing *actual engineering sanity checks* without:

- spreadsheets that slowly rot into lies
- web tools that need an account, a password reset, and an apology
- vendor software that assumes your site matches their brochure
- “just round it” optimism

It runs locally. It works offline. It does the maths you tell it to do.  
No opinions. No vibes. Just numbers.

---

## What This Does

The app is split into dedicated calculator tabs, each responsible for **one job**.  
The **Summary** tab pulls everything together and refuses to be impressed.

### Breeze Block Calculator
- Straight walls, curved walls, raceway reactors
- Real block sizes and pallet counts
- Calculates:
  - wall areas
  - block quantities
  - pallet counts
  - leftovers you will argue about later
- Default pricing included, overridable because reality exists

### Sweet Sand Calculator
- Racetrack-shaped reactor bases
- Flat fill plus corner fillets (because corners exist)
- Density-based mass calculations
- Cost per tonne to total cost
- Geometry that matches how things are actually built, not how drawings pretend

### Concrete Works
- Slabs, strip footings, walls, isolated footings
- Volume, reinforcement mass, cost breakdowns
- No hidden constants
- No “trust me bro” cells

### Land Preparation
- Bulk excavation and trenching
- Compaction by lifts and passes
- Lets you model “this will be a pain” honestly
- Produces numbers you can defend, not just survive

### Manpower
- Trade-based workforce modelling
- Normal hours, overtime, overtime factors
- Mobilisation, demobilisation, overheads
- Outputs total man-hours and cost without assuming people are robots

### Equipment & Machinery
- Per-machine breakdowns
- Hire rate, utilisation, fuel burn
- Fuel cost, mobilisation, overheads
- Produces a readable breakdown instead of a suspicious lump sum

### Summary
- Aggregates everything
- Auto-recalculates after project load
- Single source of truth
- Exports a **proper PDF report** that looks like it meant to exist

---

## PDF Export

- Choose filename and location
- Dark blue + orange theme (same as the app)
- Opens automatically after generation
- Browser tab title set to:
  Construction Report

No Adobe.
No Java.
No subscriptions.
No appeasement of software gods.

---

## Project Save / Load

Projects can be saved and reopened as plain JSON files.

- Saves all user inputs across all tabs
- Load restores the entire project state
- Auto-recalculates everything on load
- Summary updates immediately

The files are:
- human-readable
- diffable
- email-friendly
- deliberately ignored by git

As they should be.

---

## Design Philosophy

- Local-first
- No cloud dependencies
- No subscriptions
- No telemetry
- No surprises
- Deterministic maths over optimism
- UI that stays out of your way

This tool exists because real projects need answers **now**, not after logging in, syncing, or convincing a dashboard to behave.

---

## Installation

Install the requirements.

Run the app.

That’s it.

If it doesn’t work offline, it’s a bug.

---

## What This Is Not

- A tender BOQ generator
- A replacement for detailed design
- A crystal ball
- A tool that survives bad assumptions

It is an **engineering calculator**.  
It tells you what you told it. Nothing more. Nothing less.

---

## Final Note

If this saves you time, prevents one bad spreadsheet decision, or stops one late-night recalculation spiral, then it’s doing its job.

No cloud.
No nonsense.
Just numbers.
