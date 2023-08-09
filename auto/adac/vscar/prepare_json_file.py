import os
import re

import numpy as np
import pandas as pd
from loguru import logger
from tqdm import tqdm

from auto.adac.best_car.find_best_car import (
    NUMBER_REGEXP,
    _convert_to_number,
    _get_fixed_column_name,
)

NUMERIC_TYPES = {"int", "float"}
NUMERIC_COLUMNS = {
    "Länge",
    "Anhängelast ungebremst",
    "KFZ-Steuer ohne Befreiung/Jahr (kann durch WLTP abweichen)",
    "CO2-Wert kombiniert (WLTP)",
    "Kofferraumvolumen fensterhoch mit umgeklappter Rücksitzbank",
    "Beschleunigung 0-100km/h",
    "Höchstgeschwindigkeit",
    "Nennleistung in kW",
    "Kofferraumvolumen normal",
    "Leistung maximal bei U/min. (Verbrennungsmotor)",
    "Breite (inkl. Außenspiegel)",
    "Rampenwinkel",
    "Batteriegewicht (Elektro- und PlugIn-Hybrid)",
    "Drehmoment (Systemleistung)",
    "Türanzahl",
    "Leergewicht (EU)",
    "Wendekreis",
    "Autom. Abstandsregelung",
    "Zuladung",
    "Drehmoment maximal bei U/min. (Verbrennungsmotor)",
    "Leistung maximal in PS (Systemleistung)",
    "Anzahl Zylinder (Verbrennungsmotor)",
    "Batteriekapazität (Netto) in kWh",
    "Leistung maximal in kW (Systemleistung)",
    "Alufelgen",
    "Wertverlust",
    "Reichweite NEFZ (elektrisch)",
    "CO2-Wert (NEFZ)",
    "KFZ-Steuer pro Jahr ohne Steuerbefreiung",
    "Batteriekapazität (Brutto) in kWh",
    "Böschungswinkel vorne",
    "Grundpreis",
    "Reichweite WLTP City (elektrisch)",
    "Lederausstattung",
    "Sitzanzahl maximal",
    "Kofferraumvolumen dachhoch mit umgeklappter Rücksitzbank",
    "Klassenübliche Ausstattung nach ADAC-Vorgabe",
    "Gesamtzuggewicht",
    "Einparkassistent",
    "Füllmenge AdBlue-Behälter",
    "Breite",
    "Zul. Gesamtgewicht",
    "Höhe",
    "Tankgröße",
    "Fixkosten",
    "Bodenfreiheit maximal",
    "Navigation",
    "Metallic-Lackierung",
    "id",
    "Anhängelast gebremst 12%",
    "Stützlast",
    "Tankgröße (optional)",
    "Vollkaskobetrag 100% 500 € SB",
    "Anhängerkupplung",
    "Anzahl Ventile (Verbrennungsmotor)",
    "Dachlast",
    "Böschungswinkel hinten",
    "HSN Schlüsselnummer",
    "Fahrzeugpreis",
    "Fahrgeräusch",
    "Hubraum (Verbrennungsmotor)",
    "Einparkhilfe",
    "Reichweite WLTP (elektrisch)",
    "Betriebskosten",
    "Sitzanzahl",
    "Radstand",
    "Werkstattkosten",
    "Anzahl Gänge",
    "Verbrauch Gesamt (NEFZ)",
    "Verbrauch kombiniert (WLTP)",
}
NON_NUMERIC_COLUMNS = {
    "Seitenairbag hinten - Bezeichnung",
    "AC-Ladeanschluss am Fahrzeug",
    "Start-/Stopp-Automatik (Verbrennungsmotor)",
    "Einparkhilfe - Bezeichnung",
    "Kurvenlicht",
    "3-Punkt-Gurt hinten Mitte",
    "Fahrzeugklasse",
    "3-Punkt-Gurt hinten Mitte - Bezeichnung",
    "Airbag Beifahrer",
    "WLAN Hotspot",
    "Federung hinten",
    "Seitenairbag vorne - Bezeichnung",
    "Lichtsensor",
    "Wattiefe",
    "Teilkaskobeitrag 150 € SB",
    "Zentralverriegelung",
    "Kindersitz integriert",
    "Navigation - Bezeichnung",
    "Tankeinbauort",
    "Reifendruckkontrolle",
    "Freisprecheinrichtung",
    "Bremsassistent - Bezeichnung",
    "PreCrash-System",
    "Modellstart",
    "Schaltpunktanzeige",
    "Typ",
    "Verbrauch kombiniert (WLTP) - 2. Antrieb",
    "Seitenairbag vorne",
    "Mittenairbag hinten",
    "Füllmenge AdBlue-Behälter (optional)",
    "Abbiegeassistent",
    "Kopfairbag vorne",
    "Fensterheber elektr. vorne",
    "Kopfairbag vorne - Bezeichnung",
    "Speed-Limiter",
    "Verbrauch Kurzstrecke (WLTP)",
    "Garantie (Fahrzeug)",
    "Kraftstoffart (2.Antrieb)",
    "Fernlichtassistent",
    "Ladezeiten",
    "Airbag Deaktivierung - Bezeichnung",
    "Notruffunktion",
    "Höchstgeschwindigkeit elektrisch (Hybrid)",
    "Ladeanschlussposition (zusätzlich)",
    "Isofix - Bezeichnung",
    "Baureihe",
    "Leistung / Drehmoment (Elektromotor 3)",
    "Getriebeart",
    "image",
    "Fahrdynamikregelung - Bezeichnung",
    "Kosten",
    "Verkehrsschild-Erkennung",
    "Mittenairbag vorne",
    "Ladezustandskontrolle",
    "Leistung / Drehmoment (Elektromotor 1)",
    "Verbrauch Gesamt (2.Antrieb) (NEFZ)",
    "Einbauposition / Motorbauart (Elektromotor 2)",
    "Kreuzungsassistent",
    "Smartphone-Integration (Android Auto/Apple CarPlay)",
    "processed date",
    "Kraftstoffart",
    "Verbrauch Außerorts (NEFZ)",
    "PreCrash-System - Bezeichnung",
    "Kurvenbremskontrolle",
    "Ladeanschlussposition",
    "Motorcode",
    "Nachtsicht-Assistent",
    "Motorart",
    "Typklassen (KH/VK/TK)",
    "Intelligenter Geschwindigkeitsassistent",
    "Verbrauch Innerorts (NEFZ)",
    "Fahrdynamikregelung",
    "Querverkehrassistent hinten",
    "AC Ladekabel Ladestation",
    "AC Ladekabel Haushalt",
    "Bremse hinten",
    "Speichertechnik (z.B. Lithiumionen, Feststoff etc.)",
    "checksum",
    "Verbrauch Autobahn (WLTP)",
    "AC-/DC-Laden optional",
    "Antriebsschlupfregelung",
    "DC-Schnell-Ladeanschluss am Fahrzeug",
    "CO2-Effizienzklasse",
    "Leistung / Drehmoment (Elektromotor 2)",
    "Reifengröße",
    "Regensensor",
    "Verbrauch Stadtrand (WLTP)",
    "Müdigkeitserkennung",
    "Einbauposition / Motorbauart (Elektromotor 1)",
    "Reifengröße hinten (abweichend)",
    "Variable Lichtverteilung",
    "Anhängerkupplung Typ",
    "Aktivlenkung",
    "Einbauposition / Motorbauart (Verbrennungsmotor)",
    "Seitenairbag hinten",
    "Spurwechselassistent",
    "Runflat- Bezeichnung",
    "Xenon-Scheinwerfer",
    "Abgasreinigung (Verbrennungsmotor)",
    "Fensterheber elektr. hinten",
    "Fußgängererkennung",
    "Leistung / Drehmoment (Verbrennungsmotor)",
    "Spurhalteassistent",
    "Antriebsschlupfregelung - Bezeichnung",
    "Bremsassistent",
    "Airbag Sonstige - Bezeichnung",
    "Runflat",
    "Nebelscheinwerfer",
    "Karosserie",
    "Durchrostung",
    "Marke",
    "Kopfstützen hinten",
    "Bremse vorne",
    "Fahrdynamikregelung - Anhänger",
    "Haftpflichtbeitrag 100%",
    "Trailer-Assist",
    "Isofix",
    "Ausstiegswarner",
    "Zusätzliche Garantien",
    "Emergency Assistent",
    "Wärmepumpe",
    "Aktive Kopfstützen",
    "Antriebsart",
    "Airbag Fahrer",
    "Radio",
    "Airbag Sonstige",
    "Abbiegelicht",
    "Sonstiges",
    "Reifendruckkontrolle - Bezeichnung",
    "Anzahl der Schiebetüren serienmäßig/auf Wunsch",
    "Kopfairbag hinten",
    "url",
    "Baureihenstart",
    "Gemischaufbereitung (Verbrennungsmotor)",
    "Radio - Bezeichnung",
    "TSN Schlüsselnummer",
    "Verbrauch Landstraße (WLTP)",
    "Federung vorne",
    "ABS",
    "Ladeleistung (kW)",
    "name",
    "Servolenkung",
    "AC-Ladefunktion",
    "LED-Scheinwerfer",
    "Smartphone-Induktive Ladeeinrichtung",
    "Aufladung (Verbrennungsmotor)",
    "Bremslicht dynamisch",
    "Herstellerinterne Baureihenbezeichnung",
    "Fußgängerschutz-System",
    "Laserscheinwerfer",
    "Bremslicht dynamisch - Bezeichnung",
    "Kopfstützen hinten Mitte",
    "Tankgröße (2.Antrieb)",
    "Rücksitzbank umklappbar",
    "Digitaler Radioempfang (DAB)",
    "Stauassistent",
    "Head-up-Display (HUD)",
    "Modell",
    "Lackgarantie",
    "Schadstoffklasse",
    "City-Notbremsassistent",
    "Ausweichassistent",
    "Steigung maximal",
    "TSN Schlüsselnummer 2",
    "Einbauposition / Motorbauart (Elektromotor 3)",
    "Notbremsassistent",
    "Berganfahrassistent",
    "Kollisionswarnung",
    "Airbag Deaktivierung",
    "Kopfairbag hinten - Bezeichnung",
    "Klimaanlage",
}


def _get_column_data(df):
    data = {}
    for column in df.columns:
        data[column] = {
            "type": "str",
            "additional_values": [],
            "range": {},
        }

        if column in NUMERIC_COLUMNS:
            unique_values = set(df[column].unique())
            unique_numeric_values = [
                v
                for v in list(unique_values)
                if len(NUMBER_REGEXP.findall(str(v))) in {1, 2}
            ]
            unique_non_numeric_values = unique_values.difference(unique_numeric_values)
            data[column]["additional_values"] = unique_non_numeric_values

            values = pd.Series(
                [
                    _convert_to_number(NUMBER_REGEXP.findall(str(v))[0])
                    for v in unique_numeric_values
                ]
            )
            data[column]["range"]["min"] = values.min()
            data[column]["range"]["max"] = values.max()

            dtype = values.dtypes
            if np.issubdtype(dtype, np.floating):
                data[column]["type"] = "float"
            elif np.issubdtype(dtype, np.integer):
                data[column]["type"] = "int"

    return data


def _get_numeric_columns(df):
    # function used in tests to check that all proper column are in NUMERIC_COLUMNS
    numeric_columns = set(df.select_dtypes(include=[np.number]).columns)
    column = "Bodenfreiheit maximal"
    for column in df.columns:
        unique_values = df[column].unique()
        if np.issubdtype(df[column].dtype, np.number):
            numeric_columns.add(column)
            continue
        if column in NON_NUMERIC_COLUMNS:
            logger.debug(f"SKIP: Column {column} - non numeric")
            continue

        unique_numeric_values = [
            v
            for v in list(unique_values)
            if len(NUMBER_REGEXP.findall(str(v))) in {1, 2}
        ]
        ratio = len(unique_numeric_values) / len(unique_values)
        if ratio > 0.9:  # 90% of values are numeric
            common_suffixes = list(
                set([NUMBER_REGEXP.sub("", v) for v in unique_numeric_values])
            )
            max_suffixes = 3
            if len(common_suffixes) > 0 and len(common_suffixes) <= max_suffixes:
                numeric_columns.add(column)
            else:
                fsuffixes = ", ".join(common_suffixes[:max_suffixes])
                if len(common_suffixes) > max_suffixes:
                    fsuffixes += "..."
                logger.debug(
                    f"SKIP: Column {column}, nr suffixes: {len(fsuffixes)}: {fsuffixes}"
                )
        else:
            logger.debug(
                f"SKIP: Column {column}, ratio {ratio}, unique_numeric_values: {len(unique_numeric_values)}, unique_values: {len(unique_values)}"
            )

    _non_numeric_columns = set(df.columns).difference(numeric_columns)
    return numeric_columns


def __main():
    cur_dir = os.path.dirname(__file__)
    df = pd.read_csv(os.path.join(cur_dir, "../adac.csv"))

    # fix numeric columns
    for column in NUMERIC_COLUMNS:
        df[_get_fixed_column_name(column)] = df[column].apply(_convert_to_number)

    # adding fuel, power, price
    df["fuel"] = df["Kraftstoffart"]
    df["transmission"] = df["Getriebeart"]
    df["power"] = df["Leistung maximal in kW (Systemleistung)"]
    df["price"] = df["Grundpreis"].str.replace(" Euro", "").astype(int)

    # replaceing column names
    old_cols = df.columns.to_list()
    # save columns which will be fields - "left part"
    last_db_field = "processed date"
    last_db_field_index = old_cols.index(last_db_field)
    df.columns = [
        {"id": "adac_id", "processed date": "processed_date"}.get(c, c)
        for c in old_cols
    ]

    old_cols = df.columns.to_list()
    new_columns = old_cols[: last_db_field_index + 1] + [
        col for col in old_cols[last_db_field_index + 1 :]
    ]

    df.columns = new_columns
    main_attributes = set(
        new_columns[: last_db_field_index + 1]
        + [
            "fuel",
            "price",
            "power",
            "transmission",
            "image",
        ]
    )
    additional_attributes = {
        c for c in df.columns.to_list() if c not in main_attributes
    }

    column_data = _get_column_data(df)

    new_rows = []
    for _, row in tqdm(list(df.iterrows())):
        data = {k: v for k, v in row.items() if k in main_attributes}
        data["attributes"] = []
        for k, v in row.items():
            if k in additional_attributes:
                attr = {"name": k, "value": v, "column_data": column_data[k]}
                data["attributes"].append(attr)

        new_rows.append(data)

    df = pd.DataFrame(new_rows)
    df = df.drop_duplicates(subset=["adac_id"])
    df.to_json(os.path.join(cur_dir, "car.json"), orient="records")


if __name__ == "__main__":
    __main()
