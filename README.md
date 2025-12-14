# Ash's Construction Cost Calculator
### A construction estimator for engineers who no longer accept vibes as a costing methodology

<img width="677" height="530" alt="image" src="https://github.com/user-attachments/assets/55e4528d-ad00-44f6-aa32-f1b7d7b81068" />


---

## What Is This?

This is a **desktop construction cost calculator** for producing early-stage quantities and costs **without**:

- spreadsheets held together by merged cells and hope  
- cloud tools that require a login, a subscription, and an emotional support ticket  
- vendor software that assumes your site is flat, square, and morally pure  
- estimates that begin with “it should be roughly…”

It runs locally.  
It works offline.  
It does not care about your Wi-Fi, your VPN, or your password manager having a moment.

---

## What This Does

The application is split into focused calculator tabs.  
Each tab has one job. It does that job. It does not branch out into opinions.

The **Summary** tab aggregates everything and presents the result without sympathy.

### Breeze Block Calculator
- Straight walls, curved walls, raceway reactors
- Uses real block dimensions and pallet counts
- Calculates:
  - wall areas
  - block quantities
  - pallet counts
  - leftover blocks that will absolutely be “kept for later”
- Default pricing included, overridable because pricing is a social construct

### Sweet Sand Calculator
- Racetrack-shaped reactor bases
- Flat fill plus corner fillets (because corners exist in reality)
- Density-based mass calculation
- Cost per tonne to total cost
- Geometry that reflects how things are actually built, not how drawings suggest they might be

### Concrete Works
- Slabs, strip footings, walls, isolated footings
- Volume, reinforcement mass, cost breakdowns
- No hidden factors
- No “multiply by 1.2 because vibes”

### Land Preparation
- Bulk excavation
- Trenches
- Compaction by lifts and passes
- Explicitly models how annoying compaction really is
- Produces numbers you can say out loud in a meeting without apologising

### Manpower
- Trade-based workforce modelling
- Normal hours and overtime
- Overtime factors that acknowledge labour laws exist
- Mobilisation, demobilisation, overheads
- Outputs man-hours and cost without assuming humans are interchangeable units

### Equipment & Machinery
- Per-machine rows
- Hire rate, utilisation, fuel burn
- Fuel cost, mobilisation, overheads
- Produces an actual breakdown instead of a suspiciously round number

### Summary
- Aggregates everything
- Auto-recalculates after project load
- Single source of truth
- Exports a **proper PDF report** that looks like someone meant it

---

## PDF Export

- Choose filename and location
- Opens automatically after generation
- Makes it look like you know what you're doing


No Adobe.  
No Java.  
No 17 GB updates.  
No ancient curses.

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

## Executable Release (For People Who Do Not Want Python Opinions)

A **standalone EXE** is available in the GitHub Releases section.

- No Python installation required
- No virtual environments
- No command line
- No “it works on my machine” energy

Download it.  
Double-click it.  
It runs.

It does not update itself mid-calculation.  
It does not ask for permissions it doesn’t need.  
It does not try to sell you a premium tier.

---

## Design Philosophy

- Local-first
- No cloud dependencies
- No subscriptions
- No telemetry
- No popups asking if you’re enjoying the experience
- Deterministic maths over optimism
- UI that stays out of your way

This tool exists because real projects need numbers **now**, not after logging in, syncing, or negotiating with a dashboard that thinks everything is a KPI.

---

## What This Is Not

- A tender BOQ generator
- A replacement for detailed design
- A scheduling oracle
- A crystal ball
- A substitute for thinking

It is an **engineering calculator**.

If the inputs are bad, the outputs will also be bad.
But they will be bad in a consistent, repeatable, auditable way.

---

## License

This project is released under the **MIT License**.

Which means:
- Use it
- Modify it
- Ship it
- Embed it in something else
- Do not attempt to sue me when concrete behaves like concrete

No warranties.  
No guarantees.  
No miracles.

Just software.


