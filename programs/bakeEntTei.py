import re
from processhelpers import (
    TEIDIR,
    TEIBAREDIR,
    NERCORRECT_YML,
    NERCORRECT_REPORT_YML,
    detag,
    retag,
)

from tf.core.generic import deepdict
from tf.core.helpers import console
from tf.core.files import initTree, readYaml, writeYaml

WHITE_RE = re.compile(r"""\s+""", re.S)

ENT_ELEM_START = """<name type="person" key="{eid}" fullName="{ename}">"""
ENT_ELEM_END = "</name>"


class BakeEntTei:
    def __init__(self, app):
        self.app = app
        api = app.api
        E = api.E
        self.E = E
        F = api.F
        self.F = F
        L = api.L
        self.L = L

        console("Making entity index ...")
        entityNodes = F.otype.s("entity")
        lookupEntities = {}
        self.lookupEntities = lookupEntities
        lookupEnts = {}
        self.lookupEnts = lookupEnts

        for entity in entityNodes:
            eid = F.eid.v(entity)
            ename = F.ename.v(entity)
            ents = E.eoccs.f(entity)
            lookupEntities[entity] = (eid, ename)

            for ent in ents:
                eslots = E.oslots.s(ent)
                firstSlot = eslots[0]
                lastSlot = eslots[-1]
                fl = L.u(eslots[0], otype="file")[0]
                lookupEnts.setdefault(fl, []).append((firstSlot, lastSlot, entity))

        nEnts = sum(len(v) for v in lookupEnts.values())
        console(f"{len(lookupEntities)} entities with {nEnts} occurrences")

    def bakeCorpus(self, filza=None, file=None):
        F = self.F
        L = self.L

        corrections = readYaml(asFile=NERCORRECT_YML)

        lookupEnts = self.lookupEnts

        fzNodes = F.otype.s("folder")

        if filza is not None:
            if type(filza) is int:
                filza = f"{filza:>02}"
            else:
                if filza.endswith("b"):
                    filza = f"{int(filza.removesuffix("b")):>02}b"
                else:
                    filza = f"{int(filza):>02}"

        if file is not None:
            if type(file) is int:
                file = f"{file:>03}"
            else:
                file = f"{int(file):>03}"

        scopeRep = (
            "whole corpus"
            if filza is None and file is None
            else (
                f"filza {filza} only"
                if file is None
                else (
                    f"files {file} in all filzas only"
                    if filza is None
                    else f"file {filza}:{file} only"
                )
            )
        )
        console(f"Bake entities into TEI in {TEIBAREDIR} ({scopeRep}) ...")
        corpusGood = True

        for fz in fzNodes:
            fzRep = F.folder.v(fz)

            if filza is not None and filza != fzRep:
                continue

            console(f"\tfilza {fzRep}")
            filzaDir = f"{TEIBAREDIR}/{fzRep}"
            newFilzaDir = f"{TEIDIR}/{fzRep}"
            initTree(newFilzaDir, fresh=True, gentle=True)
            flNodes = L.d(fz, otype="file")
            fzGood = True

            limit = 5
            i = 0

            for fl in flNodes:
                flRep = F.file.v(fl)

                if file is not None and file != flRep:
                    continue

                letterFile = f"{filzaDir}/{flRep}.xml"
                newLetterFile = f"{newFilzaDir}/{flRep}.xml"

                with open(letterFile) as fh:
                    xmlText = fh.read()

                allTokens = tuple((s, F.str.v(s)) for s in L.d(fl, otype="t"))
                ents = lookupEnts.get(fl, [])
                nEnts = len(ents)
                cr = "" if i < limit < 5 else "\r"
                console(
                    f"{cr}\t\tletter {flRep} ({nEnts:>3} entities)", newline=i < limit
                )
                i += 1

                (flGood, newXmlText) = self.bakeFile(
                    fzRep, flRep, xmlText, allTokens, ents
                )

                if flGood:
                    letterCorrections = corrections.get(fzRep, {}).get(flRep, None)

                    if letterCorrections is not None:
                        (corrGood, nApplied, nFailed, kinds, newXmlText) = self.correct(
                            newXmlText, letterCorrections
                        )
                        rep = f"{nApplied} applied, {nFailed} failed"
                        kindRep = ", ".join(kinds)
                        console(
                            f"{cr}\t\tletter {flRep} ({nEnts:>3} entities: "
                            f"correction(s): {kindRep} {rep}",
                            error=not corrGood,
                        )
                        if not corrGood:
                            fzGood = False
                else:
                    console(
                        f"{cr}\t\tletter {flRep} ({nEnts:>3} entities: matching failed",
                        error=True,
                    )
                    fzGood = False

                with open(newLetterFile, "w") as fh:
                    fh.write(newXmlText)

            if i > limit:
                console("\n")

            status = "all good" if fzGood else "some files failed"
            console(f"\tfilza {fzRep}, {status}", error=not fzGood)

            if not fzGood:
                corpusGood = False

        writeYaml(deepdict(corrections, ordinary=True), asFile=NERCORRECT_REPORT_YML)
        status = "all good" if corpusGood else "some files failed"
        console(f"Done, {status}", error=not corpusGood)

    def bakeFile(self, filza, file, xmlText, allTokens, ents):
        if len(ents) == 0:
            return (True, xmlText)

        lookupEntities = self.lookupEntities

        (tags, plainText) = detag(xmlText)

        nXml = len(plainText)

        xPos = 0
        good = True
        mapping = {}

        for s, t in allTokens:
            if t is None or t == "\u200b" or t.strip() == "":
                continue

            nT = len(t)

            whole = False
            offset = xPos

            while not whole:
                found = plainText.find(t, offset, -1)

                if found == -1:
                    break

                endPos = found + nT
                endPosMin = endPos - 1
                whole = (
                    endPos >= nXml
                    or not plainText[endPosMin].isalnum()
                    or not plainText[endPos].isalnum()
                )

                if not whole:
                    offset = found + 1

            if found == -1:
                foundRep = "XX"
            else:
                foundRep = "OK"
                xPos = found
                mapping[(s, -1)] = xPos

            preStart = max((0, xPos - 30))
            pre = WHITE_RE.sub(" ", plainText[preStart:xPos]).strip()

            if found != -1:
                xPos += nT
                mapping[(s, 1)] = xPos

            postEnd = min((xPos + 30, nXml))
            post = WHITE_RE.sub(" ", plainText[xPos:postEnd]).strip()

            if found == -1:
                good = False
                console(f"slot {s:>6} {foundRep} {pre}┣{t}┫{post}")
                break

        if not good:
            return (good, xmlText)

        entSlots = set()

        for firstSlot, lastSlot, entity in ents:
            entSlots.add((firstSlot, -1, entity))
            entSlots.add((lastSlot, 1, entity))

        entSlots = sorted(entSlots)

        newPlainText = ""
        xPos = 0

        for eSlot, pos, entity in entSlots:
            nextPos = mapping[(eSlot, pos)]
            newPlainText += plainText[xPos:nextPos]
            xPos = nextPos

            if pos == -1:
                eInfo = lookupEntities[entity]
                (eid, ename) = eInfo
                newPlainText += ENT_ELEM_START.format(eid=eid, ename=ename)
            else:
                newPlainText += ENT_ELEM_END

        newPlainText += plainText[xPos:]
        newXmlText = retag(tags, newPlainText)

        return (good, newXmlText)

    def correct(self, xmlText, corrections):
        textLines = xmlText.split("\n")
        nLines = len(textLines)

        good = True
        kinds = []
        nApplied = 0
        nFailed = 0

        for correction in corrections:
            kind = correction.kind
            tweaks = correction.tweaks

            kinds.append(kind)
            corrGood = True

            for tweak in tweaks:
                line = tweak.line
                orig = tweak.orig
                new = tweak.new

                if line > nLines:
                    tweak.status = "failed"
                    tweak.reason = f"line {line} > {nLines} (lines in file)"
                    corrGood = False

                text = textLines[line - 1]

                n = text.count(orig)

                if n == 1:
                    textLines[line - 1] = text.replace(orig, new)
                    tweak.status = "applied"
                else:
                    tweak.status = "failed"
                    tweak.reason = f"occurs {n} times"
                    corrGood = False

            if corrGood:
                nApplied += 1
            else:
                good = False
                nFailed += 1

        return (good, nApplied, nFailed, kinds, "\n".join(textLines))
