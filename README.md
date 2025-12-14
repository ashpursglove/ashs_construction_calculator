# Construction Cost Calculator
### A local-first construction estimator for people who have stared at a spreadsheet long enough to realise it is lying.

---

## What Is This?

This is a **desktop construction cost calculator** built in **Python + PyQt5** for doing early-stage quantity and cost estimates **without**:

- spreadsheets that slowly mutate into folklore  
- cloud tools that require an account, a verification email, and forgiveness  
- vendor software that assumes your site is flat, square, and blessed  
- estimates based on “it was about this much last time”

It runs locally. It works offline.  
If your internet is down, this does not care.

---

## What This Does

The application is split into focused calculator tabs.  
Each tab does *one job*, correctly, without opinions.

The **Summary** tab aggregates everything and does not ask how you feel about the result.

### Breeze Block Calculator
- Straight walls, curved walls, raceway reactors
- Uses real block sizes and pallet counts
- Calculates:
  - wall areas
  - block quantities
  - pallet counts
  - leftover blocks you will argue about later
- Default pricing included, overridable because reality always disagrees

### Sweet Sand Calculator
- Racetrack-shaped reactor bases
- Flat fill plus corner fillets (because corners exist, despite drawings)
- Density-based mass calculation
- Cost per tonne to total cost
- Geometry that reflects how things are actually built, not how brochures imagine them

### Concrete Works
- Slabs, strip footings, walls, isolated footings
- Volume, reinforcement mass, and cost breakdowns
- No hidden coefficients
- No “multiply by 1.3 just in case” magic

### Land Preparation
- Bulk excavation
- Trenches
- Compaction by lifts and passes
- Models how annoying compaction really is
- Produces numbers you can defend in a meeting without sweating

### Manpower
- Trade-based workforce modelling
- Normal hours and overtime
- Overtime factors that acknowledge labour laws exist
- Mobilisation, demobilisation, overheads
- Outputs total man-hours and cost without assuming people are machines

### Equipment & Machinery
- Per-machine breakdowns
- Hire rate, utilisation, fuel burn
- Fuel cost, mobilisation, overheads
- Produces an actual breakdown instead of a suspicious round number

### Summary
- Aggregates everything
- Auto-recalculates after project load
- Single source of truth
- Exports a **proper PDF report** that looks deliberate

---

## PDF Export

- Choose filename and location
- Dark blue + orange theme (same as the app)
- Opens automatically after generation
- Browser tab title reads:
  Construction Report

No Adobe.  
No Java.  
No rituals.  
No “why is this 400 MB”.

---

## Project Save / Load

Projects can be saved and reopened as plain JSON files.

- Saves all user inputs across all tabs
- Load restores the entire project state
- Automatically recalculates everything
- Summary updates immediately

The files are:
- human-readable
- diffable
- email-friendly
- intentionally ignored by git

As they should be.

---

## Executable Release (Yes, Really)

There is a **standalone EXE** available in the GitHub Releases section.

- No Python install required
- No virtual environments
- No command line incantations
- Just download, double-click, and calculate things

It is portable.  
It does not phone home.  
It does not update itself mid-calculation.

If it breaks, it breaks honestly.

---

## Design Philosophy

- Local-first
- No cloud dependencies
- No subscriptions
- No telemetry
- No popups asking if you’re enjoying the experience
- Deterministic maths over “smart” estimates
- UI that stays out of your way

This tool exists because real projects need numbers **now**, not after logging in, syncing, or negotiating with a dashboard.

---

## What This Is Not

- A tender BOQ generator
- A replacement for detailed design
- A scheduling oracle
- A solution to bad assumptions

It is an **engineering calculator**.

If the inputs are wrong, the outputs will also be wrong.
But they will be wrong consistently.

---

## License

This project is released under the **MIT License**.

That means:
- Use it
- Modify it
- Ship it
- Embed it in something else
- Do not sue the author if concrete behaves like concrete

If it saves you time, great.  
If it saves you from one catastrophic spreadsheet decision, even better.

---

## Final Note

If this tool:
- replaces one fragile spreadsheet
- prevents one late-night recalculation spiral
- or stops one meeting from devolving into “back-of-the-envelope maths”

Then it has done exactly what it was built to do.

No cloud.  
No nonsense.  
Just numbers.
