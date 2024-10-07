import re
from dataclasses import dataclass

from tf.core.files import expanduser, readYaml, writeJson, initTree, fileOpen, fileCopy
from tf.core.helpers import console
from tf.core.generic import AttrDict
from tf.browser.html import H
from tf.ner.helpers import toAscii


ORG = "suriano"
REPO = "letters"
BACKEND = "gitlab.huc.knaw.nl"

PAGES = "pages"
COVERS = "covers"
LOGO = "logo"

NER_NAME = "persons"
NER_NAME_M = "persons-merged"

_REPODIR = expanduser(f"~/{BACKEND}/{ORG}/{REPO}")
_PROGRAMDIR = f"{_REPODIR}/programs"
_REPORTDIR = f"{_REPODIR}/report"
_NERDIR = f"{_REPODIR}/ner/specs"
_DATADIR = f"{_REPODIR}/datasource"
_SCANINDIR = f"{_DATADIR}/scans"
_SCONFIGDIR = f"{_SCANINDIR}/config"
_SREPORTDIR = f"{_SCANINDIR}/report"
_ENTITYDIR = f"{_DATADIR}/entities"
_TRANSDIR = f"{_DATADIR}/transcriptions"
_TREPORTDIR = f"{_TRANSDIR}/report"
_ENTITYMETA_JSON = f"{_ENTITYDIR}/entitymeta.json"
_METADIR = f"{_DATADIR}/metadata"

SCANDIR = f"{_REPODIR}/scans"
SIMAGEDIR = f"{_SCANINDIR}/images"
PAGEDIR = f"{SIMAGEDIR}/{PAGES}"
COVERDIR = f"{SIMAGEDIR}/{COVERS}"
COVERINDIR = f"{_SCANINDIR}/{COVERS}"
LOGODIR = f"{SCANDIR}/{LOGO}"
LOGOINDIR = f"{_DATADIR}/{LOGO}"
MISSING_YML = f"{_SCONFIGDIR}/missing.yaml"
ROTATE_YML = f"{_SCONFIGDIR}/rotate.yaml"
EXCL_YML = f"{_SCONFIGDIR}/exclusions.yaml"
SCANERRORS_TXT = f"{_SREPORTDIR}/scanerrors.txt"
METACSS = "meta.css"
METAOUTDIR = f"{_REPODIR}/static/both/metadata"
DOCXDIR = f"{_TRANSDIR}/docx"
TEIXDIR = f"{_TRANSDIR}/teiSimple"
TRANS_TXT = f"{_TRANSDIR}/translation.txt"
PAGETRANSCRIBER_TSV = f"{_TREPORTDIR}/pagetranscriber.tsv"
HEADERS_TXT = f"{_TREPORTDIR}/headers.txt"
LETTERTRANSCRIBER_TXT = f"{_TREPORTDIR}/lettertranscriber.txt"
LETTERMETA_YML = f"{_TREPORTDIR}/lettermeta.yml"
LETTERDATE_YML = f"{_TREPORTDIR}/letterdate.yml"
PAGEINFO_TXT = f"{_TREPORTDIR}/pageinfo.txt"
METAMARKS_TXT = f"{_TREPORTDIR}/metamarks.txt"
EDITORIAL_TXT = f"{_TREPORTDIR}/editorial.txt"
DECODIFIED_TXT = f"{_TREPORTDIR}/decodified.txt"
DISPLACED_TXT = f"{_TREPORTDIR}/displaced.txt"
FOOTNOTES_TXT = f"{_TREPORTDIR}/footnotes.txt"
FOOTNOTESUT_TXT = f"{_TREPORTDIR}/footnoteuntrans.txt"
FOOTNOTESEX_TXT = f"{_TREPORTDIR}/footnoteexamples.txt"
PAGESEQ_JSON = f"{_TREPORTDIR}/pageseq.json"
SCANTRANS_TSV = f"{_TREPORTDIR}/scantrans.tsv"
SOURCEBASE = _DATADIR
TEIDIR = f"{SOURCEBASE}/tei"
THUMBDIR = f"{_REPODIR}/thumb"
THUMBPAGESDIR = f"{THUMBDIR}/{PAGES}"
THUMBCOVERDIR = f"{THUMBDIR}/{COVERS}"
SUMMARY_FILE = f"{_METADIR}/summaries.xlsx"
NO_VARIANT_TXT = f"{_METADIR}/novariant.txt"
NERIN_FILE = f"{_METADIR}/{NER_NAME}.xlsx"
NEROUT_FILE = f"{_REPODIR}/ner/specs/{NER_NAME}.xlsx"
NERIN_FILE_M = f"{_METADIR}/{NER_NAME}-merged.xlsx"
NEROUT_FILE_M = f"{_REPODIR}/ner/specs/{NER_NAME}-merged.xlsx"
REPORT_CFGERRORS = f"{_REPORTDIR}/00-cfgerrors.txt"
REPORT_THUMBERRORS = f"{_REPORTDIR}/10-thumberrors.txt"
REPORT_THUMBPAGES = f"{_REPORTDIR}/20-thumbpages.txt"
REPORT_WARNINGS = f"{_REPORTDIR}/30-warnings.txt"
REPORT_PAGEWARNINGS = f"{_REPORTDIR}/40-pagewarnings.txt"

BIS = "bis"
TER = "ter"

PAGE_STRICT_RE = re.compile(rf"""([0-9]{{1,3}})((?:{BIS}|{TER})?)([rv])([A-Z]?)""")

PAGESPEC_RE = re.compile(
    rf"""
    ^
    \s*
    ([0-9]*)
    ((?:{BIS}|{TER})?)
    \s*
    ([rv]?)
    \s*
    ([a-qA-Q]?)
    [^0-9]*
    $
    """,
    re.X | re.S,
)

PAGE_ORIG_RE = re.compile(
    rf"""
    ^
    ([0-9]+)
    ((?:{BIS}|{TER})?)
    -
    ([rv])
    $
    """,
    re.X,
)

PAGE_HEADER_RE = re.compile(
    rf"""
    ^
    ([0-9]+)
    \s*
    ((?:{BIS}|{TER})?)
    \s*
    ([rv]?)
    [^0-9]*
    $
    """,
    re.X,
)

HEADER_RE = re.compile(
    r"""
        ^
        (?:Filza)?
        (?:\ |_)?
        ([0-9]+)
        _
        [0-9]+
        (?:-[0-9]+)?
        _
        \ ?
        (
            [A-Za-z]+
            (?:_[A-Za-z]+)?
        )
        _
        (?:
            \ ?
            cc?\.
            \s*
        )?
        (.+)
        $
    """,
    re.X,
)

HEAD_PB_EXCH_RE = re.compile(
    r"""
    (
        <div\b[^>]*>
    )
    \s*
    (
        <head\b[^>]*>(.*?)<\/head>
    )
    \s*
    """,
    re.X,
)

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

NOTE_NEWLINE_RE = re.compile(
    r"""
    <note\b
    .*?
    </note>
    """,
    re.X | re.S,
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
    (\s*)
    (
        (?:
            <ptr\b
        )?
    )
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

HI_ESCAPE_RE = re.compile(
    r"""
    <hi\b[^>]*rend="(superscript|underline)"[^>]*>
    (.*?)
    </hi>
    """,
    re.X | re.S,
)

HI_UNESCAPE_RE = re.compile(
    r"""
    <hi_(superscript|underline)>
    (.*?)
    </hi_\1>
    """,
    re.X | re.S,
)

HI_REDUCE_RE = re.compile(
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

HI_SPURIOUS_RE = re.compile(
    r"""
    <hi\b[^>]*>
    (
        [\s\n.,:;\[\]\(\)|/…]*
    )
    </hi>
    """,
    re.X | re.S,
)

HI_SMALLCAPS_RE = re.compile(
    r"""
    <hi\ rend="smallcaps">
    (.*?)
    </hi>
    """,
    re.X | re.S,
)

HI_MOVELB_RE = re.compile(
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
HI_TRANSLATE_RE = re.compile(
    r"""
    <hi\b[^>]*rend="italic"[^>]*>
    """,
    re.X | re.S,
)

HI_ITALIC_RE = re.compile(
    r"""
    <hi\b[^>]*rend="italic"[^>]*>
    (.*?)
    </hi>
    """,
    re.X | re.S,
)

P_UNWRAP_RE = re.compile(
    r"""
    ^
    \s*
    <p>(.*)<\/p>
    \s*
    $
    """,
    re.X | re.S,
)

# All chars:
# [^A-Za-z0-9="/,.;:?#’…½¾(){}\[\]~|^<>àáçèÈéÉęìíñòó°ùú  ­￼*_-]

ALL_GLYPHS = r"""A-Za-z0-9="/?#’…½¾(){}\[\]~|^àáçèÈéÉęìíñòó°ùú*_-"""


FOOTNOTE_ROMAN_RE = re.compile(
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

PART_SPEC_RE = re.compile(
    r"""
    ^
    (.*?)
    (
        [.,;:()-]
        \s*
    )
    (.*)
    $
    """,
    re.X | re.S,
)

PAGE_SPEC_RE = re.compile(
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

FOL_RE_RE = re.compile(
    r"""
    ^
    (c?)c\.
    \s*
    """,
    re.X | re.S,
)


def folRepl(match):
    c1 = match.group(1)

    return "ff. " if c1 else "f. "


def normalizeChars(text):
    return APOS_RE.sub("’", text)


def stripP(match):
    return match.group(1).strip()


def stripNoteNewlines(match):
    text = match.group(0)
    return text.replace("\n", " ").replace("<p", "<..P").replace("</p", "</..P")


def stripNewlines(match):
    text = match.group(0)
    return text.replace("\n", " ").replace("<..P", "<p").replace("</..P", "</p")


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


def ucFirst(x):
    return (
        x
        if x is None or type(x) is not str or len(x) == 0
        else f"{x[0].upper()}{x[1:]}"
    )


def lcFirst(x):
    return (
        x
        if x is None or type(x) is not str or len(x) == 0
        else f"{x[0].lower()}{x[1:]}"
    )


def makeSubDiv(target, textKind, romanNum, textNum, kind):
    targetRep = f""" corresp="{target}" """ if target else ""
    romanNumRep = textKind if romanNum is None else f"{textKind} {romanNum}"
    facs = f"{kind} text of {romanNumRep}"

    return (
        f"""<div type="{kind}" facs="{facs}" n="{textNum}"{targetRep}>""",
        f"""<head>{facs}</head>"""
    )


@dataclass(init=True, order=True, frozen=True)
class Page:
    num: int
    suffix: str
    face: str
    x: str = ""

    def __repr__(self):
        return f"{self.num:>03}{self.suffix}{self.face}{self.x}"

    def isTrue(self):
        return self.x == ""

    def isSimple(self):
        return self.suffix == ""

    def zapX(self):
        return self.__class__(self.num, self.suffix, self.face, x="")

    def simplify(self):
        return self.__class__(self.num, "", self.face, x="")

    def complicate(self, sf):
        return self.__class__(self.num, BIS if sf == 2 else TER, self.face, x="")

    def flip(self):
        f = self.face
        return self.__class__(self.num, self.suffix, "v" if f == "r" else "r", x="")

    def folio(self):
        return (self.num, self.suffix)

    def isSubsequent(self, prev):
        if prev is None:
            return False

        num = self.num
        face = self.face
        suffix = self.suffix
        prevNum = prev.num
        prevFace = prev.face
        prevSuffix = prev.suffix

        return (
            face == "v"
            and prevFace == "r"
            and prevSuffix == suffix
            and prevNum == num
            or face == "r"
            and (
                prevFace is None
                and prevSuffix is None
                and prevNum is None
                or prevFace == "v"
                and (
                    prevNum == num - 1
                    and suffix == ""
                    or prevNum == num
                    and (
                        prevSuffix == ""
                        and suffix == BIS
                        or prevSuffix == BIS
                        and suffix == TER
                    )
                )
            )
        )

    @classmethod
    def parse(cls, page, kind="text"):
        header = kind == "header"
        orig = kind == "orig"
        log = kind == "log"
        text = kind == "text"

        strict = not header and not text

        match = (
            PAGE_HEADER_RE
            if header
            else PAGE_ORIG_RE if orig else PAGE_STRICT_RE if log else PAGESPEC_RE
        ).match(page)

        if match:
            if header or orig:
                (num, suffix, face) = match.group(1, 2, 3)
                x = ""
            else:
                (num, suffix, face, x) = match.group(1, 2, 3, 4)

            if strict:
                if not num.isdecimal():
                    return None
            else:
                if num == "":
                    num = "0"

            if suffix not in {"", BIS, TER}:
                return None

            if face not in {"r", "v"}:
                if strict or face != "":
                    return None

            x = x.upper()

            if x not in {"", "A", "B", "C", "D", "E"}:
                return None

            if x != "" and orig:
                return None

            return cls(int(num), suffix, face, x=x.upper())

        return None

    @classmethod
    def setRep(cls, pages):
        return ", ".join(str(p) for p in sorted(pages))


class PageInfo:
    def __init__(self, silent=False):
        self.silent = silent
        self.error = False

        initTree(_REPORTDIR, fresh=False)
        initTree(_TREPORTDIR, fresh=False)
        self.exclusions = readYaml(asFile=EXCL_YML)

        scanInfo = {}
        errors = {}

        for file, key, isdict in (
            (MISSING_YML, "missingInfo", False),
            (ROTATE_YML, "rotateInfo", True),
        ):
            data = readYaml(asFile=file)
            newData = AttrDict()
            theseErrors = []
            scanInfo[key] = newData
            errors[key] = theseErrors

            for filza, info in data.items():
                if isdict:
                    newInfo = {}
                    newData[filza] = newInfo

                    for pageStr, value in info.items():
                        page = Page.parse(pageStr, kind="log")

                        if page is None:
                            errors.append((filza, pageStr))
                            continue

                        newInfo[page] = value
                else:
                    newInfo = set()
                    newData[filza] = newInfo

                    for pageStr in info:
                        page = Page.parse(pageStr, kind="log")

                        if page is None:
                            errors.append((filza, pageStr))
                            continue

                        newInfo.add(page)

        with open(REPORT_CFGERRORS, "w") as rh:
            for key, wrongPages in errors.items():
                if len(wrongPages) == 0:
                    continue

                n = len(wrongPages)
                examples = ", ".join(wrongPages[0:5])
                msg = f"{n:>4} wrong page keys in {key}"
                console(f"\t{msg}: {examples}")

                rh.write(f"{msg}\n")

                for pageStr in wrongPages:
                    rh.write(f"\t{pageStr}\n")

        good = sum(len(x) for x in errors.values()) == 0

        if not good:
            self.error = True
            return

        self.missingInfo = scanInfo.get("missingInfo", {})
        self.rotateInfo = scanInfo.get("rotateInfo", {})

    def console(self, *args, **kwargs):
        """Print something to the output.

        This works exactly as `tf.core.helpers.console`

        When the silent member of the object is True, the message will be suppressed.
        """
        silent = self.silent

        if not silent:
            console(*args, **kwargs)


def distilPages(pageSpec, asDeclared, simpleOnly=False, knownPages=None):
    specs = pageSpec.split("-", 1)
    (fromSpec, toSpec) = (specs[0], specs[0]) if len(specs) == 1 else specs

    fromPage = Page.parse(fromSpec, kind="text")
    toPage = Page.parse(toSpec, kind="text")

    if fromPage is None:
        return (f"no valid start page given: {fromSpec}", set())

    if toPage is None:
        return (f"no valid end page given: {toSpec}", set())

    if simpleOnly:
        fromPage = fromPage.simplify()
        toPage = toPage.simplify()

    toNum = toPage.num
    toSuffix = toPage.suffix
    toFace = toPage.face

    if toNum == 0:
        toNum = fromPage.num
        toSuffix = fromPage.suffix if toPage.suffix == "" else toPage.suffix
        toFace = "v" if toPage.face == "" else toPage.face

    toPage = Page(toNum, toSuffix, toFace, x=toPage.x)

    if knownPages is not None:
        fromZap = fromPage.zapX()
        toZap = toPage.zapX()

        if fromZap in knownPages:
            fromPage = fromZap
        if toZap in knownPages:
            toPage = toZap

    warnings = ", ".join(
        p.x for p in (fromPage, toPage) if asDeclared and not p.isTrue()
    )

    pages = {fromPage, toPage}

    fn = fromPage.num
    ff = fromPage.face
    fs = fromPage.suffix
    tn = toPage.num
    tf = toPage.face
    ts = toPage.suffix

    if (fn, fs) != (tn, ts):
        if ff == "r":
            pages.add(Page(fn, fs, "v"))

        if fn == tn:
            if ts == TER:
                if fs == "":
                    pages.add(Page(fn, BIS, "r"))
                    pages.add(Page(fn, BIS, "v"))
        else:
            for p in range(fn, tn + 1):
                if p == fn:
                    pass
                elif p == tn:
                    if ts == TER:
                        pages.add(Page(tn, BIS, "r"))
                        pages.add(Page(tn, BIS, "v"))
                    elif ts == BIS:
                        pages.add(Page(tn, "", "r"))
                        pages.add(Page(tn, "", "v"))
                else:
                    pages.add(Page(p, "", "r"))
                    pages.add(Page(p, "", "v"))

        if tf == "v":
            pages.add(Page(tn, ts, "r"))

    return (warnings, pages)


META_TEMPLATE = """\
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8"/>
        <title>{title}</title>
        <link rel="stylesheet" href="{metaCss}"/>
    </head>
    <body>{material}</body>
</html>
"""

URL_RE = re.compile(r"""(https://)([^/\s]+)((?:/\S+)?)""")


def nerMeta(metaFields, metaData, suppressEmpty=True, skip={"kind"}, silent=True):
    initTree(METAOUTDIR, fresh=True, gentle=True)
    fileCopy(f"{_PROGRAMDIR}/{METACSS}", f"{METAOUTDIR}/{METACSS}")

    toc = []

    json = {}

    for metaKey, values in metaData.items():
        toc.append((values[0], metaKey))

        thisMeta = {
            field: URL_RE.sub(r"""<a href="\1\2\3">\2</a>""", value)
            for (field, value) in zip(metaFields, values)
            if (not suppressEmpty or len(value.strip()) > 0)
            and field.lower() not in skip
        }
        json[metaKey] = thisMeta

        material = H.table(
            H.join(
                [
                    H.tr(
                        [
                            H.td(field, cls="label"),
                            H.td(
                                URL_RE.sub(r"""<a href="\1\2\3">\2</a>""", value),
                                cls="value",
                            ),
                        ],
                        cls=f"{field} section",
                    )
                    for (field, value) in thisMeta.items()
                ],
                sep="\n",
            ),
            eidkind="{metaKey}",
            cls="metadata",
        )

        with fileOpen(f"{METAOUTDIR}/{metaKey}.html", "w") as fh:
            fh.write(
                META_TEMPLATE.format(title=metaKey, metaCss=METACSS, material=material)
            )

    with fileOpen(f"{METAOUTDIR}/__index__.html", "w") as fh:
        toc = H.div(
            H.join(
                [
                    H.div(H.a(name, href=f"{link}.html"))
                    for (name, link) in sorted(toc, key=lambda x: toAscii(x[0]))
                ],
                sep="\n",
            ),
            cls="toc",
        )
        fh.write(
            META_TEMPLATE.format(title="table of names", metaCss=METACSS, material=toc)
        )

    writeJson(json, asFile=_ENTITYMETA_JSON)
