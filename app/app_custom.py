# DEF import
from tf.advanced.find import loadModule
# END DEF

# DEF init
        app.image = loadModule("image", *args)
        app.image.getImagery(app, app.silent, checkout=kwargs.get("checkout", ""))
        app.reinit()
# END DEF

# DEF extra
    # GRAPHICS Support

    def getGraphics(app, isPretty, n, nType, outer):
        result = ""

        theGraphics = app.image.getImage(
            app,
            n,
            _asString=True,
            warning=False,
        )
        if theGraphics:
            result = f"<div>{theGraphics}</div>" if isPretty else f" {theGraphics}"

        return result

    def imagery(app):
        return set(app._imagery)
# END DEF
