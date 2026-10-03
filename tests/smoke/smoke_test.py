from datetime import date
from pathlib import Path
import json

import computadora.memoria.memoria as memoria
from computadora.cerebro.nlu import CerebroComputadora


def write_test_raw(d: date):
    p = memoria._raw_path_for(d)
    p.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        {"ts":"2026-04-03T00:00:00Z","role":"user","text":"hola, esto es una prueba"},
        {"ts":"2026-04-03T00:00:05Z","role":"assistant","text":"hola, dime algo"},
        {"ts":"2026-04-03T00:00:10Z","role":"user","text":"dime todo lo que sepas sobre ti (test)"}
    ]
    with p.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print("Wrote raw test file:", p)


def run():
    test_date = date(2099, 12, 31)
    write_test_raw(test_date)

    print("Compressing test date", test_date)
    memoria.compress_day(test_date)

    sp = memoria._summary_path_for(test_date)
    sample = memoria._sample_path_for(test_date)
    print("Summary exists:", sp.exists(), sp)
    if sp.exists():
        print(sp.read_text(encoding="utf-8")[:1000])
    print("Sample exists:", sample.exists(), sample)
    if sample.exists():
        print(sample.read_text(encoding="utf-8")[:1000])

    print("Instantiating CerebroComputadora")
    c = CerebroComputadora()
    q = "dime todo lo que sepas sobre ti"
    print("Asking:", q)
    r = c.pensar(q)
    print("Response:", r)


if __name__ == "__main__":
    run()
