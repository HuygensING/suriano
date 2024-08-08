from tf.core.helpers import console
from tf.core.timestamp import DEEP, TERSE
from tf.app import use

from processdocs import normalizeChars


class MakeNER:
    def __init__(self, make, silent=False):
        self.make = make
        self.silent = silent
        self.error = False

        self.load()

    def load(self, withEntities=False):
        silent = self.silent
        make = self.make

        backend = make.backend
        org = make.org
        repo = make.repo
        version = None if withEntities else make.version
        msg = "with entities" if withEntities else ""

        console(f"\tLoading TF {msg} ...")

        loadVerbose = DEEP if silent else TERSE

        self.app = use(
            f"{org}/{repo}:clone",
            backend=backend,
            checkout="clone",
            version=version,
            silent=loadVerbose,
        )
        make.app = self.app

    def task(self, sheet):
        silent = self.silent
        A = self.app
        NE = A.makeNer(normalizeChars=normalizeChars, silent=silent)
        NE.setSheet(sheet)
        NE.reportHits()
        NE.bakeEntities()
        self.load(withEntities=True)
