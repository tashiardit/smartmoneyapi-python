from smartmoneyapi import SmartMoneyClient
c = SmartMoneyClient()
res = c.confirm("BTC", "long")
if res["action"] == "SKIP":
    print("Skip — weak context:", res["reasons"])
else:
    print(f"{res['action']} {res['confidence']} — size x{res['size_multiplier']}")
# Not financial advice. Crypto trading involves risk.
