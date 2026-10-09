"""Does 'Length shown as min/max' beat the claimed 'Length = gene 1' only because it has
more free values? Fit both to fake data made by the CLAIM model (where gene 1 is the truth).
If the rival gains about as much on fake data as on real data, the real-data gain is noise."""
from concurrent.futures import ProcessPoolExecutor
from model import CLAIM, LitterFit
from sim_checks import fake_dataset

RIVALS = {"CLAIM": CLAIM,
          "length=min": {**CLAIM, "rules": ("mean", "min", "max", "min")},
          "length=max": {**CLAIM, "rules": ("mean", "min", "max", "max")}}


def job(seed):
    fake, _ = fake_dataset("CLAIM", seed)
    return seed, {k: round(sum(LitterFit(d, m).fit() for _, d in fake.groupby("litter", sort=False)), 1)
                  for k, m in RIVALS.items()}


if __name__ == "__main__":
    with ProcessPoolExecutor() as ex:
        for seed, r in ex.map(job, (11, 12, 13, 14, 15)):
            print(f"fake CLAIM seed {seed}: " + ", ".join(f"{k} {v}" for k, v in r.items())
                  + f"  gain of length=min over CLAIM: {r['length=min'] - r['CLAIM']:+.1f}")
