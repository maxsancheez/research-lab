#!/usr/bin/env python3
"""Unit economics of a shared, pay-per-crate solar cold room at the farm gate (India).

Answers three questions:
  1. Does a standalone cold room pay back from storage fees alone?
  2. What tariff / occupancy does it need to break even?
  3. When is it worth it for the farmer to pay that fee?

Standard library only. Edit ASSUMPTIONS and re-run:  python3 cold_room_model.py
Every number marked (est.) is an assumption, not a sourced figure. See ../README.md.
"""

ASSUMPTIONS = {
    # Asset: sourced ranges from pv magazine India (2021) and Outlook Business
    "capex_inr": 14_00_000,          # 5 MT solar cold room, INR 12-15 lakh installed
    "subsidy_share": 0.35,           # govt capital subsidy 35-50% (individuals)
    "capacity_tonnes": 5,            # Ecofrost-class room: ~5-6 MT
    "crate_kg": 20,                  # standard returnable plastic crate (ColdHubs uses 20 kg)
    "life_years": 10,                # (est.)
    "discount_rate": 0.12,           # (est.) cost of capital for a small rural operator

    # Operations
    "tariff_inr_per_crate_day": 5.0,  # (est.) ColdHubs charges 100 naira ~ INR 5; no public Indian rate found
    "avg_occupancy": 0.55,            # (est.) harvests are seasonal; rooms are rarely full year-round
    "operating_days": 300,            # (est.)
    "operator_salary_inr_month": 12_000,  # (est.) one local attendant
    "maintenance_share_of_capex": 0.03,   # (est.) per year
    "battery_replacement_inr": 1_50_000,  # (est.) thermal/electrical storage refresh in year 6

    # Optional add-on: operator also aggregates and sells produce for members
    "aggregation_commission": 0.03,   # (est.) 3% of produce value sold through the hub
    "produce_value_inr_per_kg": 20,   # (est.) blended fruit/veg farm-gate price
    "turns_per_crate_slot_year": 40,  # (est.) avg 7-day stays across 300 days, ~ 43 turns
}


def crates(a):
    return a["capacity_tonnes"] * 1000 // a["crate_kg"]


def annual_cashflows(a, with_aggregation=False):
    occupied_crate_days = crates(a) * a["avg_occupancy"] * a["operating_days"]
    revenue = occupied_crate_days * a["tariff_inr_per_crate_day"]
    if with_aggregation:
        kg_through = crates(a) * a["avg_occupancy"] * a["turns_per_crate_slot_year"] * a["crate_kg"]
        revenue += kg_through * a["produce_value_inr_per_kg"] * a["aggregation_commission"]
    opex = a["operator_salary_inr_month"] * 12 + a["capex_inr"] * a["maintenance_share_of_capex"]
    flows = []
    for year in range(1, a["life_years"] + 1):
        cf = revenue - opex
        if year == 6:
            cf -= a["battery_replacement_inr"]
        flows.append(cf)
    return revenue, opex, flows


def npv(rate, upfront, flows):
    return -upfront + sum(cf / (1 + rate) ** t for t, cf in enumerate(flows, start=1))


def payback_years(upfront, flows):
    total = 0
    for t, cf in enumerate(flows, start=1):
        total += cf
        if total >= upfront:
            return t
    return None


def breakeven_tariff(a):
    """Lowest INR/crate/day (to 0.1) where the 10-year NPV turns positive."""
    for tenths in range(1, 500):
        trial = dict(a, tariff_inr_per_crate_day=tenths / 10)
        _, _, flows = annual_cashflows(trial)
        if npv(a["discount_rate"], net_capex(a), flows) >= 0:
            return tenths / 10
    return None


def net_capex(a):
    return a["capex_inr"] * (1 - a["subsidy_share"])


def inr(x):
    return f"INR {x:,.0f}"


def main():
    a = ASSUMPTIONS
    upfront = net_capex(a)
    print(f"Room: {a['capacity_tonnes']} t = {crates(a)} crates of {a['crate_kg']} kg | "
          f"net capex after {a['subsidy_share']:.0%} subsidy: {inr(upfront)}\n")

    for label, agg in (("Storage fees only", False), ("Storage + 3% aggregation commission", True)):
        revenue, opex, flows = annual_cashflows(a, with_aggregation=agg)
        pb = payback_years(upfront, flows)
        print(f"== {label}")
        print(f"   revenue/yr {inr(revenue)}  opex/yr {inr(opex)}  operating profit/yr {inr(revenue - opex)}")
        print(f"   10-yr NPV @ {a['discount_rate']:.0%}: {inr(npv(a['discount_rate'], upfront, flows))}  "
              f"payback: {f'{pb} yrs' if pb else 'never (within 10 yrs)'}\n")

    print(f"Break-even storage tariff (fees only): INR {breakeven_tariff(a)}/crate/day\n")

    print("10-yr NPV (INR lakh), storage fees only. Rows: tariff INR/crate/day, cols: avg occupancy")
    occs = (0.35, 0.55, 0.75, 0.90)
    print("tariff  " + "".join(f"{o:>9.0%}" for o in occs))
    for tariff in (3, 5, 8, 10, 12):
        row = []
        for o in occs:
            trial = dict(a, tariff_inr_per_crate_day=tariff, avg_occupancy=o)
            _, _, flows = annual_cashflows(trial)
            row.append(npv(a["discount_rate"], upfront, flows) / 1e5)
        print(f"{tariff:>6}  " + "".join(f"{v:>9.1f}" for v in row))

    # Farmer side: storing is worth it when the price gain + avoided spoilage beats the fee.
    print("\nFarmer view: one 20 kg crate of tomatoes at INR 15/kg (INR 300)")
    crate_value = a["crate_kg"] * 15
    avoided_loss = 0.0837  # NABCONS 2022: tomato farm-level loss 8.37%
    for days in (3, 7, 14):
        fee = days * a["tariff_inr_per_crate_day"]
        needed = (fee - crate_value * avoided_loss) / crate_value
        print(f"   store {days:>2} days: fee {inr(fee)} ({fee / crate_value:.0%} of crate value); "
              f"break-even price rise {max(needed, 0):.1%} after counting avoided farm loss")


if __name__ == "__main__":
    main()
