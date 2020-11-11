import os
from collections import defaultdict
from pprint import pprint

import pandas as pd

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    files = sorted(
        [
            os.path.join(data_dir, p)
            for p in os.listdir(data_dir)
            if os.path.isfile(os.path.join(data_dir, p))
        ]
    )
    # files = files[-2:]
    pprint(files)
    data = defaultdict(int)
    dframes = []
    for f in files:
        print(f)
        df = pd.read_excel(io=f, sheet_name="Uued sõidukid", skiprows=3)
        df = df[df.Kategooria.apply(lambda x: "M1" in str(x))]
        # df = df[(df.Kategooria == 'M1') & (df['Mootori tüüp'] == 'Diisel')]
        # df = df[(df.Kategooria == 'M1') & (df['Mootori tüüp'] == 'Bensiin hübriid')]
        # df = df[(df.Kategooria == 'M1') & ('Diisel hübriid' == df['Mootori tüüp'])]
        # df = df[(df.Mark == 'Lamborghini')]

        dframes.append(df)
        for _, d in df.iterrows():
            name = " ".join([d["Mark"], d["Mudel"], str(round(d["Mootori võimsus"]))])
            data[name] += d["Arv"]

    pd.concat(dframes).to_csv("mnt.csv")
    data = sorted(data.items(), key=lambda x: x[1])
    pprint(data)

    # TODO; find how much car each model gets sold by fuel type
