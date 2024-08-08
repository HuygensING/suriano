from tf.advanced.helpers import dh
from tf.advanced.repo import checkoutRepo
from tf.core.timestamp import AUTO, TERSE, VERBOSE
from tf.core.files import (
    dirContents,
    stripExt,
    extNm,
    fileExists,
    mTime,
    dirMake,
    fileCopy,
    splitPath,
)

LOCAL_IMAGE_DIR = "illustrations"


def imageCls(app, n):
    api = app.api
    F = api.F
    facs = F.facs.v(n)

    return None if "xxxx_" in facs else facs


def getImage(
    app,
    n,
    warning=True,
    _asString=False,
):
    facs = imageCls(app, n)

    if facs:
        imagery = app._imagery
        image = imagery.get(facs, None)

        if image is None:
            result = "<span>❌</span>" if warning else ""
        else:
            theImage = _useImage(app, image, n)
            result = f'<a href="{theImage}" target="{theImage} title="{facs}">📷</a>'
    else:
        result = "<span>❌</span>" if warning else ""

    if not warning:
        if not image:
            result = ""

    if result == "":
        return ""

    html = f"<div>{result}</div>".replace("\n", "")

    if _asString:
        return html

    dh(html)

    if not warning:
        return True


def _useImage(app, image, node):
    _browse = app._browse
    aContext = app.context

    (imageDir, imageName) = splitPath(image)
    ext = ".jpg"
    imagePath = f"{image}{ext}"
    localBase = aContext.localDir if _browse else app.curDir
    localDir = f"{localBase}/{LOCAL_IMAGE_DIR}"

    (filza, page) = imageName.split("_", 2)
    page = page.replace("-", "")

    if not fileExists(localDir):
        dirMake(localDir)

    localImageName = f"folio-{filza}-{page}{ext}"
    localImagePath = f"{localDir}/{localImageName}"

    if not fileExists(localImagePath) or mTime(imagePath) > mTime(localImagePath):
        fileCopy(imagePath, localImagePath)

    base = "/local/" if _browse else ""
    return f"{base}{LOCAL_IMAGE_DIR}/{localImageName}"


def getImagery(app, silent, checkout=""):
    aContext = app.context
    org = aContext.org
    repo = aContext.repo
    graphicsRelative = aContext.graphicsRelative

    (imageRelease, imageCommit, imageLocal, imageBase, imageDir) = checkoutRepo(
        app.backend,
        app._browse,
        org=org,
        repo=repo,
        folder=graphicsRelative,
        version="",
        checkout=checkout,
        withPaths=True,
        keep=True,
        silent=silent,
    )
    if not imageBase:
        app.api = None
        return

    app.imageDir = f"{imageBase}/{org}/{repo}/{graphicsRelative}/pages"

    images = {}
    app._imagery = images

    imageDir = app.imageDir

    fileNames = dirContents(imageDir)[0]

    for fileName in sorted(fileNames):
        ext = extNm(fileName)

        if ext != "jpg":
            continue

        fileName = stripExt(fileName)
        images[fileName] = f"{imageDir}/{fileName}"

    if silent in {VERBOSE, AUTO, TERSE}:
        dh(f"Found {len(images)} images<br>")
