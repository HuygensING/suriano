import sys
import re
from subprocess import run

from docx2python import docx2python

from tf.core.files import dirContents, initTree, expanduser
from tf.core.helpers import console, specFromRanges, rangesFromSet


ORG = "HuygensING"
REPO = "suriano"
REPODIR = expanduser(f"~/github/{ORG}/{REPO}")
REPORTDIR = f"{REPODIR}/report"
DATADIR = f"{REPODIR}/data"
DOCDIR = f"{DATADIR}/docx"
TEISIMPLEDIR = f"{DATADIR}/teiSimple"
TEIDIR = f"{DATADIR}/tei"

MONTHS = """
    gennaio|gennaro
    febbraio|febraro
    marzo
    aprile|april
    maggio
    giugno|zugno
    luglio
    agosto
    settembre
    ottobre
    novembre
    dicembre|decembre
""".strip().split()

MONTH_NUM = {}
VALID_MONTHS = []

for (i, monthSpec) in enumerate(MONTHS):
    names = monthSpec.split("|")
    for name in names:
        MONTH_NUM[name] = i + 1
        VALID_MONTHS.append(name)

validMonthPat = rf"""\b{"|".join(VALID_MONTHS)}\b"""


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
            <num>{num}</num>
        </correspAction>
    </correspDesc>
</profileDesc>
</teiHeader>
<text>
<body>
<div type="original">
    {original}
</div>
<div type="secretarial">
    {secretarial}
</div>
<div type="notes">
    {notes}
</div>
<div type="summary">
    {summary}
</div>
</body>
</text>
</TEI>
"""


headers = {}
pageInfo = {}
transcriberInfo = {}


letterSplitRe = re.compile(
    r"""
    \s*<p>\s*/\s*START\s+LETTER\s*/\s*</p>\s*
    """,
    re.X | re.S,
)

stripTailRe = re.compile(
    r"""
    \s*
    </body>
    \s*
    </text>
    \s*
    </TEI>
    .*
    """,
    re.X | re.S,
)


def transformFilza(text, filza, thisTranscriberInfo):
    texts = []

    letters = letterSplitRe.split(text)[1:]
    letters[-1] = stripTailRe.sub("", letters[-1])

    for (i, letter) in enumerate(letters):
        texts.append(transform(filza, i + 1, letter, thisTranscriberInfo))

    return texts


# <p>18 ottobre 1616, L’Aia (cc. 43r-44v, 50bis r-51v)</p>
pagesLineRe = re.compile(
    r"""
    <p>
    \s*
    /
    \s*
    (
        [0-9]+
        [^/]*
    )
    /
    \s*
    </p>
    """,
    re.X,
)

pageDigits = re.compile(
    r"""
    ^
    \s*
    ([0-9]*)
    [^0-9]*
    $
    """,
    re.X | re.S,
)

sectionStartRe = re.compile(
    r"""
    ^
    \s*
    <p>
    n\.\s*
    ([0-9]+)
    \s*
    </p>
    \s*
    $
    """,
    re.X,
)

sectionLineRe = re.compile(
    r"""
    ^
    \s*
    <p>
    (.*)
    \(cc?\.\s*
    ([^)]*)
    \)
    \s*
    (.*?)
    </p>
    \s*
    $
    """,
    re.X,
)

attachmentRe = re.compile(
    r"""
    ^
    \s*
    allegato
    \s+
    ([IVX]+)
    \s+
    al
    \s+
    n\.
    \s+
    ([0-9]+)
    \s*
    $
    """,
    re.X | re.I,
)

letterRe = re.compile(
    r"""
    ^
    \s*
    ([^,]+)
    ,
    (.*)
    $
    """,
    re.X,
)

dateRe = re.compile(
    r"""
    ^
    \s*
    ([0-9]{1,2})
    \s*
    ((?:"""
    + validMonthPat
    + r""")+)
    \s*
    ([0-9]{4})
    \s*
    $
    """,
    re.X | re.I,
)

paraNewlineRe = re.compile(
    r"""
    <p\b
    .*?
    </p>
    """,
    re.X | re.S,
)

paraPageInterruptRe = re.compile(
    r"""
    </p>
    (
        \s*
        <pb[^>]*>
        \s*
    )
    <p>
    (
        \s*
        (?:
            <[^>]*>
            \s*
        )*
        [a-zàáçèéęìíñòóùú]
    )
    """,
    re.X | re.S
)


nlRe = re.compile(r""" *\n\s*""", re.S)
whiteRe = re.compile(r"""  +""", re.S)
nlWhiteRe = re.compile(r"""(?: \n)|(?:\n )""", re.S)


def stripNewlines(match):
    text = match.group(0)
    return text.replace("\n", " ")


stripPRe = re.compile(
    r"""
    ^
    \s*
    <p>
    \s*
    (.*)
    </p>
    \s*
    $
    """,
    re.X | re.S,
)


def stripP(match):
    return match.group(1).strip()


noteRe = re.compile(
    r"""
    <note>(.*?)</note>
    """,
    re.X | re.S,
)


notes = []
noteMark = 0


def moveNote(match):
    global noteMark

    noteMark += 1
    noteText = match.group(1).strip()
    noteText = stripPRe.sub(stripP, noteText)
    footNote = (
        f"""<note xml:id="tn{noteMark}"><p><hi rend="footnote">{noteMark}</hi> """
        f"""{noteText}</p></note>"""
    )
    notes.append(footNote)
    return f"""<ptr target="#tn{noteMark}" n="{noteMark}"/>"""


warnings = []


def trimPage(match):
    spec = match.group(1).strip()
    specId = spec.replace(" ", "_")
    return f"""<pb xml:id="f{specId}" n="{spec}"/>"""


# All chars:
# [^A-Za-z0-9="/,.;:?#’…½¾(){}\[\]~|^<>àáçèÈéÉęìíñòó°ùú  ­￼*_-]
#

def transform(filza, letter, text, thisTranscriberInfo):
    global noteMark

    noteMark = 0
    notes.clear()

    thisPageInfo = pageInfo.setdefault(filza, {}).setdefault(letter, {})

    pages = set()
    pageSpecs = pagesLineRe.findall(text)
    thisPageInfo["specs"] = pageSpecs

    for pageSpec in pageSpecs:
        specs = pageSpec.split("-", 1)
        (fromSpec, toSpec) = (specs[0], specs[0]) if len(specs) == 1 else specs

        match = pageDigits.match(fromSpec)
        if match:
            fromDigits = match.group(1)
        match = pageDigits.match(toSpec)
        if match:
            toDigits = match.group(1)

        if fromDigits == "" and toDigits == "":
            continue

        if fromDigits == "":
            pages.add(int(toDigits))
        elif toDigits == "":
            pages.add(int(fromDigits))
        else:
            for p in range(int(fromDigits), int(toDigits) + 1):
                pages.add(p)

    thisPageInfo["pages"] = pages
    transcribers = set()
    for p in pages:
        ts = thisTranscriberInfo.get(p, set())
        transcribers |= ts

    text = noteRe.sub(moveNote, text)
    text = paraNewlineRe.sub(stripNewlines, text)
    text = text.replace("\u00a0", " ").replace("\u00ad", " ").replace("\ufffc", " ")
    textLines = text.split("\n")
    newTextLines = []

    curN = None
    startSection = False
    date = ""
    normalizedDate = ""
    settlement = ""
    nums = []
    biblScope = []
    summary = ""
    secretarial = ""
    transcribers = ", ".join(sorted(transcribers))

    for (i, line) in enumerate(textLines):
        if startSection:
            startSection = False
            match = sectionLineRe.match(line)
            if not match:
                warnings.append(
                    (filza, letter, i + 1, line, "Unrecognized section line")
                )
                newTextLines.append(line)
                continue

            (kindSpec, pageSpec) = match.group(1, 2)
            biblScope.append(pageSpec)
            match = attachmentRe.match(kindSpec)

            if match:
                (num, target) = match.group(1, 2)
                atts = f"""n="{curN}" corresp="{target}" source="{pageSpec}" """
                newTextLines.append(f"""<div type="appendix" {atts}>""")
            else:
                match = letterRe.match(kindSpec)
                if match:
                    (dateSpec, placeSpec) = match.group(1, 2)
                    settlement = placeSpec.strip()
                    match = dateRe.match(dateSpec)
                    if match:
                        (day, month, year) = match.group(1, 2, 3)
                        normalizedDate = f"{year}-{MONTH_NUM[month]:>02}-{int(day):>02}"
                    else:
                        warnings.append(
                            (filza, letter, i + 1, dateSpec, "letter has invalid date")
                        )
                        normalizedDate = ""
                    newTextLines.append(f"""<div type="text" n="{curN}">""")
                else:
                    warnings.append(
                        (
                            filza,
                            letter,
                            i + 1,
                            line,
                            "Section line is not letter nor attachment",
                        )
                    )
                    newTextLines.append("""<div type="text">""")

            newTextLines.append(
                line.replace("<p>", "<head>").replace("</p>", "</head>")
            )

        else:
            match = sectionStartRe.match(line)
            if match:
                if curN:
                    newTextLines.append("</div>")
                curN = match.group(1)
                nums.append(curN)
                startSection = True
            else:
                newTextLines.append(line)

    if curN:
        newTextLines.append("</div>")

    text = "\n".join(newTextLines)
    text = text.replace("|", "<lb/>\n")
    text = text.replace("\n</p>", "</p>")
    text = text.replace("<lb/></p>", "</p>")
    text = text.replace("[", "<supplied>")
    text = text.replace("]", "</supplied>")
    text = text.replace("""rendition="simple:""", '''rend="''')
    text = pagesLineRe.sub(trimPage, text)
    text = paraPageInterruptRe.sub(r"\1\2", text)
    text = nlRe.sub("\n", text)
    text = whiteRe.sub(" ", text)
    text = nlWhiteRe.sub("\n", text)

    return template.format(
        filza=filza,
        letterno=letter,
        num=", ".join(nums),
        normalizedDate=normalizedDate,
        date=date,
        settlement=settlement,
        biblScope=", ".join(b.strip() for b in biblScope),
        respName=transcribers,
        original=text,
        secretarial=secretarial,
        summary=summary,
        notes="\n".join(notes),
    )


def teiFromDocx():
    console("DOCX => TEI")
    files = sorted(
        x
        for x in dirContents(DOCDIR)[0]
        if x.endswith(".docx") and not x.startswith("~")
    )
    initTree(TEISIMPLEDIR, fresh=True, gentle=True)

    for file in files:
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


def headersFromDocx():
    console("DOCX => headers")
    files = sorted(
        x
        for x in dirContents(DOCDIR)[0]
        if x.endswith(".docx") and not x.startswith("~")
    )

    headerRe = re.compile(
        r"""
            ^
            Filza_
            ([0-9]+)
            _
            [0-9]+
            _
            ([^_]*)
            _cc?\.
            \s*
            ([^-]+)
            -
            (.+)
            $
        """,
        re.X,
    )
    pageRe = re.compile(
        r"""
            ^
            ([0-9]+)
            [^0-9]*
            $
        """,
        re.X,
    )

    for file in files:
        console(f"\t{file}")
        inFile = f"{DOCDIR}/{file}"
        with docx2python(inFile) as cn:
            for h in cn.header:
                # Filza_3_5_Cristina_cc. 147r-178v
                text = h[0][0][0]
                match = headerRe.match(text)
                if not match:
                    console(f"\t\twrong header: «{text}»")
                    continue
                (filza, transcriber, fromPage, toPage) = match.group(1, 2, 3, 4)
                matchF = pageRe.match(fromPage)
                matchT = pageRe.match(toPage)
                if not (matchF and matchT):
                    if not matchF:
                        console(f"\t\twrong from page «{fromPage}» in «{text}»")
                    if not matchT:
                        console(f"\t\twrong to page «{toPage}» in «{text}»")
                    continue
                fromPage = int(matchF.group(1))
                toPage = int(matchT.group(1))
                filza = int(filza)
                for p in range(fromPage, toPage + 1):
                    headers.setdefault(transcriber, {}).setdefault(filza, set()).add(p)
                    transcriberInfo.setdefault(filza, {}).setdefault(p, set()).add(
                        transcriber
                    )

    for (transcriber, filzas) in sorted(headers.items()):
        nFilzas = len(filzas)
        nPages = sum(len(x) for x in filzas.values())
        filzaPlural = " " if nFilzas == 1 else "s"
        pagePlural = " " if nPages == 1 else "s"
        console(
            f"{transcriber:<20}: {nPages:>3} page{pagePlural} "
            f"in {nFilzas:>2} filza{filzaPlural}"
        )


def teiFromTei():
    console("TEI simple => TEI enriched")
    files = dirContents(TEISIMPLEDIR)[0]
    initTree(TEIDIR, fresh=True, gentle=True)
    letterTranscribers = {}

    with open(f"{REPORTDIR}/pageinfo.txt", "w") as rh:
        for file in files:
            if not file.endswith(".xml"):
                continue

            console(f"\t{file}")

            with open(f"{TEISIMPLEDIR}/{file}") as f:
                text = f.read()

            filza = int(file.split("_", 2)[1])
            initTree(f"{TEIDIR}/{filza}", fresh=True, gentle=True)
            thisTranscriberInfo = transcriberInfo[filza]
            texts = transformFilza(text, filza, thisTranscriberInfo)

            startPage = 1

            for (i, text) in enumerate(texts):
                letter = i + 1
                pages = pageInfo[filza][letter]["pages"]
                transcribers = set()
                for p in pages:
                    ts = thisTranscriberInfo.get(p, set())
                    transcribers |= ts
                letterTranscribers.setdefault(filza, {})[letter] = ts
                nextPage = max(pages) + 1
                expectedPages = set(range(startPage, nextPage))

                if expectedPages != pages:
                    thisPageInfo = pageInfo[filza][letter]

                    extraPages = pages - expectedPages
                    missingPages = expectedPages - pages

                    rh.write(f"{filza} {letter}\n")
                    rh.write(f"\texpected: {startPage}-{nextPage - 1}\n")
                    pagesRep = specFromRanges(rangesFromSet(thisPageInfo["pages"]))
                    rh.write(f"\tfound:    {pagesRep}\n")

                    if len(extraPages):
                        pagesRep = specFromRanges(rangesFromSet(extraPages))
                        console(f"\t\tletter {letter}: extra pages: {pagesRep}")
                        rh.write(f"\textra:    {pagesRep}\n")
                    if len(missingPages):
                        pagesRep = specFromRanges(rangesFromSet(missingPages))
                        console(f"\t\tletter {letter}: missing pages: {pagesRep}")
                        rh.write(f"\tmissing:  {pagesRep}\n")

                    rh.write("\tspecs:\n")
                    for spec in thisPageInfo["specs"]:
                        rh.write(f"\t\t{spec}\n")

                startPage = nextPage

                with open(f"{TEIDIR}/{filza}/{letter}.xml", "w") as f:
                    f.write(text)

    with open(f"{REPORTDIR}/letterinfo.txt", "w") as lh:
        for (filza, letterInfo) in sorted(letterTranscribers.items()):
            lh.write(f"\nFilza {filza:>2}\n\n")
            for (letter, transcribers) in sorted(letterInfo.items()):
                tRep = ", ".join(sorted(transcribers))
                lh.write(f"\t{letter:>4} {tRep}\n")

    print(f"{len(warnings)} warnings")
    for (filza, letter, ln, line, heading) in warnings:
        print(f"{filza}_{letter:>03}:{ln:>5} {heading} :: {line}")


def main():
    tasks = dict(
        pandoc=False,
        headers=False,
        tei=False,
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

    initTree(REPORTDIR, fresh=False)

    for (task, do) in tasks.items():
        if not do:
            continue

        console(f"TASK {task}")

        if task == "pandoc":
            teiFromDocx()
        elif task == "headers":
            headersFromDocx()
        elif task == "tei":
            teiFromTei()


if __name__ == "__main__":
    main()
