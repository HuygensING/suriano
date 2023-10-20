from openpyxl import load_workbook

from tf.core.files import writeYaml
from tf.browser.ner.helpers import normalize, toSmallId, toTokens


TRANSFORM_DEFS = """
d=
da=
dal=
de=
del=
dela=
der=
detto=
di=
el=
en=
et=
giovanni=gio
il=
la=
le=
of=
tot=
van=
von=
y=
zu=
"""

TRANSFORM = {}

for line in TRANSFORM_DEFS.strip().split("\n"):
    (x, y) = line.split("=")
    TRANSFORM[x.strip()] = y.strip()


def doSheet(fileIn, fileOut):
    wb = load_workbook(fileIn, data_only=True)
    ws = wb.active

    (headRow, subHeadRow, *rows) = list(ws.rows)
    rows = [row for row in rows if any(c.value for c in row)]

    info = {}

    for r, row in enumerate(ws.rows):
        if r in {0, 1}:
            continue
        if not any(c.value for c in row):
            continue

        (ent, synonyms) = (normalize(row[i].value or "") for i in range(2))
        eid = toSmallId(ent, transform=TRANSFORM)

        if not ent:
            print(f"Row {r:>3}: no entity name")
            continue

        i = 0
        while eid in info:
            i += 1
            eid = f"{eid}.{i}"
            print(f"Row {r:>3}: multiple instances ({eid})")

        occs = sorted(
            (normalize(x) for x in ([] if not synonyms else synonyms.split(";"))),
            key=lambda x: -len(x),
        )
        info[eid] = dict(name=ent, occs=occs)

    writeYaml(info, asFile=fileOut)

    nEid = len(info)
    nOcc = sum(len(x["occs"]) for x in info.values())
    noOccs = sum(1 for x in info.values() if len(x["occs"]) == 0)
    print(f"{nEid} entities with {nOcc} occurrence specs")
    print(f"{noOccs} entities do not have occurrence specifiers")


def showReport(ner, report):
    total = 0

    for eid, info in ner.items():
        name = info.name
        occs = info.occs
        for occ in occs:
            matches = report.get(toTokens(occ), None)
            if matches is None:
                continue
            n = len(matches)
            total += n
            print(f"{eid:<24} {occ:<20} {n:>5} x {name}")

    print(f"Total {total}")
