import collections
import re
import json

from analiticcl import VariantModel, Weights, SearchParameters

from tf.core.files import initTree, fileExists
from tf.core.helpers import console
from tf.convert.recorder import Recorder


HTML_PRE = """<html>
<head>
    <meta charset="utf-8"/>
    <style>
«css»
    </style>
</head>
<body>
"""

HTML_POST = """
</body>
</html>
"""


def readJson(asFile=None):
    with open(asFile) as fh:
        result = json.load(fh)
    return result


def writeJson(data, asFile=None):
    with open(asFile, "w") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)


class Detect:
    def __init__(self, A, sheet):
        self.A = A
        self.sheet = sheet

        workDir = f"{A.context.localDir}/{A.context.extraData}/analyticcl"
        self.workDir = workDir
        initTree(workDir, fresh=False)

        NE = A.makeNer()
        self.NE = NE

        NE.setSheet(sheet, caseSensitive=True, force=True)
        sheetData = NE.getSheetData()

        console("Overview of names by length:")
        triggers = set(sheetData.rowMap)

        lengths = collections.defaultdict(list)

        for trigger in triggers:
            lengths[len(trigger.split())].append(trigger)

        for n, trigs in sorted(lengths.items(), key=lambda x: -x[0]):
            examples = "\n      ".join(sorted(trigs, key=lambda x: x.lower())[0:5])
            console(f"  {n} tokens: {len(trigs):>3} names e.g.:\n      {examples}")

    def prepare(self):
        self.makeAlphabet()
        self.makeText()
        self.makeLexicon()
        self.setupAnaliticcl()

    def search(self, start=None, end=None, score_threshold=0.8, force=0):
        A = self.A
        model = self.model
        rec = self.rec
        textComplete = self.textComplete
        workDir = self.workDir
        lexiconOccs = self.lexiconOccs

        text = textComplete[start:end]
        nText = len(text)

        offset = 0 if start is None else nText + start if start < 0 else start

        console(f"{nText:>8} text  length")
        console(f"{offset:>8} offset in complete text")

        matchesFile = f"{workDir}/matches-{start}-{end}.json"
        matchesPosFile = f"{workDir}/matchespos-{start}-{end}.json"
        rawMatchesFile = f"{workDir}/rawmatches-{start}-{end}.json"

        A.indent(reset=True)

        if force == 2 or not fileExists(rawMatchesFile):
            A.info("Compute variants of the lexicon words ...")
            rawMatches = model.find_all_matches(
                text,
                SearchParameters(
                    unicodeoffsets=True,
                    max_ngram=4,
                    freq_weight=0.25,
                    score_threshold=score_threshold,
                ),
            )
            writeJson(rawMatches, asFile=rawMatchesFile)
        else:
            A.info("Read previously computed variants of the lexicon words ...")
            rawMatches = readJson(asFile=rawMatchesFile)

        A.info(f"{len(rawMatches):>8} raw   matches")

        if force == 1 or not fileExists(matchesFile) or not fileExists(matchesPosFile):
            A.info("Filter variants of the lexicon words ...")
            positions = rec.positions(simple=True)

            matches = {}
            matchPositions = collections.defaultdict(list)

            for match in rawMatches:
                text = match["input"].replace("\n", " ")
                textL = text.lower()

                if text in lexiconOccs:
                    continue

                candidates = match["variants"]

                if len(candidates) == 0:
                    continue

                candidates = {
                    cand["text"]: s
                    for cand in candidates
                    if (s := cand["score"]) >= score_threshold
                }

                if len(candidates) == 0:
                    continue

                textRemove = set()

                for cand in candidates:
                    candL = cand.lower()
                    if candL == textL:
                        textRemove.add(cand)

                for cand in textRemove:
                    del candidates[cand]

                if len(candidates) == 0:
                    continue

                # if the match ends with 's we remove the part without it from the
                # candidates

                if text.endswith("'s"):
                    head = text.removesuffix("'s")
                    if head in candidates:
                        del candidates[head]

                        if len(candidates) == 0:
                            continue

                # we have another need to filter: if the text of a match is one short
                # word longer than a candidate we remove that candidate
                # provided the extra word is lower case and has at most 3 letters
                # this is to prevent cases like
                # «Adam Schivelbergh» versus «Adam Schivelbergh di»
                #
                # We do this also when the extra word is at the start, like
                # «di monsignor Mangot» versus «monsignor Mangot»

                parts = text.split()

                if len(parts) > 0:
                    (head, tail) = (parts[0:-1], parts[-1])

                    if len(tail) <= 3 and tail.islower():
                        head = " ".join(head)

                        if head in candidates:
                            del candidates[head]

                            if len(candidates) == 0:
                                continue

                    (head, tail) = (parts[0], parts[1:])

                    if len(head) <= 3 and head.islower():
                        tail = " ".join(tail)

                        if tail in candidates:
                            del candidates[tail]

                            if len(candidates) == 0:
                                continue

                position = match["offset"]
                start = position["begin"]
                end = position["end"]
                nodes = sorted(
                    {positions[i] for i in range(offset + start, offset + end)}
                )

                matches[text] = candidates
                matchPositions[text].append(nodes)

            writeJson(matches, asFile=matchesFile)
            writeJson(matchPositions, asFile=matchesPosFile)
        else:
            A.info("Read previously filtered variants of the lexicon words ...")
            matches = readJson(asFile=matchesFile)
            matchPositions = readJson(asFile=matchesPosFile)

        A.info(f"{len(matches):>8} filtered matches")

        self.matches = matches
        self.matchPositions = matchPositions

    def listResults(self, start=None, end=None):
        workDir = self.workDir
        matches = self.matches

        lines = []

        head = ("variant", "score", "candidate")
        dash = f"{'-' * 4} | {'-' * 25} | {'-' * 5} | {'-' * 25}"
        console(f"{'i':>4} | {head[0]:<25} | {head[1]} | {head[2]}")
        console(f"{dash}")
        startN = start or 0

        for text, candidates in sorted(matches.items()):
            for cand, score in sorted(candidates.items()):
                lines.append((text, score, cand))

        for i, (text, score, cand) in enumerate(lines[start:end]):
            console(f"{i + startN:>4} | {text:<25} |  {score:4.2f} | {cand}")

        console(f"{dash}")

        file = f"{workDir}/variants.tsv"

        with open(file, "w") as fh:
            fh.write(f"{'\t'.join(head)}\n")
            for text, score, cand in lines:
                fh.write(f"{text}\t{score:4.2f}\t{cand}\n")

        console(f"{len(matches)} variants found and written to {file}")

    def showResults(self, start=None, end=None):
        A = self.A
        F = A.api.F
        matches = self.matches
        matchPositions = self.matchPositions

        i = 0

        for text, candidates in sorted(matches.items())[start:end]:
            i += 1
            nCand = len(candidates)
            pl = "" if nCand == 1 else "s"
            console(f"{i:>4} Variant «{text}» of {nCand} candidate{pl}")
            console("  Occurrences:")
            occs = matchPositions[text]

            for nodes in occs:
                sectionStart = A.sectionStrFromNode(nodes[0])
                sectionEnd = A.sectionStrFromNode(nodes[-1])
                section = (
                    sectionStart
                    if sectionStart == sectionEnd
                    else f"{sectionStart} - {sectionEnd}"
                )
                preStart = max((nodes[0] - 10, 1))
                preEnd = nodes[0]
                postStart = nodes[-1] + 1
                postEnd = min((nodes[-1] + 10, F.otype.maxSlot + 1))
                preText = "".join(
                    f"{F.str.v(n)}{F.after.v(n)}" for n in range(preStart, preEnd)
                )
                inText = "".join(f"{F.str.v(n)}{F.after.v(n)}" for n in nodes)
                postText = "".join(
                    f"{F.str.v(n)}{F.after.v(n)}" for n in range(postStart, postEnd)
                )
                context = f"{section}: {preText}«{inText}»{postText}".replace("\n", " ")
                console(f"    {context}")

            console("  Candidates with score:")

            for cand, score in sorted(candidates.items(), key=lambda x: (-x[1], x[0])):
                console(f"\t{score:4.2f} {cand}")

            console("-----")

    def displayResults(self, start=None, end=None, asFile=None):
        A = self.A
        L = A.api.L
        matches = self.matches
        matchPositions = self.matchPositions
        lexiconOccs = self.lexiconOccs
        workDir = self.workDir

        if asFile is not None:
            content = []

            htmlStart = HTML_PRE.replace("«css»", A.context.css)
            htmlEnd = HTML_POST

            content.append([htmlStart])
            empty = True

            A.indent(reset=True)
            A.info("Gathering information on extra triggers ...")

        i = 0
        s = 0

        for varText, candidates in sorted(
            matches.items(), key=lambda x: (-len(x[1]), x[0])
        )[start:end]:
            i += 1

            # make a list of where the candidates are and include the score

            varOccs = matchPositions[varText]
            nVar = len(varOccs)

            candOccs = []
            candRep1 = "`" + "` or `".join(candidates) + "`"
            candRep2 = "<code>" + "</code> or <code>".join(candidates) + "</code>"

            for cand, score in candidates.items():
                myOccs = lexiconOccs[cand]

                for occ in myOccs:
                    candOccs.append((occ[0], score, cand, occ))

            # use this list later to find the nearest/best variant

            if asFile is None:
                A.dm(
                    f"# {i}: {nVar} x variant `{varText}` on "
                    f"candidate {candRep1}\n\n"
                )
            else:
                content[-1].append(
                    f"<h1>{i}: {nVar} x variant <code>{varText}</code> on "
                    f"candidate {candRep2}</h1>"
                )
                empty = False

            sections = set()
            highlights = {}
            bestCand = None

            for candOcc in candOccs:
                if bestCand is None or bestCand[1] < candOcc[1]:
                    bestCand = candOcc

            for n in bestCand[3]:
                highlights[n] = "lightgreen"

            section = L.u(bestCand[0], otype="chunk")[0]
            sections.add(section)

            for varNodes in varOccs:
                highlights |= {n: "goldenrod" for n in varNodes}

                nFirst = varNodes[0]
                section = L.u(nFirst, otype="chunk")[0]
                sections.add(section)

                nearestCand = None

                for candOcc in candOccs:
                    if nearestCand is None or abs(nearestCand[0] - nFirst) > abs(
                        candOcc[0] - nFirst
                    ):
                        nearestCand = candOcc

                for n in nearestCand[3]:
                    if n in highlights:
                        highlights[n] = "yellow"
                    else:
                        highlights[n] = "cyan"

                section = L.u(nearestCand[0], otype="chunk")[0]
                sections.add(section)

            sections = tuple((s,) for s in sorted(sections))

            s += len(sections)

            if asFile is None:
                A.table(sections, highlights=highlights, full=True)
            else:
                content[-1].append(
                    A.table(sections, highlights=highlights, full=True, _asString=True)
                )

                if i % 10 == 0:
                    A.info(f"{i:>4} variants done giving {s:>4} chunks")
                if i % 100 == 0:
                    content[-1].append(htmlEnd)
                    content.append([htmlStart])
                    empty = True

        A.info(f"{i:>4} matches done")

        if asFile is not None:
            content[-1].append(htmlEnd)
            if empty:
                content.pop()

            extraFileBase = f"{workDir}/extra"
            initTree(extraFileBase, fresh=True, gentle=True)

            for i, material in enumerate(content):
                extraFile = f"{extraFileBase}/{asFile}{i + 1:>02}.html"

                with open(extraFile, "w") as fh:
                    fh.write("\n".join(material))

                console(f"Extra triggers written to {extraFile}")

    def makeAlphabet(self):
        A = self.A
        C = A.api.C
        workDir = self.workDir

        alphabetFile = f"{workDir}/alphabet.tsv"
        self.alphabetFile = alphabetFile

        with open(alphabetFile, "w") as fh:
            # This file will consist of one character per line,
            # for each distinct alpha character in the corpus, ordered by frequency.
            # Numeric characters will be put on a single line, with tabs in between.
            # All other characters will be ignored.

            digits = []

            for c, freq in C.characters.data["text-orig-full"]:
                if c.isalpha():
                    fh.write(f"{c}\n")
                elif c.isdigit():
                    digits.append(c)
            fh.write("\t".join(digits))

        console(f"Alphabet written to {alphabetFile}")

    def makeText(self):
        NE = self.NE
        A = self.A
        api = A.api
        F = A.api.F
        L = A.api.L
        workDir = self.workDir

        rec = Recorder(api)

        lineType = NE.settings.lineType
        slotType = F.otype.slotType
        maxSlot = F.otype.maxSlot
        lines = F.otype.s(lineType)
        lineEnds = {L.d(ln, otype=slotType)[-1] for ln in lines}
        skipTo = None

        for t in range(1, maxSlot + 1):
            tp = t + 1
            tpp = t + 2

            if tp in lineEnds and tp < maxSlot and F.str.v(tp) == "-":
                rec.start(t)
                rec.add(f"{F.str.v(t)}{F.after.v(t)}")
                rec.end(t)
                rec.start(tpp)
                rec.add(f"{F.str.v(tpp)}{F.after.v(tpp)}\n")
                rec.end(tpp)
                skipTo = tpp
            elif skipTo is not None:
                if t < skipTo:
                    continue
                else:
                    skipTo = None
            else:
                rec.start(t)
                rec.add(f"{F.str.v(t)}{F.after.v(t)}")
                rec.end(t)

        self.rec = rec
        textComplete = rec.text()
        self.textComplete = textComplete

        textFile = f"{workDir}/text.txt"

        with open(textFile, "w") as fh:
            fh.write(textComplete)

        console(f"Text written to {textFile} - {len(textComplete)} characters")

    def makeLexicon(self):
        A = self.A
        NE = self.NE
        workDir = self.workDir

        sheetData = NE.getSheetData()
        NEinventory = sheetData.inventory

        A.indent(reset=True)
        A.info("Collecting the triggers for the lexicon")

        inventory = {}

        for eidkind, triggers in NEinventory.items():
            for trigger, scopes in triggers.items():
                inventory.setdefault(trigger, set())

                for occs in scopes.values():
                    for slots in occs:
                        inventory[trigger].add(tuple(slots))

        A.info(f"{len(inventory)} triggers collected")

        remSpaceRe = re.compile(r""" +([^A-Za-z])""")
        accentSpaceRe = re.compile(r"""([’']) +""")

        lexicon = {}
        mapNormal = {}

        lexiconOccs = {}
        self.lexiconOccs = lexiconOccs

        for name, occs in inventory.items():
            occStr = name
            occNormal = remSpaceRe.sub(r"\1", occStr)
            occNormal = accentSpaceRe.sub(r"\1", occNormal)
            nOccs = len(occs)
            lexicon[occNormal] = nOccs
            mapNormal[occNormal] = occStr
            lexiconOccs[occNormal] = occs

        sortedLexicon = sorted(lexicon.items(), key=lambda x: (-x[1], x[0].lower()))

        for name, n in sortedLexicon[0:10]:
            console(f"  {n:>3} x {name}")

        console("  ...")

        for name, n in sortedLexicon[-10:]:
            console(f"  {n:>3} x {name}")

        console(f"{len(lexicon):>8} lexicon length")

        lexiconFile = f"{workDir}/lexicon.tsv"
        self.lexiconFile = lexiconFile

        with open(lexiconFile, "w") as fh:
            for name, n in sorted(lexicon.items()):
                fh.write(f"{name}\t{n}\n")

        console(f"Lexicon written to {lexiconFile}")

    def setupAnaliticcl(self):
        alphabetFile = self.alphabetFile
        lexiconFile = self.lexiconFile

        console("Set up analiticcl")

        model = VariantModel(
            alphabetFile, Weights(ld=0.3, lcs=0.1, prefix=0.1, suffix=0.1, case=0.4)
        )
        self.model = model
        model.read_lexicon(lexiconFile)
        model.build()
