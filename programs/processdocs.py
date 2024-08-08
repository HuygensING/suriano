"""Convert DOCX to TEI

USAGE

Program

    from processdocs import TeiFromDocx

    TFD = TeiFromDocx(silent)
    TFD.task(task, task, task, ...)

Where task is:

*   `pandoc`: convert docx files to tei simple files
*   `headers`: read page header info from docx files
*   `tei`: convert tei simple files to proper tei files
*   `all`: perform the three previous steps in that order

"""

import re
import collections
from subprocess import run

from docx2python import docx2python
from openpyxl import load_workbook

from tf.core.files import (
    dirContents,
    initTree,
    extNm,
    mTime,
    fileExists,
    writeJson,
)
from tf.core.helpers import console
from processhelpers import (
    HEADER_RE,
    PAGES,
    THUMBPAGESDIR,
    SUMMARY_FILE,
    DOCXDIR,
    TEIXDIR,
    TRANSCRIBER_TSV,
    HEADERS_TXT,
    PAGEINFO_TXT,
    SCANTRANS_TSV,
    TEIDIR,
    REPORT_THUMBERRORS,
    REPORT_THUMBPAGES,
    REPORT_WARNINGS,
    REPORT_PAGEWARNINGS,
    PAGESEQ_JSON,
    LETTERINFO_TXT,
    PageInfo,
    Page,
    distilPages,
)


SENDER = "sender"
RECIPIENT = "recipient"
RECIPIENTLOC = "recipientLoc"
SUMMARY = "summary"
EDITORNOTES = "editorNotes"
SHELFMARK = "shelfmark"

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

TEMPLATE = """\
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
                <idno type="shelf">{shelfmark}</idno>
            </msIdentifier>
        </msDesc>
        <bibl>
            <note>{editorNotes}</note>
            <biblScope unit="page">{biblScope}</biblScope>
        </bibl>
    </sourceDesc>
</fileDesc>
<profileDesc>
    <correspDesc>
        <note>{summary}</note>
        <correspAction type="sent">
            <name ref="bio.xml#cs">{sender}</name>
            <settlement>{settlement}</settlement>
            <date when="{normalizedDate}">{date}</date>
            <num>{textNums}</num>
        </correspAction>
        <correspAction type="received">
            <name>{recipient}</name>
            <settlement>{recipientLoc}</settlement>
        </correspAction>
    </correspDesc>
</profileDesc>
</teiHeader>
<text>
<body>
{material}
<div type="notes">
    {notes}
</div>
</body>
</text>
</TEI>
"""


MONTH_NUM = {}
VALID_MONTHS = []

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

for i, monthSpec in enumerate(MONTHS):
    names = monthSpec.split("|")
    for name in names:
        MONTH_NUM[name] = i + 1
        VALID_MONTHS.append(name)

VALID_MONTH_PAT = rf"""\b{"|".join(VALID_MONTHS)}\b"""


LETTER_SPLIT_RE = re.compile(
    r"""
    \s*<p>\s*/\s*START\s+LETTER\s*/\s*</p>\s*
    """,
    re.X | re.S,
)

SECRETARIAL_START_RE = re.compile(
    r"""
    <p>\s*<hi\b[^>]*>\s*Regesto\s+antico\s*</hi>\s*</p>\s*
    """,
    re.X | re.S,
)

STRIPTAIL_RE = re.compile(
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

EM_DASH = "—"

# <p>18 ottobre 1616, L’Aia (cc. 43r-44v, 50bis r-51v)</p>
PAGES_LINE_RE = re.compile(
    r"""
    ^
    (.*?)
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
    (.*)
    $
    """,
    re.X,
)

NOPAGESPEC_RE = re.compile(
    r"""
    ^
    \s*
    (?:
        decodifica
      | traduzione
    )
    """,
    re.X | re.S,
)

SECTION_START_RE = re.compile(
    r"""
    ^
    \s*
    <p>
    n\.\s*
    ([0-9]+[a-z]*)
    \s*
    </p>
    \s*
    $
    """,
    re.X,
)

SECTION_LINE_RE = re.compile(
    r"""
    ^
    \s*
    <p>
    (.*)
    \(cc?\.\s*
    ([^);]*)
    [\);]
    \s*
    .*?
    </p>
    \s*
    $
    """,
    re.X,
)

ATTACHMENT_RE = re.compile(
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
    \s*
    ([0-9]+[a-z]*)
    \s*
    $
    """,
    re.X | re.I,
)

LETTER_RE = re.compile(
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

DATE_RE = re.compile(
    r"""
    ^
    \s*
    ([0-9]{1,2})
    \s*
    ((?:"""
    + VALID_MONTH_PAT
    + r""")+)
    \s*
    ([0-9]{4})
    \s*
    $
    """,
    re.X | re.I,
)

PARA_NEWLINE_RE = re.compile(
    r"""
    <p\b
    .*?
    </p>
    """,
    re.X | re.S,
)

PARA_PAGE_INTERRUPT_RE = re.compile(
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
    re.X | re.S,
)


NL_RE = re.compile(r""" *\n\s*""", re.S)
WHITE_RE = re.compile(r"""  +""", re.S)
NL_WHITE_RE = re.compile(r"""(?: \n)|(?:\n )""", re.S)


def stripNewlines(match):
    text = match.group(0)
    return text.replace("\n", " ")


STRIP_P_RE = re.compile(
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


APOS_RE = re.compile(r"""['‘]""")


def normalizeChars(text):
    return APOS_RE.sub("’", text)


def stripP(match):
    return match.group(1).strip()


FILZA_RE = re.compile(r"^([0-9]+)(.*)$")
TEXT_NUM_RE = re.compile(r"^([0-9]+)(.*)$")


def normFilza(filza):
    match = FILZA_RE.match(filza)
    (digits, rest) = match.group(1, 2)
    return f"{digits:>02}{rest}"


def normText(textNum):
    match = TEXT_NUM_RE.match(textNum)
    (digits, rest) = match.group(1, 2)
    return f"{digits:>03}{rest}"


NOTE_RE = re.compile(
    r"""
    <note>(.*?)</note>
    """,
    re.X | re.S,
)


NOTES = []
NOTEMARK = 0


def moveNote(match):
    global NOTEMARK

    NOTEMARK += 1
    noteText = match.group(1).strip()
    noteText = STRIP_P_RE.sub(stripP, noteText)
    footNote = (
        f"""<note xml:id="tn{NOTEMARK}"><p><hi rend="footnote">{NOTEMARK}</hi> """
        f"""{noteText}</p></note>"""
    )
    NOTES.append(footNote)
    return f"""<ptr target="#tn{NOTEMARK}" n="{NOTEMARK}"/>"""


# All chars:
# [^A-Za-z0-9="/,.;:?#’…½¾(){}\[\]~|^<>àáçèÈéÉęìíñòó°ùú  ­￼*_-]
#


class TeiFromDocx(PageInfo):
    def __init__(self, silent=False):
        PageInfo.__init__(self, silent=silent)

        self.warnings = []
        self.scanWarnings = []
        self.pageWarnings = []
        self.pageWarningCount = 0
        self.filzaPageNums = {}
        self.rhw = None
        self.filzaPages = {}

    def warn(self, filza, letter, textNum, ln, line, heading, summarize=False):
        rhw = self.rhw
        warnings = self.warnings

        warnings.append((filza, letter, textNum, ln, line, heading, summarize))

        if rhw:
            msg = f"{filza}:{letter} n.{textNum} ln {ln:>5} {heading} :: {line}"
            rhw.write(f"{msg}\n")

    def pageWarn(self, add, msg, filza=None, letter=None, textNum=None):
        rhp = self.rhp
        pageWarnings = self.pageWarnings

        if add:
            self.pageWarningCount += 1

        prefix = f"filza {filza}" if filza is not None else ""
        prefix = f"{prefix}:{letter}" if letter is not None else ""
        prefix = f"{prefix} n{textNum}" if textNum is not None else ""
        sep = ": " if prefix else ""
        msg = f"{prefix}{sep}{msg}"
        pageWarnings.append(msg)

        if rhp:
            rhp.write(f"{msg}\n")

    def showWarnings(self):
        silent = self.silent
        warnings = self.warnings

        nWarnings = len(warnings)
        limit = 100

        summarized = collections.Counter()
        ln = 0

        for filza, letter, textNum, ln, line, heading, summarize in warnings:
            if summarize:
                summarized[heading] += 1
            else:
                if ln >= limit:
                    continue

                msg = f"{filza}:{letter} n.{textNum} ln {ln:>5} " f"{heading} :: {line}"
                self.console(msg, error=True)
                ln += 1

        nSummarized = len(summarized)

        if nSummarized:
            self.console("", error=True)

        for heading, n in sorted(summarized.items(), key=lambda x: (-x[1], x[0])):
            self.console(f"{n:>5} {'x':<6} {heading}. See extrainfo.txt", error=True)

        if silent:
            if nWarnings:
                console(f"\tThere were {nWarnings} warnings.", error=True)
        else:
            console("", error=True)
            console(f"{nWarnings} warnings", error=nWarnings > 0)

        warnings.clear()

    def showPageWarnings(self):
        silent = self.silent
        pageWarnings = self.pageWarnings
        n = self.pageWarningCount
        limit = 100

        for msg in pageWarnings[0:limit]:
            self.console(f"\t{msg}", error=True)

        if silent:
            if n:
                console(f"\tThere were {n} page warnings.", error=True)
        else:
            self.console("", error=True)
            console(f"{n} page warnings", error=n > 0)

        pageWarnings.clear()
        self.pageWarningCount = 0

    def readMetadata(self):
        if self.error:
            return

        console("Collecting excel metadata ...")

        try:
            wb = load_workbook(SUMMARY_FILE, data_only=True)
            ws = wb.active
        except Exception as e:
            console(f"\t{str(e)}", error=True)
            self.error = True
            return

        (headRow, *rows) = list(ws.rows)

        fields = {head.value: i for (i, head) in enumerate(headRow)}
        yearI = fields["year"]
        monthI = fields["month"]
        dayI = fields["day"]
        senderI = fields[SENDER]
        recipientI = fields[RECIPIENT]
        recipientLocI = fields[RECIPIENTLOC]
        summaryI = fields[SUMMARY]
        editorNotesI = fields[EDITORNOTES]
        shelfmarkI = fields[SHELFMARK]

        rows = [row for row in rows if any(c.value for c in row)]

        information = {}
        self.extraLetterData = information

        def fi(row, index):
            return row[index].value or 0

        def fs(row, index):
            return normalizeChars(row[index].value or "")

        for row in rows:
            year = fi(row, yearI)
            month = f"{fi(row, monthI):>02}"
            day = f"{fi(row, dayI):>02}"
            sender = fs(row, senderI)
            recipient = fs(row, recipientI)
            recipientLoc = fs(row, recipientLocI)
            summary = fs(row, summaryI)
            editorNotes = fs(row, editorNotesI)
            shelfmark = fs(row, shelfmarkI)

            date = f"{year}-{month}-{day}"

            information.setdefault(date, []).append(
                dict(
                    sender=sender,
                    recipient=recipient,
                    recipientLoc=recipientLoc,
                    summary=summary,
                    editorNotes=editorNotes,
                    shelfmark=shelfmark,
                )
            )

        self.console(f"\tfound metadata for {len(information)} letters")

    def trimPage(self, filza, letter, textNum, spec, pages):
        rotateInfo = self.rotateInfo
        spec = spec.strip()

        elements = []

        for page in pages:
            if not page.isTrue():
                elements.append(f"""\n<p n="{page}">{EM_DASH * 3}</p>\n""")
                continue

            facs = f"{filza}_{page}"
            rot = rotateInfo.get(filza, {}).get(page, 0)
            elements.append(f"""<pb n="{page}" facs="{facs}" rend="{rot}"/>""")

        logicalPages = "".join(elements)
        return f"""{logicalPages}"""

    def transformFilza(self, file, filza):
        if self.error:
            return

        with open(f"{TEIXDIR}/{file}") as f:
            text = f.read()

        letterTexts = []
        self.pageSeq[filza] = []
        self.filzaPages[filza] = collections.defaultdict(list)
        self.filzaPageNums[filza] = {}

        letters = LETTER_SPLIT_RE.split(text)[1:]
        letters[-1] = STRIPTAIL_RE.sub("", letters[-1])

        for i, letterText in enumerate(letters):
            letterTexts.append(self.transform(filza, f"{i + 1:>03}", letterText))

        return letterTexts

    def transform(self, filza, letter, text):
        if self.error:
            return

        pageInfo = self.pageInfo
        extraLetterData = self.extraLetterData
        transcriberInfo = self.transcriberInfo
        thisTranscriberInfo = transcriberInfo[filza]
        filzaPages = self.filzaPages[filza]
        filzaPageNums = self.filzaPageNums[filza]
        pageSeq = self.pageSeq[filza]

        global NOTEMARK

        NOTEMARK = 0
        NOTES.clear()

        text = NOTE_RE.sub(moveNote, text)
        text = PARA_NEWLINE_RE.sub(stripNewlines, text)
        text = text.replace("\u00a0", " ").replace("\u00ad", " ").replace("\ufffc", " ")
        textLines = text.split("\n")
        newTextLines = []
        secrTextLines = []

        textNum = None
        startSection = False
        date = ""
        normalizedDate = ""
        settlement = ""
        textNums = []
        biblScope = []

        pageMarks = []
        pagesDeclared = set()

        letterPages = set()
        textPages = set()
        thisPageInfo = pageInfo.setdefault(filza, {}).setdefault(letter, {})
        thisPageInfo["pages"] = letterPages
        textInfo = {}
        thisPageInfo["texts"] = textInfo

        destLines = newTextLines

        def processPageMark(pageMark):
            filzaPages[pageMark].append((letter, textNum, ln))

            pagesMarked = set()

            for pageSpec in pageMark.split(","):
                (warnings, thesePages) = distilPages(
                    pageSpec.strip(), False, knownPages=knownPages - knownPagesSeen
                )
                for page in thesePages:
                    if page in knownPages:
                        knownPagesSeen.add(page)

                pagesMarked |= thesePages

            for page in pagesMarked:
                if page in filzaPageNums:
                    prevLetter = filzaPageNums[page]
                    msg = (
                        f"in letter {letter}"
                        if prevLetter == letter
                        else f"in letters {letter} and {prevLetter}"
                    )
                    self.pageWarn(
                        True,
                        f"{page} occurs multiple times, {msg}",
                        filza=filza,
                        letter=letter,
                        textNum=textNum,
                    )

                filzaPageNums[page] = letter

                if page.isTrue():
                    letterPages.add(page)
                    textPages.add(page)

            return pagesMarked

        for i, line in enumerate(textLines):
            ln = i + 1

            match = SECTION_START_RE.match(line)

            if match:
                if textNum:
                    textInfo[textNum] = (
                        set(pagesDeclared),
                        tuple(pageMarks),
                        set(textPages),
                    )
                    pageMarks.clear()
                    pagesDeclared.clear()
                    textPages.clear()
                    newTextLines.append("</div>")

                    if len(secrTextLines):
                        newTextLines.append("""<div type="secretarial">""")
                        newTextLines.extend(secrTextLines)
                        secrTextLines.clear()
                        destLines = newTextLines
                        newTextLines.append("</div>")

                    newTextLines.append("</div>")

                textNum = normText(match.group(1))
                textNums.append(textNum)
                startSection = True
                continue

            if startSection:
                startSection = False
                match = SECTION_LINE_RE.match(line)

                if not match:
                    self.warn(
                        filza, letter, textNum, ln, line, "Unrecognized section line"
                    )
                    newTextLines.append(line)
                    continue

                (kindSpec, pageSpecs) = match.group(1, 2)

                knownPages = set()
                knownPagesSeen = set()

                for pageSpec in pageSpecs.split(","):
                    if NOPAGESPEC_RE.match(pageSpec):
                        continue

                    (warnings, thesePages) = distilPages(pageSpec.strip(), True)
                    pagesDeclared |= thesePages

                    for page in thesePages:
                        knownPages.add(page)

                    if warnings:
                        self.pageWarn(
                            True,
                            f"illegal page decl: {warnings}",
                            filza=filza,
                            letter=letter,
                            textNum=textNum,
                        )

                biblScope.append(pageSpecs)
                match = ATTACHMENT_RE.match(kindSpec)

                if match:
                    (romanNum, target) = match.group(1, 2)
                    atts = (
                        f"""facs="{romanNum}" n="{textNum}" """
                        f"""corresp="{target}" source="{pageSpecs}" """
                    )
                    newTextLines.append(f"""<div type="appendix" {atts}>""")
                else:
                    match = LETTER_RE.match(kindSpec)
                    if match:
                        (dateSpec, placeSpec) = match.group(1, 2)
                        date = dateSpec
                        settlement = placeSpec.strip()
                        match = DATE_RE.match(dateSpec)
                        if match:
                            (day, month, year) = match.group(1, 2, 3)
                            normalizedDate = (
                                f"{year}-{MONTH_NUM[month]:>02}-{int(day):>02}"
                            )
                        else:
                            warning = "letter has invalid date"
                            self.warn(filza, letter, textNum, ln, dateSpec, warning)
                            normalizedDate = ""
                        newTextLines.append(f"""<div type="text" n="{textNum}">""")
                    else:
                        warning = "Section line is not letter nor attachment"
                        self.warn(filza, letter, textNum, ln, line, warning)
                        newTextLines.append("""<div type="text">""")

                newTextLines.append("""<div type="original">""")

                newTextLines.append(
                    line.replace("<p>", "<!--<head>").replace("</p>", "</head>-->")
                )
                continue

            match = PAGES_LINE_RE.search(line)

            if match:
                pre, pageMark, post = match.group(1, 2, 3)
                pageMarks.append(pageMark)
                pages = processPageMark(pageMark)
                pageSeq.extend(
                    [f"{filza}_{page}" for page in pages if page.isTrue()]
                )
                newText = (
                    pre + self.trimPage(filza, letter, textNum, pageMark, pages) + post
                )
                destLines.append(newText)
                continue

            match = SECRETARIAL_START_RE.match(line)

            if match:
                destLines = secrTextLines
                continue

            destLines.append(line)

        if textNum:
            textInfo[textNum] = (set(pagesDeclared), tuple(pageMarks), set(textPages))
            newTextLines.append("</div>")

        if len(secrTextLines):
            newTextLines.append("""<div type="secretarial">""")
            newTextLines.extend(secrTextLines)
            secrTextLines.clear()
            destLines = newTextLines
            newTextLines.append("</div>")

        newTextLines.append("</div>")

        transcribers = set()

        for page in letterPages:
            ts = thisTranscriberInfo.get(page.simplify(), set())
            transcribers |= ts

        transcribers = ", ".join(sorted(transcribers))

        text = "\n".join(newTextLines)
        text = text.replace("|", "<lb/>\n")
        text = text.replace("\n</p>", "</p>")
        text = text.replace("<lb/></p>", "</p>")
        # text = text.replace("[", "<supplied>")
        # text = text.replace("]", "</supplied>")
        text = text.replace("""rendition="simple:""", '''rend="''')
        text = PARA_PAGE_INTERRUPT_RE.sub(r"\1\2", text)
        text = NL_RE.sub("\n", text)
        text = WHITE_RE.sub(" ", text)
        text = NL_WHITE_RE.sub("\n", text)

        extraDatas = extraLetterData.get(normalizedDate, [])

        extraData = None

        for sheet in extraDatas:
            if sheet.get("seen", False):
                continue

            sheet["seen"] = True
            extraData = sheet
            break

        if extraData is None:
            warning = "no extra letter data in xls"
            self.warn(filza, letter, "", "", normalizedDate, warning, summarize=True)

            sender = ""
            recipient = ""
            recipientLoc = ""
            summary = ""
            editorNotes = ""
            shelfmark = ""
        else:
            sender = extraData[SENDER]
            recipient = extraData[RECIPIENT]
            recipientLoc = extraData[RECIPIENTLOC]
            summary = extraData[SUMMARY]
            editorNotes = extraData[EDITORNOTES]
            shelfmark = extraData[SHELFMARK]

        return TEMPLATE.format(
            filza=filza,
            letterno=letter,
            textNums=", ".join(textNums),
            normalizedDate=normalizedDate,
            date=date,
            settlement=settlement,
            biblScope=", ".join(b.strip() for b in biblScope),
            respName=transcribers,
            material=text,
            sender=sender,
            recipient=recipient,
            recipientLoc=recipientLoc,
            summary=summary,
            editorNotes=editorNotes,
            shelfmark=shelfmark,
            notes="\n".join(NOTES),
        )

    def teiFromDocx(self):
        if self.error:
            return

        console("DOCX => simple TEI per filza ...")

        files = sorted(
            x
            for x in dirContents(DOCXDIR)[0]
            if x.endswith(".docx") and not x.startswith("~")
        )
        initTree(TEIXDIR, fresh=False)

        for file in files:
            self.console(f"\t{file} ... ", newline=False)

            inFile = f"{DOCXDIR}/{file}"
            outFile = f"{TEIXDIR}/{file}".removesuffix(".docx") + ".xml"

            if fileExists(outFile) and mTime(outFile) > mTime(inFile):
                self.console("uptodate")
                continue

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
            with open(outFile) as fh:
                text = normalizeChars(fh.read())

            with open(outFile, mode="w") as fh:
                fh.write(text)

            self.console("converted")

    def headersFromDocx(self):
        if self.error:
            return

        silent = self.silent

        console("DOCX => headers ...")

        files = sorted(
            x
            for x in dirContents(DOCXDIR)[0]
            if x.endswith(".docx") and not x.startswith("~")
        )

        headers = {}
        headerTexts = collections.Counter()
        transcriberInfo = {}
        self.transcriberInfo = transcriberInfo

        wrongHeaders = 0

        for file in files:
            self.console(f"\t{file}")

            inFile = f"{DOCXDIR}/{file}"

            x = f"{file}: " if silent else "\t\t"

            try:
                with docx2python(inFile) as cn:
                    header = cn.header

            except Exception as e:
                self.console(str(e), error=True)
                self.error = True
                wrongHeaders += 1
                continue

            for h in header:
                # Filza_3_5_Cristina_cc. 147r-178v
                text = h[0][0][0]
                if not text:
                    continue
                headerTexts[text] += 1
                match = HEADER_RE.match(text)

                if not match:
                    self.console(f"{x}wrong header: «{text}»", error=True)
                    wrongHeaders += 1
                    continue

                (filza, transcriber, pageSpec) = match.group(1, 2, 3)
                filza = normFilza(filza)
                transcriber = transcriber.replace("_", ", ")
                (warnings, pages) = distilPages(pageSpec, True, simpleOnly=True)

                if warnings:
                    self.console(
                        f"{x}wrong page spec in header «{pageSpec}»: {warnings}",
                        error=True,
                    )
                    continue

                for page in pages:
                    headers.setdefault(transcriber, {}).setdefault(filza, set()).add(
                        page
                    )
                    transcriberInfo.setdefault(filza, {}).setdefault(page, set()).add(
                        transcriber
                    )

        msg = (
            "OK: All headers are OK"
            if wrongHeaders == 0
            else f"XX: There were {wrongHeaders} issues with the headers"
        )
        if silent:
            if wrongHeaders:
                console(f"\t{msg}", error=True)
        else:
            console(f"\t{msg}", error=wrongHeaders > 0)

        with open(HEADERS_TXT, "w") as rh:
            for text, n in sorted(headerTexts.items()):
                rh.write(f"{n:>3} x «{text}»\n")

        with open(TRANSCRIBER_TSV, "w") as rh:
            for filza in sorted(transcriberInfo):
                pages = transcriberInfo[filza]

                for page in sorted(pages):
                    transcribers = pages[page]
                    transcribersRep = ",".join(transcribers)

                    rh.write(f"{filza}\t{page}\t{transcribersRep}\n")

        if not silent:
            for transcriber, filzas in sorted(headers.items()):
                nFilzas = len(filzas)
                nPages = sum(len(x) for x in filzas.values())
                filzaPlural = " " if nFilzas == 1 else "s"
                pagePlural = " " if nPages == 1 else "s"
                console(
                    f"{transcriber:<20}: {nPages:>3} page{pagePlural} "
                    f"in {nFilzas:>2} filza{filzaPlural}"
                )

    def readTranscribers(self):
        if self.error:
            return

        transcriberInfo = {}
        self.transcriberInfo = transcriberInfo

        console("Collecting transcribers ...")

        with open(TRANSCRIBER_TSV) as rh:
            for line in rh:
                (filza, pageStr, transcribers) = line.rstrip("\n").split("\t")
                page = Page.parse(pageStr, kind="log")

                transcriberInfo.setdefault(filza, {})[page] = set(
                    transcribers.split("\t")
                )

    def readThumbs(self):
        if self.error:
            return

        silent = self.silent

        pages = []
        self.scanPages = pages
        errors = {}
        self.scanErrors = errors

        console("Collecting page scans ...")

        DS_STORE = ".DS_Store"

        thumbs = dirContents(THUMBPAGESDIR)[0]

        if not len(thumbs):
            errors["empty"] = True

        for thumb in sorted(thumbs):
            if thumb == DS_STORE:
                continue

            ext = extNm(thumb)

            if ext != "jpg":
                errors.setdefault("other_extension", []).append(thumb)
                continue

            name = thumb.removesuffix(".jpg")
            parts = name.split("_", 1)

            if len(parts) != 2:
                errors.setdefault("no_filza", []).append(thumb)
                continue

            (filza, pageStr) = parts
            page = Page.parse(pageStr, kind="log")

            if page is None or not page.isTrue():
                errors.setdefault("wrong page", []).append(thumb)
                continue
            else:
                pages.append((filza, page))

        stats = dict(error=0, good=0)

        with open(REPORT_THUMBERRORS, "w") as rh:
            for error in sorted(errors):
                rh.write(f"{error}:\n")

                for item in errors[error]:
                    rh.write(f"  {item}\n")
                    stats["error"] += 1

                rh.write("\n")

        with open(REPORT_THUMBPAGES, "w") as rh:
            rh.write("page\n")

            for filza, page in pages:
                rh.write(f"{filza}_{page}\n")
                stats["good"] += 1

        for stat, n in sorted(stats.items()):
            if silent:
                if stat == "error" and n > 0:
                    console(f"\t{n:>3} x {stat}", error=True)
                    self.error = True
            else:
                console(f"{n:>3} x {stat}", error=stat == "error" and n > 0)

    def reportScans(self):
        if self.error:
            return

        silent = self.silent
        pageInfo = self.pageInfo
        scanPages = self.scanPages
        exclusions = self.exclusions

        pageTrans = {}
        pageScans = {}

        for filza, filzaData in pageInfo.items():
            for letterData in filzaData.values():
                pages = letterData[PAGES]

                for page in pages:
                    pageTrans.setdefault(filza, set()).add(page)

        for filza, page in scanPages:
            pageScans.setdefault(filza, set()).add(page)

        noScans = 0
        noTrans = 0
        both = 0

        allFilzas = set(pageTrans) | set(pageScans)

        with open(SCANTRANS_TSV, "w") as rh:
            rh.write("filza\tpage\tstatus\ttrans\tscan\n")

            for filza in sorted(allFilzas):
                filzaExclusions = exclusions[filza]

                startAt = None

                if filzaExclusions is not None:
                    if filzaExclusions.exclude:
                        continue

                    startAt = filzaExclusions.startAt

                trans = pageTrans.get(filza, set())
                scans = pageScans.get(filza, set())

                allPages = trans | scans

                for page in sorted(allPages):
                    if page in scans and startAt is not None and page.num < startAt:
                        continue

                    t = page in trans
                    s = page in scans

                    tRep = "yes" if t else "no"
                    sRep = "yes" if s else "no"
                    rep = "XX"

                    if t and s:
                        rep = "OK"
                        both += 1
                    elif t:
                        noScans += 1
                    elif s:
                        noTrans += 1

                    rh.write(f"{filza}\t{page}\t{rep}\t{tRep}\t{sRep}\n")

                    if rep == "XX":
                        status = (
                            "scan but no transcription"
                            if s
                            else "transcription but no scan"
                        )
                        self.console(f"{filza}: {page}: {status}", error=True)

        self.console(f"Pages with    transcription and    scan: {both:>5}")

        msgScans = f"Pages with    transcription and no scan: {noScans:>5}"
        msgTrans = f"Pages with no transcription and    scan: {noTrans:>5}"

        if silent:
            if noScans:
                console(f"\t{msgScans}", error=True)
            if noTrans:
                console(f"\t{msgTrans}", error=True)
        else:
            console(msgScans, error=noScans > 0)
            console(msgTrans, error=noTrans > 0)
            console(f"See {SCANTRANS_TSV}", error=True)

    def teiFromTei(self):
        if self.error:
            return

        transcriberInfo = self.transcriberInfo
        missingInfo = self.missingInfo

        self.warnings = []
        self.pageWarnings = []
        self.pageWarningCount = 0

        self.rhw = open(REPORT_WARNINGS, mode="w")
        self.rhp = open(REPORT_PAGEWARNINGS, mode="w")

        console("simple TEI per filza => enriched TEI per letter ...")

        files = dirContents(TEIXDIR)[0]
        initTree(TEIDIR, fresh=True, gentle=True)

        letterTranscribers = {}
        pageInfo = {}
        self.pageInfo = pageInfo

        pageSeq = {}
        self.pageSeq = pageSeq

        for file in sorted(files):
            if not file.endswith(".xml"):
                continue

            self.console(f"\t{file}")

            filza = file.removesuffix(".xml")
            initTree(f"{TEIDIR}/{filza}", fresh=True, gentle=True)
            thisTranscriberInfo = transcriberInfo[filza]
            letterTexts = self.transformFilza(file, filza)

            # startPage = 1

            for i, letterText in enumerate(letterTexts):
                letter = f"{i + 1:>03}"
                pages = pageInfo[filza][letter][PAGES]
                transcribers = set()

                for page in pages:
                    ts = thisTranscriberInfo.get(page, set())
                    transcribers |= ts

                letterTranscribers.setdefault(filza, {})[letter] = transcribers

                # startPage = nextPage

                with open(f"{TEIDIR}/{filza}/{letter}.xml", "w") as f:
                    f.write(letterText)

        writeJson(pageSeq, asFile=PAGESEQ_JSON)

        with open(PAGEINFO_TXT, "w") as rh:
            for filza in sorted(pageInfo):
                rh.write(f"Filza {filza}\n")
                filzaPages = self.filzaPages[filza]
                filzaPageInfo = pageInfo[filza]
                filzaMissingInfo = missingInfo[filza] or set()

                for letter in sorted(filzaPageInfo):
                    rh.write(f"\tLetter {letter}\n")
                    letterPageInfo = filzaPageInfo[letter]["texts"]

                    for textNum in sorted(letterPageInfo):
                        rh.write(f"\t\tText {textNum}\n")
                        (pagesDeclared, pageMarks, pages) = letterPageInfo[textNum]

                        for pageMark in pageMarks:
                            occurrences = filzaPages[pageMark]
                            n = len(occurrences)

                            if n > 1:
                                rh.write(
                                    f"\t\t\t{pageMark} occurs {len(occurrences)} x\n"
                                )
                                self.pageWarn(
                                    True,
                                    f"{pageMark} occurs {n} x",
                                    filza=filza,
                                    letter=letter,
                                    textNum=textNum,
                                )

                                too = "     "

                                for lt, nm, ln in occurrences:
                                    rh.write(
                                        "\t\t\t\t" f"letter {lt} n.{textNum} ln {ln:>4}"
                                    )
                                    self.pageWarn(
                                        False,
                                        f"\t{too}in {lt} n.{nm:5} ln {ln:>4}",
                                    )
                                    too = "also "

                        extra = pages - pagesDeclared

                        if len(extra):
                            for page in extra:
                                if page.simplify() in pagesDeclared:
                                    pagesDeclared.add(page)

                        if pagesDeclared - filzaMissingInfo == pages:
                            rh.write(f"\t\t\tOK: {Page.setRep(pages)}\n")
                        else:
                            msg1 = f"Declared:     {Page.setRep(pagesDeclared)}"
                            msg2 = f"Encountered:  {Page.setRep(pages)}"
                            missing = pagesDeclared - pages
                            extra = pages - pagesDeclared

                            if len(missing):
                                ps = Page.setRep(missing)
                                msg3 = f"\t\t\tMissing:     {ps}\n"
                                self.pageWarn(
                                    True,
                                    f"missing {ps}",
                                    filza=filza,
                                    letter=letter,
                                    textNum=textNum,
                                )
                            else:
                                msg3 = ""

                            if len(extra):
                                ps = Page.setRep(extra)
                                msg4 = f"\t\t\tExtra:       {ps}\n"
                                self.pageWarn(
                                    True,
                                    f"extra   {ps}",
                                    filza=filza,
                                    letter=letter,
                                    textNum=textNum,
                                )
                            else:
                                msg4 = ""

                            if len(extra) or len(missing):
                                self.pageWarn(False, f"\t{msg1}")
                                self.pageWarn(False, f"\t{msg2}")
                            rh.write(f"\t\t\t{msg1}\n\t\t\t{msg2}\n{msg3}{msg4}")

        with open(LETTERINFO_TXT, "w") as lh:
            for filza, letterInfo in sorted(letterTranscribers.items()):
                lh.write(f"\nFilza {filza}\n\n")
                for letter, transcribers in sorted(letterInfo.items()):
                    tRep = ", ".join(sorted(transcribers))
                    lh.write(f"\t{letter} {tRep}\n")

        self.showPageWarnings()
        self.showWarnings()

        self.rhw.close()
        self.rhw = None
        self.rhp.close()
        self.rhp = None

    def task(self, *args):
        if self.error:
            return

        tasks = dict(
            pandoc=False,
            headers=False,
            tei=False,
        )

        good = True

        for arg in args:
            if arg in tasks:
                tasks[arg] = True
            elif arg == "all":
                for arg in tasks:
                    tasks[arg] = True
            else:
                console(f"Unrecognized task: {arg}", error=True)
                good = False

        if not good:
            console(f"Valid tasks are {' '.join(tasks)}", error=True)
            return

        if all(not do for do in tasks.values()):
            console("Nothing to do", error=True)
            return

        for task, do in tasks.items():
            if not do:
                continue

            if task == "pandoc":
                self.teiFromDocx()
            elif task == "headers":
                self.headersFromDocx()
            elif task == "tei":
                self.readTranscribers()
                self.readThumbs()
                self.readMetadata()
                self.teiFromTei()
                self.reportScans()
