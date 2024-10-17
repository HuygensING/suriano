# How to work with this repository

The Suriano pipeline is built with programs in this directory, where some steps
rely heavily of functions of [Text-Fabric](https://github.com/annotation/text-fabric).

## Preparation

### Install image processing software

Only if you need to reprocess the scans.

Install [Imagemagick](https://imagemagick.org).

### Install Pandoc

[Pandoc](https://pandoc.org)
is software that can convert Word files to simple TEI.

### Install Python and packages

Python can be installed from [python.org](www.python.org).

Then install the following packages:

```
pip install 'text-fabric[all]'
```

Additionally, install modules to read/write Office files:

```
pip install doc2python openpyxl
```

### VPN

Make sure you use the KNAW-HuC VPN.

Its is needed to fetch environment files from a repository behind the firewall,
and to deliver result files to locations behind the firewall.

### Clone suriano/letters

Create a parent directory inside your home directory exactly as follows:

```
cd ~
mkdir -p gitlab.huc.knaw.nl/suriano
cd gitlab.huc.knaw.nl/suriano
```

Now clone this repo:

```
git clone https://gitlab.huc.knaw.nl/suriano/letters.git
```

### Add files to your local clone

The data we are going to add will not be pushed to the remote, because it is
in a directory listed in the `.gitignore`.

#### Suriano data

##### The high resolution scans

Make a new directory in the repo:

```
cd letters
mkdir curatedscans
```

Retrieve the contents of the Surfdrive directory Suriano-Sources-Scans
so that it sits in exactly the above created directory `curatedscans`.

This is not a public directory on SurfDrive, you can get access by asking Nina Lamal
or Dirk Roorda to share it with you.

##### The texts, metadata and reports

Make a new directory in the repo:

```
cd letters
mkdir datasource
```

Retrieve the contents of this
[Surfdrive directory](https://surfdrive.surf.nl/files/index.php/s/L1bhixOQKMdXPjT),
so that it sits in exactly the above created directory `datasource`.

#### Environment

Retrieve the file
[env](https://code.huc.knaw.nl/tt/suriano/-/raw/main/env?ref_type=heads&inline=false)
from code.huc.knaw.nl and put it in

```
~/gitlab.huc.knaw.nl/suriano/letters/programs
```

## Operation

Start JupyterLab and navigate to the notebook

```
gitlab.huc.knaw.nl => suriano => letters => programs => convertPlain.ipynb
```

This notebook controls the complete [workflow](#workflow-overview) from ingest of the
scans through the execution steps of the conversion and ending with the export
of the results to the right locations.

The notebook has three parts:

1. The whole process straight from Python, where the intermediate data remains stored
   in memory. Recommended for fine control and debugging.
   Here you can also further tweak the Named Entity Recognition process by
   looking for spelling variants.
1. The whole process divided into 5-10 main steps. Here you can skip the ingest of the
   scans. Every step is a command line instruction, so there are no debugging
   possibilities.
1. The whole process in a single cell, with standard settings. 
   *N.B.:* This will mill through all the 9000 scans, generate thumbnails from them
   and recompute their sizes. Not recommended.

## Workflow overview

The toplevel steps of the workflow can be gleaned from
[make.py](programs/make.py).

### WF 1: Ingest scans

The scans are ingested from inside the `datasource` directory into locations
inside the `scans` directory (not synchronised in git). The resulting
directories that hold the images are flat, and the images have simple,
non-redundant names.

### WF 2: Process scans

The scans will be inspected for their sizes, and a low resolution version of the
scans will be generated (thumbnails: in the [thumb](thumb) directory).

The [thumb](thumb) directory is only used for Text-Fabric usage, and not for
the pipeline towards TextAnnoViz. Users of `suriano/letters` through
Text-Fabric will auto-download the `thumb` directory, so that they can inspect
the page scans offline in low resolution.

### WF 3: DOCX => TEI files

We convert the Word files to simple TEI files by means of Pandoc.
Each of he Word files contains the transcriptions of a complete filza, and the resulting
simple TEI file also contains the material of a complete filza.

However, not all data in the Word file is transferred to TEI: the page headers are
missing. We use a separate substep to retrieve the headers by means of `docx2python`.

We then continue by applying specific conversion logic to the simple TEI files,
steered by additional data from the page headings and from a spreadsheet with
metadata and summaries.

The result is a set of TEI files, according to the
[Suriano customization of the TEI schema](https://surfdrive.surf.nl/files/index.php/s/L1bhixOQKMdXPjT/download?path=%2Fschema&files=suriano.rng),
where each file contains a complete *letter*.

A letter consists of a main part, written by the author of the letter, and zero
or more appendices, which may or may not have been written by the author of the letter.

Each of these parts consist of a part that has been transmitted from sender to
recipient, and an optional part of material that the recipient has added to the letter,
often a short summary, or a brief note.

This step produces several files with information about the corpus that can be used
for diagnostic purposes. For an overview of the reporting see the
[readme](reports/README.md) in the reports directory.

### WF 4: TEI => TF

From the TEI data we generate Text-Fabric data (TF).
This is done by a function in Text-Fabric,
[tf.convert.tei](https://annotation.github.io/text-fabric/tf/convert/tei.html),
steered by settings in the file [tei.yaml](programs/tei.yaml) in the
[programs](programs) directory.

The convertor inspects the incoming TEI, validates it, and makes an inventory
of the elements and attributes, and the results of this end up in several report files
in [report/tei](report/tei).

Then it proceeds to create a TF dataset out of the TEI.

### WF 5: Annotate named entities

This step is driven by persons data in a spreadsheet in `datasource/metadata`.
It is copied to a location [ner](ner) within the reach of the Text-Fabric
dataset, and then Text-Fabric takes over, by means of
[tf.ner.ner](https://annotation.github.io/text-fabric/tf/ner/ner.html):
it reads and interprets the sheet, looks up its names and corresponding
triggers, marks the hits as entities, and bakes those entities into a new copy
of the TF dataset.

Additionally, the spelling variants of the triggers will be searched for in the corpus,
and they will be (selectively) merged with the original spreadsheet, thereby
increasing the number of hits with 20%.

All diagnostics can be inspected when you do these steps manually in the convertPlain
notebook. Alternatively, you can fire up the Text-Fabric browser as follows:

```
cd ~/gitlab.huc.knaw.nl/suriano/letters
tf --tool=ner
```

and then you can load the entities, see the diagnostics, inspect each entity, and look
up whatever you like in the corpus.

You can also inspect the corpus and all its markup by:

```
tf
```

(in the same directory).

From this interface you can navigate to the previous one by clicking
`Annotate` in the leftmost sidebar and then `named entities editor`.

From the NER interface you can get the generic interface by clicking on `back to
TF browser`.

### WF 6: Produce WATM

WATM stands for *Web Annotation Text Model*. It is a data model where text is a
sequence of tokens, and markup is a series of (web) annotations that target intervals
of those tokens. These annotations can also target other annotations.

The actual generation process is taken care of by Text-Fabric,
[tf.convert.watm](https://annotation.github.io/text-fabric/tf/convert/watm.html),
and the control of this process is also in Text-Fabric:
[tf.convert.makewatm](https://annotation.github.io/text-fabric/tf/convert/makewatm.html).

In fact, the whole conversion pipeline is implemented as a subclass of
[tf.cpnvert.makewatm.MakeWATM](https://annotation.github.io/text-fabric/tf/convert/makewatm.html#tf.convert.makewatm.MakeWATM).

The generation is steered by the file [watm.yaml](programs/watm.yaml).

The WATM generation is aware of the page scans: it will generate annotations that
provide urls for page images and canvases. For this it needs the configuration file
[iiif.yaml](programs/iiif.yaml).

### WF 7: Generate IIIF manifests

In order to present the page scans in the IIIF way, we need to generate manifests.
That happens in this step, and again, the code is in Text-Fabric:
[tf.convert.iiif](https://annotation.github.io/text-fabric/tf/convert/iiif.html).

This step makes also use of [iiif.yaml](programs/iiif.yaml).

### WF 8: Deploy to k8s

This step copies the end results of the conversion to the places where they are needed.

The WATM data goes to the TeamText VM.

The manifests go to a directory on a persistent volume on k8s, within reach of
an NGINX instance that serves them as static pages.
There is also other material that is brought to a neighbouring directory for being
statically served by this same NGINX instance. Think of the person metadata as set of 
HTML files (not actually used anymore by the current web serving set up, instead that
data is packaged in the WATM, from where it will be displayed in popups in the
TAV interface).

The page scans themselves go to yet another directory on the same persistent volume,
but this one is within reach of an instance of Cantaloupe, an IIIF image server.
From here the scans will be served, by links coming from the TAV interface.

# Overview of the program files

*   [convertPlain.ipynb](programs/convertPlain.ipynb):
    the workhorse and nerve centre of the complete workflow.
*   [covers.html](programs/covers.html):
    a static html file to show all the cover scans of the filzas.
*   [iiif.yaml](programs/iiif.yaml):
    configuration for manifest generation; also used by WATM generation.
*   [make.py](programs/make.py) 
    automatic run of the complete pipeline, all at once, or by main step.
*   [makener.py](programs/makener.py):
    automatic run of all steps needed for NER.
*   [meta.css](programs/meta.css):
    CSS for the persons metadata in static HTML files. (These files
    are no longer important, because the metadata is served from annotations in popups
    within the TAV interface).
*   [ner.ipynb](programs/ner.ipynb):
    Notebook to experiment with NER.
*   [nerScopes.ipynb](programs/nerScopes.ipynb):
    Notebook to experiment with scopes for NER detection.
*   [processdocs.py](programs/processdocs.py):
    Main program for document-oriented workflow steps.
*   [processhelpers.py](programs/processhelpers.py):
    Settings and shared code for `processdocs.py` and
    `processscans.py`.
*   [processscans.py](programs/processscans.py):
    Main program for image-oriented workflow steps.
*   [provision.sh](programs/provision.sh):
    Shell commands for the deploy steps: transferring results
    to the systems where they are needed.
*   [syncsurfdrive.sh](programs/syncsurfdrive.sh):
    Shell command to synchronize the `datasource` and `curatedscans` directories with
    SurfDrive.
*   [tei.yaml](programs/tei.yaml):
    configuration for the TEI to TF conversion.
*   [watm.yaml](programs/watm.yaml):
    configuration for the TF to WATM conversion.
