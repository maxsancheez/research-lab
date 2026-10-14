# cold_room_model.py

Unit economics of one shared, pay-per-crate solar cold room (5 t, 250 crates).

```bash
python3 cold_room_model.py
```

No dependencies (Python 3.8+). Change any value in `ASSUMPTIONS` at the top of the file and re-run. Values marked `(est.)` are assumptions; the rest come from the sources in `../README.md`.

It prints:
- yearly revenue, opex, 10-year NPV and payback, with and without an aggregation commission
- the break-even storage tariff
- an NPV grid of tariff × occupancy
- the farmer's break-even price rise for 3, 7 and 14-day holds
