import sys
from subprocess import run

from tf.app import use
from tf.core.timestamp import DEEP, TERSE
from tf.core.files import fileCopy
from tf.convert.iiif import IIIF
from tf.convert.makewatm import MakeWATM

from processhelpers import (
    nerMeta,
    NER_NAME,
    NERIN_FILE,
    NEROUT_FILE,
    SOURCEBASE,
    PAGESEQ_JSON,
)
from processdocs import TeiFromDocx
from processscans import Scans
from makener import MakeNER


class Make(MakeWATM):
    def __init__(self, fileLoc):
        super().__init__(fileLoc, sourceBase=SOURCEBASE)

    def doTask_docx2tei(self):
        silent = self.flag_silent

        TFD = TeiFromDocx(silent=silent)
        TFD.task("all")

        if TFD.error:
            self.good = False

    def doTask_ner(self):
        silent = self.flag_silent
        fileCopy(NERIN_FILE, NEROUT_FILE)
        NER = MakeNER(self, silent=silent)
        NER.task(NER_NAME)
        nerMeta(*NER.getMeta(), silent=silent)

        if NER.error:
            self.good = False

    def doTask_ingest(self):
        silent = self.flag_silent
        force = self.flag_force

        SC = Scans(silent=silent, force=force)
        SC.ingest()

    def doTask_scans(self):
        silent = self.flag_silent
        force = self.flag_force

        SC = Scans(silent=silent, force=force)
        SC.process()

    def doTask_iiif(self):
        silent = self.flag_silent
        prod = self.flag_prod

        if hasattr(self, "app"):
            app = self.app
        else:
            backend = self.backend
            org = self.org
            repo = self.repo
            loadVerbose = DEEP if silent else TERSE
            app = use(
                f"{org}/{repo}:clone",
                backend=backend,
                checkout="clone",
                silent=loadVerbose,
            )

        II = IIIF("", app, PAGESEQ_JSON, prod=prod, silent=silent)
        II.manifests()

    def doTask_deploy(self):
        prod = self.flag_prod
        mode = "prod" if prod else "dev"

        run(f"./provision.sh {mode} all", shell=True)


if __name__ == "__main__":
    Mk = Make(__file__)
    Mk.setOptions(
        taskSpecs=(
            ("ingest", "Ingest scans"),
            ("scans", "Process scans"),
            ("docx2tei", "DOCX ==> TEI files"),
            ("tei2tf", None),
            ("ner", "Annotate named entities"),
            ("watm", None),
            ("iiif", "Generate IIIF manifests"),
            ("deploy", "Deploy to k8s"),
        )
    )
    sys.exit(Mk.main())
