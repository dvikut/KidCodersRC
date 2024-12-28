
from kisauto_parancsok import elore, hatra, jobbra, balra, hatra_balra, hatra_jobbra, varj

# Fentebb látszik az összes utasítás, paraméterben másodpercet adhatunk meg ha nem jó az 1
# Alább pedig a játszótér

elore()
balra()
for _ in range(2):
    hatra()
    elore()
varj(1.5)
hatra(2)

