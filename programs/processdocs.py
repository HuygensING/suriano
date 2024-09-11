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
    writeYaml,
)
from tf.core.helpers import console, htmlEsc
from processhelpers import (
    HEADER_RE,
    PAGES,
    THUMBPAGESDIR,
    SUMMARY_FILE,
    DOCXDIR,
    TEIXDIR,
    PAGETRANSCRIBER_TSV,
    TRANS_TXT,
    HEADERS_TXT,
    PAGEINFO_TXT,
    METAMARKS_TXT,
    DECODIFIED_TXT,
    DISPLACED_TXT,
    FOOTNOTESRM_TXT,
    FOOTNOTESUT_TXT,
    FOOTNOTESEG_TXT,
    SCANTRANS_TSV,
    TEIDIR,
    REPORT_THUMBERRORS,
    REPORT_THUMBPAGES,
    REPORT_WARNINGS,
    REPORT_PAGEWARNINGS,
    PAGESEQ_JSON,
    LETTERTRANSCRIBER_TXT,
    LETTERMETA_YML,
    LETTERDATE_YML,
    PageInfo,
    Page,
    distilPages,
    ucFirst,
    lcFirst,
)


SENDER = "sender"
SENDERLOC = "senderLoc"
RECIPIENT = "recipient"
RECIPIENTLOC = "recipientLoc"
SUMMARY = "summary"
EDITORNOTES = "editorNotes"
RESOURCES = "resources"
SHELFMARK = "shelfmark"
DECODED = "decoded"
DISPLACED = "displaced"

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
            <note>
                {editorNotes}
            </note>
            <biblScope unit="page">{biblScope}</biblScope>
        </bibl>
    </sourceDesc>
</fileDesc>
<profileDesc>
    <correspDesc>
        <note>{summary}</note>
        <correspAction type="sent">
            <name ref="bio.xml#cs">{sender}</name>
            <settlement>{senderLoc}</settlement>
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
    \s*<p>\s*(?:<hi\b[^>]*><lb\s*/></hi>)?/\s*START\s+LETTER\s*/\s*</p>\s*
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

META_RE = re.compile(
    r"""
    <hi\ rend="(bold|italic)"[^>]*>
    (.*?)
    </hi>
    """,
    re.X | re.S,
)

UNDERLINE_RE = re.compile(
    r"""
    <hi\ rend="underline"[^>]*>
    (.*?)
    </hi>
    """,
    re.X | re.S,
)

APOS_RE = re.compile(r"""['‘]""")

HI_ESCAPE = re.compile(
    r"""
    <hi\b[^>]*rend="(superscript|underline)"[^>]*>
    (.*?)
    </hi>
    """,
    re.X | re.S,
)

HI_UNESCAPE = re.compile(
    r"""
    <hi_(superscript|underline)>
    (.*?)
    </hi_\1>
    """,
    re.X | re.S,
)

HI_REDUCE = re.compile(
    r"""
    </hi>
    (
        \s*
        (?:
            (?:
                \[
                [^\]]*
                \]
            )
            |
            (?:
                <ptr\b[^>]*/>
            )
            |
            [.,|]
        )?
        \s*
    )
    <hi\b[^>]*>
    """,
    re.X | re.S,
)

HI_SPURIOUS = re.compile(
    r"""
    <hi\b[^>]*>
    (
        [\s\n.,:;\[\]\(\)|/…]*
    )
    </hi>
    """,
    re.X | re.S,
)

HI_SMALLCAPS = re.compile(
    r"""
    <hi\ rend="smallcaps">
    (.*?)
    </hi>
    """,
    re.X | re.S,
)

HI_MOVELB = re.compile(
    r"""
    (</hi>)
    (
        [\s\n.,:;\[\]\(\)/…]*
        [|]
        [\s\n.,:;\[\]\(\)/…]*
    )
    (</p>)
    """,
    re.X | re.S,
)
HI_TRANSLATE = re.compile(
    r"""
    <hi\b[^>]*rend="italic"[^>]*>
    """,
    re.X | re.S,
)

HI_ITALIC_STRIP = re.compile(
    r"""
    <hi\b[^>]*rend="italic"[^>]*>
    (.*?)
    </hi>
    """,
    re.X | re.S,
)

# All chars:
# [^A-Za-z0-9="/,.;:?#’…½¾(){}\[\]~|^<>àáçèÈéÉęìíñòó°ùú  ­￼*_-]
#

ALL_GLYPHS = r"""A-Za-z0-9="/?#’…½¾(){}\[\]~|^àáçèÈéÉęìíñòó°ùú*_-"""


FOOTNOTE_ROMAN = re.compile(
    rf"""
    (</hi>|<p>)
    (
        [^<{ALL_GLYPHS}]*
        [{ALL_GLYPHS}]
        [^<]*?
    )
    (<hi\b|</p>)
    """,
    re.X | re.S,
)

TRANS_SEP = re.compile(
    r"""
    ^
    (
        [\ .,;:-]*
    )
    (
        .*?
    )
    (
        [\ .,;:-]*
    )
    $
    """,
    re.X | re.S,
)

PART_SPEC = re.compile(
    r"""
    ^
    (.*?)
    (
        [,;]
        \s*
    )
    (.*)
    $
    """,
    re.X | re.S,
)

PAGE_SPEC = re.compile(
    r"""
    ^
    (.*?)
    (
        \bc?c\.
        (?:
            ,?
            \s*
            [0-9]+
            [rv]?
            (?:
                -
                [0-9rv]*
            )?
        )+
    )
    (.*)
    $
    """,
    re.X | re.S,
)


def normalizeChars(text):
    return APOS_RE.sub("’", text)


def stripP(match):
    return match.group(1).strip()


def stripNewlines(match):
    text = match.group(0)
    return text.replace("\n", " ")


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
        self.metaMarks = {}
        self.decodified = {}
        self.displaceds = {}

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
        prefix = f"{prefix}:{letter}" if letter is not None else prefix
        prefix = f"{prefix} n{textNum}" if textNum is not None else prefix
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
            self.console(f"{n:>5} {'x':<6} {heading}. See warnings.txt", error=True)

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
        senderLocI = fields[SENDERLOC]
        recipientI = fields[RECIPIENT]
        recipientLocI = fields[RECIPIENTLOC]
        summaryI = fields[SUMMARY]
        editorNotesI = fields[EDITORNOTES]
        resourcesI = fields[RESOURCES]
        shelfmarkI = fields[SHELFMARK]

        rows = [
            (r + 2, row) for (r, row) in enumerate(rows) if any(c.value for c in row)
        ]

        information = {}
        self.extraLetterData = information

        def fi(row, index):
            return row[index].value or 0

        def fs(row, index):
            result = normalizeChars(row[index].value or "")

            if result.startswith("(") and result.endswith(")"):
                result = result[1:-1]

            return htmlEsc(result)

        for r, row in rows:
            year = fi(row, yearI)
            month = f"{fi(row, monthI):>02}"
            day = f"{fi(row, dayI):>02}"
            sender = fs(row, senderI)
            senderLoc = fs(row, senderLocI)
            recipient = fs(row, recipientI)
            recipientLoc = fs(row, recipientLocI)
            summary = fs(row, summaryI)
            editorNotes = fs(row, editorNotesI)
            resources = fs(row, resourcesI)
            sep = (
                ". "
                if editorNotes and not editorNotes.rstrip().endswith(".") and resources
                else ""
            )
            shelfmark = fs(row, shelfmarkI)

            date = f"{year}-{month}-{day}"

            information.setdefault(date, []).append(
                dict(
                    row=r,
                    sender=sender,
                    senderLoc=senderLoc,
                    recipient=recipient,
                    recipientLoc=recipientLoc,
                    summary=summary,
                    editorNotes=f"{editorNotes}{sep}{resources}",
                    shelfmark=shelfmark,
                )
            )

        self.console(
            f"\tfound metadata for {sum(len(x) for x in information.values())} letters"
        )

    def trimPage(self, filza, letter, textNum, pages):
        rotateInfo = self.rotateInfo

        elements = []

        lastPage = f"{pages[-1]}"
        nPages = len(pages)
        sep = "" if nPages <= 1 else "\n"

        for i, page in enumerate(pages):
            if not page.isTrue():
                elements.append(f"""\n<p n="{page}">{EM_DASH * 3}</p>\n""")
                continue

            facs = f"{filza}_{page}"
            sameAs = "" if i == nPages - 1 else f""" sameAs="same as {lastPage}" """

            rot = rotateInfo.get(filza, {}).get(page, 0)
            elements.append(
                f"""<pb n="{page}" facs="{facs}"{sameAs} rend="{rot}"{sep}/>"""
            )

        logicalPages = "".join(elements)
        return f"""{logicalPages}"""

    def addExtra(self, info):
        pass

    def makeMoveNote(self, filza, letter):
        notes = self.notes
        notesLog = self.notesLog
        notesIt = self.notesIt
        editorialTrans = self.editorialTrans

        self.noteMark += 1
        self.noteText = None

        def insertQuote(match):
            (pre, roman, post) = match.group(1, 2, 3)
            romanl = roman.lstrip()

            if romanl != roman:
                pre += " "

            romanlr = romanl.rstrip()

            if romanlr != romanl:
                post = f" {post}"

            roman = romanlr
            return f"""{pre}"{roman}"{post}"""

        def stripItalic(match):
            it = match.group(1)
            it = WHITE_RE.sub(" ", it)

            parts = []
            rest = it

            while len(rest):
                match = PART_SPEC.match(rest)

                if match:
                    (thisIt, sep, rest) = match.group(1, 2, 3)
                else:
                    thisIt = rest
                    sep = None
                    rest = ""

                parts.append((True, thisIt))

                if sep is not None:
                    parts.append((False, sep))

            result = []

            for isIt, it in parts:
                if not isIt:
                    result.append(it)
                    continue

                rest = it

                while len(rest):
                    match = PAGE_SPEC.match(rest)

                    if match:
                        (thisIt, pages, rest) = match.group(1, 2, 3)
                    else:
                        thisIt = rest
                        pages = None
                        rest = ""

                    match2 = TRANS_SEP.match(thisIt)
                    (pre, thisIt, post) = match2.group(1, 2, 3)

                    if thisIt:
                        notesIt.setdefault(lcFirst(thisIt), []).append(
                            (f"{filza}:{letter}", self.noteText)
                        )
                        en = editorialTrans.get(thisIt, thisIt)
                    else:
                        en = ""
                    result.append(f"{pre}{en}{post}")

                    if pages is not None:
                        result.append(pages)

            return "".join(result)

        def mmm(match):
            noteMark = self.noteMark
            self.noteText = match.group(1).strip()
            line = PARA_NEWLINE_RE.sub(stripNewlines, self.noteText)
            line = line.replace("""rendition=""", """rend=""")
            line = line.replace("""rend="simple:""", '''rend="''')
            noteIn = line
            line = HI_SMALLCAPS.sub(r"\1", line)
            line = HI_ESCAPE.sub(r"<hi_\1>\2</hi_\1>", line)
            line = HI_REDUCE.sub(r"\1", line)
            line = HI_SPURIOUS.sub(r"\1", line)
            line = FOOTNOTE_ROMAN.sub(insertQuote, line)
            line = HI_ITALIC_STRIP.sub(stripItalic, line)
            line = HI_UNESCAPE.sub(r"""<hi rend="\1">\2</hi>""", line)
            line = WHITE_RE.sub(" ", line)
            noteOut = line

            noteMark = self.noteMark
            footNote = (
                f"""<note xml:id="tn{noteMark}">"""
                f"""<p><hi rend="footnote">{noteMark}</hi> """
                f"""{line}</p></note>"""
            )
            notes.append(footNote)
            notesLog[filza][letter].setdefault(noteMark, []).append((noteIn, noteOut))
            return f"""<ptr target="#tn{noteMark}" n="{noteMark}"/>"""

        return mmm

    def makeMetaRepl(self, filza, page):
        editorialTrans = self.editorialTrans
        allowedEditorials = self.allowedEditorials
        metaMarks = self.metaMarks
        decodified = self.decodified

        def mmm(match):
            rend = match.group(1)
            material = match.group(2)
            material = material.replace("\n", " ")
            materialClean = material.strip()

            if rend == "italic":
                en = editorialTrans.get(materialClean, None)
            else:
                en = materialClean
                if en not in allowedEditorials:
                    en is None

            if en is None:
                decodified[filza].setdefault(page, []).append(material)
                return f"""<hi rend="{DECODED}">{material}</hi>"""
            else:
                metaMarks[filza].setdefault(page, []).append(en)
                return f"""<metamark facs="{en}"/>"""

        return mmm

    def makeDisplacedMark(self, filza, page):
        displaceds = self.displaceds

        def mmm(match):
            material = match.group(1)
            material = material.replace("\n", " ")
            displaceds[filza].setdefault(page, []).append(material)
            return f"""<hi rend="displaced">{material}</hi>"""

        return mmm

    def transformFilza(self, file, filza):
        if self.error:
            return

        with open(f"{TEIXDIR}/{file}") as f:
            text = f.read()

        metaMarks = self.metaMarks
        metaMarks[filza] = {}

        decodified = self.decodified
        decodified[filza] = {}

        displaceds = self.displaceds
        displaceds[filza] = {}

        notesLog = self.notesLog
        notesLog[filza] = {}

        letterTexts = []
        self.pageSeq[filza] = []
        self.filzaPages[filza] = collections.defaultdict(list)
        self.filzaPageNums[filza] = {}

        letterDate = self.letterDate
        letterDate[filza] = {}

        extraLog = self.extraLog
        extraLog[filza] = {}

        letters = LETTER_SPLIT_RE.split(text)[1:]
        letters[-1] = STRIPTAIL_RE.sub("", letters[-1])

        for i, letterText in enumerate(letters):
            if "START LETTER" in letterText:
                self.pageWarn(
                    True,
                    "Undetected START LETTER",
                    filza=filza,
                    letter=i + 1,
                    textNum=None,
                )

            letterTexts.append(self.transform(filza, f"{i + 1:>03}", letterText))

        return letterTexts

    def transform(self, filza, letter, text):
        if self.error:
            return

        notesLogLetter = {}
        self.notesLog[filza][letter] = notesLogLetter
        letterDatesFilza = self.letterDate[filza]
        extraLogFilza = self.extraLog[filza]
        pageInfo = self.pageInfo
        extraLetterData = self.extraLetterData
        transcriberInfo = self.transcriberInfo
        thisTranscriberInfo = transcriberInfo[filza]
        filzaPages = self.filzaPages[filza]
        filzaPageNums = self.filzaPageNums[filza]
        pageSeq = self.pageSeq[filza]

        notes = []
        self.notes = notes

        self.noteMark = 0
        self.notes.clear()

        moveNote = self.makeMoveNote(filza, letter)

        text = NOTE_RE.sub(moveNote, text)

        text = PARA_NEWLINE_RE.sub(stripNewlines, text)
        text = text.replace("\u00a0", " ").replace("\u00ad", " ").replace("\ufffc", " ")
        textLines = text.split("\n")
        newTextLines = []
        secrTextLines = []

        textNum = None
        romanNum = None
        target = None
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
        textKind = None

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

            line = line.replace("""rendition=""", """rend=""")
            line = line.replace("""rend="simple:""", '''rend="''')
            line = line.replace("""<hi rend="italic"><lb /></hi>""", "")
            line = HI_SMALLCAPS.sub(r"\1", line)
            line = HI_ESCAPE.sub(r"<hi_\1>\2</hi_\1>", line)
            line = HI_REDUCE.sub(r"\1", line)
            line = HI_SPURIOUS.sub(r"\1", line)
            line = HI_MOVELB.sub(r"\2\1\3", line)

            match = SECTION_START_RE.match(line)

            if match:
                if textNum:
                    textInfo[textNum] = dict(
                        declared=set(pagesDeclared),
                        marks=tuple(pageMarks),
                        pages=set(textPages),
                        kind=textKind,
                    )
                    pageMarks.clear()
                    pagesDeclared.clear()
                    textPages.clear()
                    newTextLines.append("</div>")

                    if len(secrTextLines):
                        targetRep = f""" corresp="{target}" """ if target else ""
                        romanNumRep = "" if romanNum is None else f" ({romanNum})"
                        newTextLines.append(
                            f"""<div type="recipientContent" """
                            f"""facs="recipient content{romanNumRep}" """
                            f"""n="{textNum}"{targetRep}>"""
                        )
                        newTextLines.extend(secrTextLines)
                        secrTextLines.clear()
                        destLines = newTextLines
                        newTextLines.append("</div>")

                    newTextLines.append("</div>")

                textNum = normText(match.group(1))
                textNums.append(textNum)
                target = None
                textKind = None
                startSection = True
                romanNum = None
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
                    (romanNum, targetStr) = match.group(1, 2)
                    textKind = "attachment"
                    target = f"{targetStr:>03}"
                    atts = (
                        f"""facs="{romanNum}" n="{textNum}" """
                        f"""corresp="{target}" source="{pageSpecs}" """
                    )
                    newTextLines.append(f"""<div type="appendix" {atts}>""")
                else:
                    romanNum = None
                    match = LETTER_RE.match(kindSpec)

                    if match:
                        (dateSpec, placeSpec) = match.group(1, 2)
                        textKind = "letter"
                        target = None
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

                targetRep = f""" corresp="{target}" """ if target else ""
                romanNumRep = "" if romanNum is None else f" ({romanNum})"
                newTextLines.append(
                    f"""<div type="senderContent" """
                    f"""facs="sender content{romanNumRep}" """
                    f"""n="{textNum}"{targetRep}>"""
                )

                newTextLines.append(
                    line.replace("<p>", "<!--<p>").replace("</p>", "</p>-->")
                )
                continue

            match = PAGES_LINE_RE.search(line)

            if match:
                pre, pageMark, post = match.group(1, 2, 3)
                pageMarks.append(pageMark)
                pages = sorted(processPageMark(pageMark))
                pageSeq.extend([f"{filza}_{page}" for page in pages if page.isTrue()])
                newText = pre + self.trimPage(filza, letter, textNum, pages) + post
                destLines.append(newText)

                if len(pages) > 1:
                    self.pageWarn(
                        True,
                        f"multiple page mark {Page.setRep(pages)}",
                        filza=filza,
                        letter=letter,
                        textNum=textNum,
                    )
                continue

            match = SECRETARIAL_START_RE.match(line)

            if match:
                destLines = secrTextLines
                continue

            lastPage = pageSeq[-1]
            metaMarkRepl = self.makeMetaRepl(filza, lastPage)
            displacedMarkRepl = self.makeDisplacedMark(filza, lastPage)

            line = META_RE.sub(metaMarkRepl, line)
            line = HI_UNESCAPE.sub(r"""<hi rend="\1">\2</hi>""", line)
            line = UNDERLINE_RE.sub(displacedMarkRepl, line)
            line = HI_TRANSLATE.sub(r"""<hi rend="decoded">""", line)

            destLines.append(line)

        if textNum:
            textInfo[textNum] = dict(
                declared=set(pagesDeclared),
                marks=tuple(pageMarks),
                pages=set(textPages),
                kind=textKind,
            )
            newTextLines.append("</div>")

        if len(secrTextLines):
            targetRep = f""" corresp="{target}" """ if target else ""
            romanNumRep = "" if romanNum is None else f" ({romanNum})"
            newTextLines.append(
                f"""<div type="recipientContent" """
                f"""facs="recipient content{romanNumRep}" """
                f"""n="{textNum}"{targetRep}>"""
            )
            newTextLines.extend(secrTextLines)
            secrTextLines.clear()
            destLines = newTextLines
            newTextLines.append("</div>")

        newTextLines.append("</div>")

        letterDatesFilza.setdefault(normalizedDate, []).append(letter)
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
            sender = ""
            senderLoc = ""
            recipient = ""
            recipientLoc = ""
            summary = ""
            editorNotes = ""
            shelfmark = ""
        else:
            sender = extraData[SENDER]
            senderLoc = extraData[SENDERLOC]
            recipient = extraData[RECIPIENT]
            recipientLoc = extraData[RECIPIENTLOC]
            summary = extraData[SUMMARY]
            editorNotes = extraData[EDITORNOTES]
            shelfmark = extraData[SHELFMARK]

        extraLogFilza.setdefault(normalizedDate, []).append(
            dict(
                sender=sender,
                senderLoc=senderLoc,
                recipient=recipient,
                recipientLoc=recipientLoc,
                shelfmark=shelfmark,
                editorNotes=editorNotes,
                summary=summary,
            )
        )

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
            senderLoc=senderLoc,
            recipient=recipient,
            recipientLoc=recipientLoc,
            summary=summary,
            editorNotes=editorNotes,
            shelfmark=shelfmark,
            notes="\n".join(notes),
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

        with open(PAGETRANSCRIBER_TSV, "w") as rh:
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

        with open(PAGETRANSCRIBER_TSV) as rh:
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

    def readTransTable(self):
        editorialTrans = {}
        self.editorialTrans = editorialTrans

        allowedEditorials = set()
        self.allowedEditorials = allowedEditorials

        with open(TRANS_TXT) as fh:

            enLine = None
            itLine = None

            inText = None

            for i, line in enumerate(fh):
                ln = i + 1
                line = line.strip()

                if line == "# IN TEXT":
                    inText = True
                    continue

                if line == "# IN FOOTNOTES":
                    inText = False
                    continue

                if not line or line.startswith("#"):
                    continue

                if inText is None:
                    if line.startswith("IT: ") or line.startswith("EN: "):
                        console(
                            f"Error in translation table {TRANS_TXT}, line {ln}: "
                            "No IN TEXT of IN FOOTNOTES encountered "
                            "before IT or EN line",
                            error=True,
                        )
                        continue

                if line.startswith("IT: "):
                    if itLine is not None:
                        console(
                            f"Error in translation table {TRANS_TXT}, line {ln}: "
                            "Unexpected IT line",
                            error=True,
                        )
                    itLine = line[4:]
                    enLine = None
                    continue

                if line.startswith("EN: "):
                    enLine = line[4:]

                    if not enLine or enLine == "x":
                        enLine = None

                    if inText and enLine is not None:
                        allowedEditorials.add(enLine)
                        allowedEditorials.add(ucFirst(enLine))

                    if itLine is not None:
                        editorialTrans[itLine] = enLine
                        editorialTrans[ucFirst(itLine)] = ucFirst(enLine)

                    itLine = None
                    enLine = None
                    continue

                console(
                    f"Error in translation table {TRANS_TXT}, line {ln}: "
                    f"Unrecognized line: {line}",
                    error=True,
                )

    def teiFromTei(self):
        if self.error:
            return

        transcriberInfo = self.transcriberInfo
        missingInfo = self.missingInfo

        self.warnings = []
        self.pageWarnings = []
        self.pageWarningCount = 0

        letterDate = {}
        self.letterDate = letterDate

        extraLog = {}
        self.extraLog = extraLog

        notesLog = {}
        self.notesLog = notesLog

        notesIt = {}
        self.notesIt = notesIt

        extraLetterData = self.extraLetterData
        metaMarks = self.metaMarks
        decodified = self.decodified
        displaceds = self.displaceds

        self.readTransTable()
        editorialTrans = self.editorialTrans
        allowedEditorials = self.allowedEditorials

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

        with open(METAMARKS_TXT, "w") as rh:
            knownMarks = collections.Counter()
            unknownMarks = collections.Counter()

            for filza in sorted(metaMarks):
                pageData = metaMarks[filza]

                for page in sorted(pageData):
                    for mat in pageData[page]:
                        if mat in allowedEditorials:
                            knownMarks[mat] += 1
                        else:
                            unknownMarks[mat] += 1

            nUnknown = len(unknownMarks)
            totUnknown = sum(unknownMarks.values())

            if nUnknown:
                console(
                    f"Unknown editorial marks: {nUnknown} marks in {totUnknown} occs",
                    error=True,
                )

            rh.write(
                f"Unknown editorial marks encountered ({nUnknown} x {totUnknown}):\n"
            )

            for mat in sorted(unknownMarks, key=lambda x: x.lower()):
                n = unknownMarks[mat]
                rh.write(f"{n:>4} x *{mat}\n")

            nKnownMissing = 0

            for mat in allowedEditorials:
                if ucFirst(mat) not in knownMarks and lcFirst(mat) not in knownMarks:
                    nKnownMissing += 1

            if nKnownMissing:
                rh.write(
                    f"\nKnown editorial marks NOT encountered ({nKnownMissing}):\n"
                )
                console(f"{nKnownMissing} editorial marks NOT encountered", error=True)

                for mat in sorted(allowedEditorials, key=lambda x: x.lower()):
                    if (
                        ucFirst(mat) not in knownMarks
                        and lcFirst(mat) not in knownMarks
                    ):
                        rh.write(f"\t{mat}\n")
            else:
                rh.write("\nAll known editorial marks encountered\n")

            rh.write("\nKnown editorial marks encountered:\n")

            for mat in sorted(knownMarks, key=lambda x: x.lower()):
                n = knownMarks[mat]
                rh.write(f"{n:>4} x {mat}\n")

            rh.write("\nAll editorial marks with their pages:\n")

            for filza in sorted(metaMarks):
                rh.write(f"\nFilza {filza}\n")
                pageData = metaMarks[filza]

                for page in sorted(pageData):
                    for i, mat in enumerate(pageData[page]):
                        prefix = f"{page:<7}: " if i == 0 else f"{'':<9}"

                        if mat not in allowedEditorials:
                            mat = f"*{mat}"

                        rh.write(f"\t{prefix}{mat}\n")

        with open(DECODIFIED_TXT, "w") as rh:
            for filza in sorted(decodified):
                rh.write(f"\nFilza {filza}\n")
                pageData = decodified[filza]

                for page in sorted(pageData):
                    for i, mat in enumerate(pageData[page]):
                        prefix = f"{page:<7}: " if i == 0 else f"{'':<9}"
                        rh.write(f"\t{prefix}{mat}\n")

        with open(DISPLACED_TXT, "w") as rh:
            for filza in sorted(displaceds):
                rh.write(f"\nFilza {filza}\n")
                pageData = displaceds[filza]

                for page in sorted(pageData):
                    for i, mat in enumerate(pageData[page]):
                        prefix = f"{page:<7}: " if i == 0 else f"{'':<9}"
                        rh.write(f"\t{prefix}{mat}\n")

        with open(FOOTNOTESRM_TXT, "w") as rh:
            for filza in sorted(notesLog):
                rh.write(f"\nFilza {filza}\n")
                letterData = notesLog[filza]

                for letter in sorted(letterData):
                    rh.write(f"\tletter {letter}\n")
                    noteData = letterData[letter]

                    for note in sorted(noteData):
                        rh.write(f"\t\tnote {note}\n")

                        for noteIn, noteOut in noteData[note]:
                            rh.write(f"""\t\t\t"IN : {noteIn}"\n""")
                            rh.write(f"""\t\t\t"OUT: {noteOut}"\n""")

        with open(FOOTNOTESUT_TXT, "w") as rh, open(FOOTNOTESEG_TXT, "w") as xh:
            nUntrans = 0
            totUntrans = 0
            nTrans = 0
            totTrans = 0

            for it in sorted(notesIt, key=lambda x: x.lower()):
                en = editorialTrans.get(it, None)

                if en is None:
                    en = "x"
                    nUntrans += 1
                    totUntrans += n
                    occs = notesIt[it]
                    n = len(occs)
                    label = "e.g. " if n > 1 else ""
                    xh.write(f"{it}\n\t{n:>4} x {label}{occs[0][0]}\n\t{occs[0][1]}\n\n")
                    rh.write(f"{it}\n")
                else:
                    nTrans += 1
                    totTrans += n

            self.console(
                f"Translated italian editorial phrases ({nTrans} x {totTrans})"
            )

            if nUntrans:
                console(
                    "Untranslated italian editorial phrases "
                    f"({nUntrans} x {totUntrans})",
                    error=True,
                )

        with open(PAGEINFO_TXT, "w") as rh:
            for filza in sorted(pageInfo):
                rh.write(f"Filza {filza}\n")
                filzaPages = self.filzaPages[filza]
                filzaPageInfo = pageInfo[filza]
                filzaMissingInfo = missingInfo[filza] or set()

                for letter in sorted(filzaPageInfo):
                    rh.write(f"\tLetter {letter}\n")
                    letterPageInfo = filzaPageInfo[letter]["texts"]

                    nLetters = 0

                    for textNum in sorted(letterPageInfo):
                        lpInfo = letterPageInfo[textNum]
                        pagesDeclared = lpInfo["declared"]
                        pageMarks = lpInfo["marks"]
                        pages = lpInfo["pages"]
                        kind = lpInfo["kind"]

                        if kind == "letter":
                            nLetters += 1

                        rh.write(f"\t\t{kind} {textNum}\n")

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

                    if nLetters != 1:
                        label = (
                            "missing letter text"
                            if nLetters == 0
                            else "multiple letter texts"
                        )
                        self.pageWarn(
                            True,
                            label,
                            filza=filza,
                            letter=letter,
                        )

        with open(LETTERTRANSCRIBER_TXT, "w") as lh:
            for filza, letterInfo in sorted(letterTranscribers.items()):
                lh.write(f"\nFilza {filza}\n\n")
                for letter, transcribers in sorted(letterInfo.items()):
                    tRep = ", ".join(sorted(transcribers))
                    lh.write(f"\t{letter} {tRep}\n")

        writeYaml(letterDate, asFile=LETTERDATE_YML)
        writeYaml(extraLog, asFile=LETTERMETA_YML)

        dateFilza = {}

        for filza, dates in letterDate.items():
            for date in dates:
                dateFilza.setdefault(date, set()).add(filza)

        for date, filzas in sorted(dateFilza.items()):
            if len(filzas) > 1:
                filzaRep = ", ".join(filzas)
                warning = f"{date} occurs in multiple filzas: {filzaRep}"
                self.warn(filza, "", "", "", date, warning, summarize=False)

        letterDates = {}

        for dates in letterDate.values():
            for date, textLetters in dates.items():
                letterDates[date] = textLetters

        allDates = set(extraLetterData) | set(letterDates)

        warnings = []

        for date in sorted(allDates):
            textLetters = letterDates.get(date, [])
            metaLetters = extraLetterData.get(date, [])

            nTLetters = len(textLetters)
            nMLetters = len(metaLetters)

            if nTLetters == nMLetters:
                continue

            if nTLetters < nMLetters:
                for i in range(nTLetters, nMLetters):
                    letter = metaLetters[i]
                    shelfmark = letter["shelfmark"]
                    row = letter["row"]
                    filzas = dateFilza.get(date, set())
                    filza = ", ".join(sorted(filzas))
                    warning = (
                        f"{filza:2} {date}: metadata in r{row} "
                        f"for untranscribed letter {shelfmark}"
                    )
                    warnings.append(warning)
            else:
                for i in range(nMLetters, nTLetters):
                    letter = textLetters[i]
                    filzas = dateFilza[date]
                    filza = ", ".join(sorted(filzas))
                    warning = f"{filza:2} {date}: no metadata for letter {letter}"
                    warnings.append(warning)

        if len(warnings):
            console(
                f"{len(warnings)} discrepancies between summary file and letters",
                error=True,
            )
            for warning in warnings:
                self.console(f"\t{warning}", error=True)
        else:
            self.console("Metadata in summary file corresponds to transcribed letters")

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
