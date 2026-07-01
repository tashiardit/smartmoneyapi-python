from smartmoneyapi import SmartMoneyClient
c = SmartMoneyClient()
res = c.confirm("BTC", "long")
if res["action"].startswith("CONFIRM"):
    print(f"{res['action']} {res['confidence']} — size x{res['size_mult']}")
else:
    print(f"{res['action']} — weak/no context:", res["reasons"])
# Not financial advice. Crypto trading involves risk.
