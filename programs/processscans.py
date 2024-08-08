from subprocess import run
from tf.core.helpers import console
from tf.core.files import (
    dirContents,
    dirExists,
    dirRemove,
    dirCopy,
    initTree,
    fileExists,
    fileCopy,
    extNm,
    stripExt,
    fileRemove,
)
from processhelpers import (
    COVERS,
    PAGES,
    SCANDIR,
    SIMAGEDIR,
    COVERDIR,
    COVERINDIR,
    LOGODIR,
    LOGOINDIR,
    PAGEDIR,
    THUMBDIR,
    SCANERRORS_TXT,
    Page,
    PageInfo,
)


SCAN_QUALITY = "22%"
SCAN_RESIZE = "22%"
SCAN_COMMAND = "/opt/homebrew/bin/magick"

SCAN_OPTIONS = ["-quality", SCAN_QUALITY, "-resize", SCAN_RESIZE]
SCAN_EXT = ("jpg", "jpg")

SIZES_COMMAND = "/opt/homebrew/bin/identify"
SIZES_OPTIONS = ["-ping", "-format", "%w %h"]

DS_STORE = ".DS_Store"


class Scans(PageInfo):
    def __init__(self, silent=False, force=False):
        self.force = force
        self.error = False

        PageInfo.__init__(self, silent=silent)

    def ingest(self, dry=False):
        if self.error:
            return

        force = self.force

        self.ingestLogo(dry=dry)

        for kind in (COVERS, PAGES):
            dstDir = f"{SCANDIR}/{kind}"

            if dirExists(dstDir) and not force and not dry:
                self.console(
                    f"\tAlready ingested {kind}. "
                    f"Remove {dstDir} or pass --force to ingest again"
                )
            else:
                if kind == COVERS:
                    self.ingestCovers(dry=dry)
                else:
                    self.ingestPages(dry=dry)

    def ingestPages(self, dry=False):
        if self.error:
            return

        silent = self.silent
        exclusions = self.exclusions
        missingInfo = self.missingInfo
        rotateInfo = self.rotateInfo
        scanExt = SCAN_EXT[0]

        filzas = sorted(f for f in dirContents(SIMAGEDIR)[1] if f.isdecimal())

        errors = {}

        def error(msg, item):
            errors.setdefault(msg, []).append(item)

        toCopy = []
        rotations = {}

        for filza in filzas:
            filzaExclusions = exclusions[filza]

            skipping = False
            startAt = None
            nSkipped = None

            if filzaExclusions is not None:
                if filzaExclusions.exclude:
                    continue

                startAt = filzaExclusions.startAt

                if startAt is not None:
                    skipping = True
                    nSkipped = 0

            filzaMissing = missingInfo.get(filza, set())
            filzaDir = f"{SIMAGEDIR}/{filza}"
            self.console(f"\t{filza}")
            cents = sorted(dirContents(filzaDir)[1])

            filzaFiles = []
            prevSeq = None
            prevPage = None

            for cent in cents:
                centDir = f"{filzaDir}/{cent}"
                files = sorted(dirContents(centDir)[0])
                self.console(f"\t\t{cent} {len(files):>4} files")

                for file in files:
                    if file == DS_STORE:
                        continue

                    filzaFiles.append((cent, file))

            for item in filzaFiles:
                (cent, file) = item

                fullFile = f"{filza}/{cent}/{file}"

                if extNm(file) != scanExt:
                    error("wrong extension", file)
                    continue

                base = stripExt(file)
                parts = base.split("_")

                if len(parts) != 3:
                    error("Wrong number of parts", base)
                    continue

                (fl, seq, pageStr) = parts

                if fl != filza:
                    error("Filza mismatch", fullFile)
                    continue

                if pageStr[0] != cent:
                    error("Cent mismatch", f"{cent} => {fullFile}")
                    continue

                good = True

                if prevSeq is not None and prevSeq != seq:
                    error("Out of sequence", base)
                    good = False

                seq = prevSeq

                page = Page.parse(pageStr, kind="orig")
                rotations[f"{filza}_{page}"] = rotateInfo.get(filza, {}).get(page, 0)

                if page is None:
                    error("Wrong page format", f"{base} :: {pageStr}")
                    good = False
                else:
                    if skipping:
                        if page.num == startAt:
                            skipping = False
                        else:
                            nSkipped += 1
                            continue

                    if page in filzaMissing:
                        error("Found page that should be missing", base)

                    if (
                        prevPage is not None
                        and not page.isSubsequent(prevPage)
                        and not any(page.isSubsequent(exc) for exc in filzaMissing)
                    ):
                        error(
                            "Page number out of order",
                            f"{base}: {prevPage} =/=> {page}",
                        )
                        good = False

                    prevPage = page

                if not good:
                    continue

                toCopy.append((fullFile, f"{filza}_{page}.{scanExt}"))

        rotationFileScan = f"{SCANDIR}/rotation_{PAGES}.tsv"
        rotationFileThumb = f"{THUMBDIR}/rotation_{PAGES}.tsv"

        with open(rotationFileScan, "w") as sh, open(rotationFileThumb, "w") as th:
            head = "page\trotation\n"
            sh.write(head)
            th.write(head)

            for page in sorted(rotations):
                rot = rotations[page]
                row = f"{page}\t{rot}\n"
                sh.write(row)
                th.write(row)

        with open(SCANERRORS_TXT, "w") as rh:
            for msg, items in sorted(errors.items()):
                nFiles = len(items)
                examples = ", ".join(items[0:3])
                msgRep = f"{nFiles:>4} x {msg}"
                self.console(f"\t\t{msgRep}: {examples}")

                rh.write(f"{msg}\n")

                for item in items:
                    rh.write(f"\t{item}\n")

        nErrors = sum(len(x) for x in errors.values())
        msg = f"there were {nErrors} errors, see {SCANERRORS_TXT}"
        sep = "\t" if silent else ""
        console(f"{sep}\t{msg}\n", error=nErrors != 0)

        if nSkipped is not None:
            self.console(f"\tSkipped the first {nSkipped} files")

        label = "Dry-run" if dry else "Copying"
        self.console(f"\t{label} {len(toCopy)} files from {SIMAGEDIR} to {PAGEDIR}")

        if not dry:
            initTree(PAGEDIR, fresh=True)

            for src, dst in toCopy:
                fileCopy(f"{SIMAGEDIR}/{src}", f"{PAGEDIR}/{dst}")

    def ingestLogo(self, dry=False):
        if self.error:
            return

        if True or not dry:
            dirRemove(LOGODIR)
            dirCopy(LOGOINDIR, LOGODIR)

    def ingestCovers(self, dry=False):
        if self.error:
            return

        if not dry:
            dirRemove(COVERDIR)
            dirCopy(COVERINDIR, COVERDIR)

    def process(self):
        if self.error:
            return

        force = self.force

        plabel = "originals"
        dlabel = "thumbnails"

        # prod data

        for kind in (COVERS, PAGES):
            destDir = f"{SCANDIR}/{kind}"
            sizesFile = f"{SCANDIR}/sizes_{kind}.tsv"

            if force or not fileExists(sizesFile):
                self.doSizes(destDir, SCAN_EXT[0], sizesFile, plabel, kind)
            else:
                self.console(f"Already present: sizes file {plabel} ({kind})")

        # dev data

        for kind in (COVERS, PAGES):
            sizesFile = f"{THUMBDIR}/sizes_{kind}.tsv"
            srcDir = f"{SCANDIR}/{kind}"
            destDir = f"{THUMBDIR}/{kind}"

            if force or not dirExists(destDir):
                self.doThumb(srcDir, destDir, *SCAN_EXT, plabel, dlabel, kind)
            else:
                self.console(f"Already present: {dlabel} ({kind})")

            if force or not fileExists(sizesFile):
                self.doSizes(destDir, SCAN_EXT[1], sizesFile, dlabel, kind)
            else:
                self.console(f"Already present: sizes file {dlabel} ({kind})")

    def doSizes(self, imDir, ext, sizesFile, label, kind):
        if self.error:
            return

        fileRemove(sizesFile)

        fileNames = dirContents(imDir)[0]
        items = []

        for fileName in sorted(fileNames):
            if fileName == DS_STORE:
                continue

            thisExt = extNm(fileName)

            if thisExt != ext:
                continue

            base = fileName.removesuffix(f".{thisExt}")
            items.append((base, f"{imDir}/{fileName}"))

        console(f"\tGet sizes of {len(items)} {label} ({kind})")
        j = 0
        nItems = len(items)

        sizes = []

        for i, (base, fromFile) in enumerate(sorted(items)):
            if j == 1000:
                perc = int(round(i * 100 / nItems))
                self.console(f"\t\t{perc:>3}% done")
                j = 0

            status = run(
                [SIZES_COMMAND] + SIZES_OPTIONS + [fromFile], capture_output=True
            )
            j += 1

            if status.returncode != 0:
                console(status.stderr.decode("utf-8"), error=True)
            else:
                (w, h) = status.stdout.decode("utf-8").strip().split()
                sizes.append((base, w, h))

        perc = 100
        self.console(f"\t\t{perc:>3}% done")

        with open(sizesFile, "w") as fh:
            fh.write("file\twidth\theight\n")

            for file, w, h in sizes:
                fh.write(f"{file}\t{w}\t{h}\n")

    def doThumb(self, fromDir, toDir, extIn, extOut, plabel, dlabel, kind):
        if self.error:
            return

        rotateInfo = self.rotateInfo

        initTree(toDir, fresh=True)

        fileNames = dirContents(fromDir)[0]
        items = []

        for fileName in sorted(fileNames):
            if fileName == DS_STORE:
                continue

            thisExt = extNm(fileName)
            base = fileName.removesuffix(f".{thisExt}")
            (filza, page) = base.split("_", 1)

            if thisExt != extIn:
                continue

            items.append(
                (base, filza, page, f"{fromDir}/{fileName}", f"{toDir}/{base}.{extOut}")
            )

        console(f"\tConvert {len(items)} {plabel} to {dlabel} ({kind})")

        j = 0
        nItems = len(items)

        for i, (base, filza, page, fromFile, toFile) in enumerate(sorted(items)):
            if j == 1000:
                perc = int(round(i * 100 / nItems))
                self.console(f"\t\t{perc:>3}% done")
                j = 0

            if kind == PAGES:
                rotations = rotateInfo.get(filza, {})
                rot = rotations.get(page, 0)
            else:
                rot = 0

            if rot == 0:
                rotOptions = []
            else:
                rotOptions = ["-rotate", f"{rot}"]
                self.console(f"\t\t\t{filza}/{page} rotate {rot:>3}")

            run([SCAN_COMMAND] + [fromFile] + SCAN_OPTIONS + rotOptions + [toFile])
            j += 1

        perc = 100
        self.console(f"\t\t{perc:>3}% done")
