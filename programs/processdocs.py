import sys
from subprocess import run

from tf.core.files import dirContents, initTree, expanduser
from tf.core.helpers import console


ORG = "HuygensING"
REPO = "suriano"
REPODIR = expanduser(f"~/github/{ORG}/{REPO}")
DATADIR = f"{REPODIR}/data"
DOCDIR = f"{DATADIR}/docx"
TEISIMPLEDIR = f"{DATADIR}/teiSimple"
TEIINTERDIR = f"{DATADIR}/teiInter"
TEIDIR = f"{DATADIR}/tei"


# parameters:
#
# filza
# letterno
# normalizedDate
# date
# settlement
# biblScope
# respName
# doc2stringNotesDiv
# doc2stringSecretarial
# doc2stringOriginal
# letter.querySelector('p:nth-of-type(4)').textContent

template = """\
<?xml version="1.0" encoding="utf-8"?>
<?xml-model href="https://xmlschema.huygens.knaw.nl/suriano.rng" type="application/xml"  schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model href="https://xmlschema.huygens.knaw.nl/suriano.rng" type="application/xml"  schematypens="http://purl.oclc.org/dsdl/schematron"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
<teiHeader>
<fileDesc>
    <titleStmt>
        <title>Letter {filza}.{letterno} date {normalizedDate}</title>
        <author>Christofforo Suriano</author>
        <editor xml:id="nl">Nina Lamal</editor>
        <respStmt>
            <resp>transcription</resp>
            <name>{respName}</name>
        </respStmt>
    </titleStmt>
    <publicationStmt>
        <p/>
    </publicationStmt>
    <sourceDesc>
        <msDesc>
            <msIdentifier>
                <settlement>Venice</settlement>
                <institution>Archivio di Stato di Venezia</institution>
                <collection>Senato, Dispacci, Signori Stati</collection>
                <idno type="filza">{filza}</idno>
                <idno type="letterno">{letterno}</idno>
            </msIdentifier>
        </msDesc>
        <bibl>
            <biblScope unit="page">{biblScope}</biblScope>
        </bibl>
    </sourceDesc>
</fileDesc>
<profileDesc>
    <correspDesc>
        <correspAction type="sent">
            <name ref="bio.xml#cs">Christofforo Suriano</name>
            <settlement>{settlement}</settlement>
            <date when="{normalizedDate}">{date}</date>
            <num>1</num>
        </correspAction>
    </correspDesc>
</profileDesc>
</teiHeader>
<text>
<body>
    <div type="original">
        <div type="text">
            {doc2stringOriginal}
        </div>
        <div type="secretarial">
            {doc2stringSecretarial}
        </div>
    </div>
    <div type="notes">
        <div type="summary">
            <p>
                {p4text}
            </p>
        </div>
        {doc2stringNotesDiv}
    </div>
</body>
</text>
</TEI>
"""


def transform(text):
    return text


def teiFromDocx():
    console("DOCX => TEI")
    files = dirContents(DOCDIR)[0]
    initTree(TEISIMPLEDIR, fresh=True, gentle=True)

    for file in files:
        if not file.endswith(".docx"):
            continue

        console(f"\t{file}")
        inFile = f"{DOCDIR}/{file}"
        outFile = f"{TEISIMPLEDIR}/{file}".removesuffix(".docx") + ".xml"
        run(
            [
                "pandoc",
                inFile,
                "-f",
                "docx",
                "-t",
                "tei",
                "-s",
                "-o",
                outFile,
            ]
        )


def teiFromTei():
    console("TEI simple => TEI")
    files = dirContents(TEISIMPLEDIR)[0]
    initTree(TEIINTERDIR, fresh=True, gentle=True)

    for file in files:
        if not file.endswith(".xml"):
            continue

        console(f"\t{file}")

        with open(f"{TEISIMPLEDIR}/{file}") as f:
            text = f.read()

        text = transform(text)

        with open(f"{TEIINTERDIR}/{file}", "w") as f:
            f.write(text)


def sanitizeXml():
    console("Sanitize XML")
    files = dirContents(TEIINTERDIR)[0]
    initTree(TEIDIR, fresh=True, gentle=True)

    for file in files:
        if not file.endswith(".xml"):
            continue

        console(f"\t{file}")

        inFile = f"{TEIINTERDIR}/{file}"
        outFile = f"{TEIDIR}/{file}"
        run(
            [
                "xmllint",
                "-o",
                outFile,
                "--format",
                inFile,
            ]
        )


def main():
    tasks = dict(
        pandoc=False,
        tei=False,
        sanitize=False,
    )

    args = sys.argv[1:]

    good = True

    for arg in args:
        if arg in tasks:
            tasks[arg] = True
        elif arg == "all":
            for arg in tasks:
                tasks[arg] = True
        else:
            console(f"Unrecognized task: {arg}")
            good = False

    if not good:
        console(f"Valid tasks are {' '.join(tasks)}")
        return

    if all(not do for do in tasks.values()):
        console("Nothing to do")
        return

    for (task, do) in tasks.items():
        if not do:
            continue

        console(f"TASK {task}")

        if task == "pandoc":
            teiFromDocx()
        elif task == "tei":
            teiFromTei()
        elif task == "sanitize":
            sanitizeXml()


if __name__ == "__main__":
    main()
