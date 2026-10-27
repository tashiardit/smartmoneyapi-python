"""Print the composite macro snapshot. No API key needed."""
from smartmoneyapi import SmartMoneyClient

m = SmartMoneyClient().macro()

fg = m["fear_greed"]
reg = m["derivatives_regime"]
print("fear & greed :", fg.get("value"), fg.get("classification"), "|", fg.get("status"))
print("derivatives  :", reg.get("label") or reg.get("status"),
      "| OI coverage:", reg.get("included_oi_share"))
print("cot status   :", m["cot"].get("status"))

# Components the API does not serve are listed, not zero-filled.
for w in m["withheld"]:
    print("withheld     :", w["field"], "-", w["reason"])
if m["stale"] or m["warming"] or m["unavailable"]:
    print("note: some components are stale, warming or unavailable")
