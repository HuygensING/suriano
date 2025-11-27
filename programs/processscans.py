from subprocess import run
from tf.core.helpers import console
from tf.core.files import (
    dirContents,
    dirExists,
    initTree,
    fileExists,
    extNm,
    fileRemove,
)
from processhelpers import (
    COVERS,
    PAGES,
    SCANDIR,
    THUMBDIR,
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
