import re
from processhelpers import TEIDIR, TEIBAREDIR

from tf.core.helpers import console
from tf.core.files import initTree

WHITE_RE = re.compile(r"""\s+""", re.S)


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
                tokens = tuple((s, F.str.v(s)) for s in E.oslots.s(ent))
                fl = L.u(eslots[0], otype="file")[0]
                lookupEnts.setdefault(fl, []).append((fl, tokens, entity))

        nEnts = sum(len(v) for v in lookupEnts.values())
        console(f"{len(lookupEntities)} entities with {nEnts} occurrences")

    def bakeCorpus(self, filza=None, file=None):
        F = self.F
        L = self.L
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

            for fl in flNodes:
                flRep = F.file.v(fl)

                if file is not None and file != flRep:
                    continue

                console(f"\t\tletter {flRep}")
                letterFile = f"{filzaDir}/{flRep}.xml"
                newLetterFile = f"{newFilzaDir}/{flRep}.xml"

                with open(letterFile) as fh:
                    xmlText = fh.read()

                allTokens = tuple((s, F.str.v(s)) for s in L.d(fl, otype="t"))
                ents = lookupEnts.get(fl, [])

                (flGood, newXmlText) = self.bakeFile(fzRep, flRep, xmlText, allTokens, ents)

                if not flGood:
                    fzGood = False

                with open(newLetterFile, "w") as fh:
                    fh.write(newXmlText)

            status = "all good" if fzGood else "some files failed to match"
            console(f"\tfilza {fzRep}, {status}")

            if not fzGood:
                corpusGood = False

        status = "all good" if corpusGood else "some files failed to match"
        console(f"Done, {status}")

    def bakeFile(self, filza, file, xmlText, allTokens, ents):
        nXml = len(xmlText)
        nTokens = len(allTokens)
        nEnts = len(ents)
        console(f"\t\t\txml: {nXml:>5} chars; {nTokens:>5} tokens; {nEnts:>3} ents")

        xPos = 0
        good = True

        for i, s in allTokens:
            if s is None or s == "\u200b" or s.strip() == "":
                continue

            found = xmlText.find(s, xPos, -1)
            nS = len(s)

            if found == -1:
                foundRep = "XX"
            else:
                foundRep = "OK"
                xPos = found

            preStart = max((0, xPos - 30))
            pre = WHITE_RE.sub(" ", xmlText[preStart:xPos]).strip()

            if found != -1:
                xPos += nS

            postEnd = min((xPos + 30, nXml))
            post = WHITE_RE.sub(" ", xmlText[xPos:postEnd]).strip()

            # console(f"{i:>5} {foundRep} {pre}┣{s}┫{post}")

            if found == -1:
                good = False
                console(f"{i:>5} {foundRep} {pre}┣{s}┫{post}")
                break

        newXmlText = xmlText

        return (good, newXmlText)
