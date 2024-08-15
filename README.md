[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)

![ok](docs/images/logo.png)
![huc](docs/images/huc.png)
![tf](docs/images/tf-small.png)

# The correspondence of Christofforo Suriano

In this repo we develop a website for the correspondence of Christofforo Suriano.

We proceed as follows:

1.  There are incoming page scans, they are renamed and checked for completeness
1.  There are incoming transcriptions in Word, they are converted to TEI, and
    in the process the page sequneces in the transcriptions are compared with
    the pages in the scans
1.  The TEI is converted to Text-Fabric
1.  Using Text-Fabric and a spreadsheet of named entity triggers, we mark thousands
    of named entities in the text
1.  By means of Text-Fabric we generate a WATM export: a set of text fragments
    and annotations
1.  By means of Text-Fabric we generate IIIF manifest for the page scans
1.  The WATM output is exported to the Team Text virtual machine
1.  The manifests and other static files are exported to a persistent volume on
    our k8s network

This is where the control of this repo stops. The infrastructure of TeamText takes
over from here:

1.  The WATM is imported in TextRepo and AnnoRepo: essentially it is a stream of
    tokens and a set of web annotations
1.  Additional configuration to steer the final display and the search indexes
    is added to Broccoli and Brinta
1.  Finally, TextAnnoViz displays the letters on the website, fed by the contents of
    AnnoRepo, TextRepo, Brinta and Broccoli.

There is a large degree of isomorphism between the Text-Fabric data and the final 
website data.

Researchers can use Text-Fabric to download the letters to their computer and browse
and search them in a local browser.
Or they can access them by means of Python programs and Jupyter notebooks.

We'll provide a set of tutorials for that.

# Curated data

The source data and the TEI that we derived from it and more is available on
[SurfDrive (public readonly link)](https://surfdrive.surf.nl/files/index.php/s/L1bhixOQKMdXPjT).

There is an extensive
[README](https://surfdrive.surf.nl/files/index.php/s/L1bhixOQKMdXPjT#editor)
that describes the contents of that data.

# How to operate this repo

Clone this repo so that it sits in exactly this directory:

```
~/gitlab.huc.knaw.nl/suriano/letters
```

(`~` is the home directory on your system)

Retrieve the contents of the Surfdrive directory above, so that it sits in exactly
this directory:

```
~/gitlab.huc.knaw.nl/suriano/letters/datasource
```

Start JupyterLab and navigate to the notebook

```
~/gitlab.huc.knaw.nl/suriano/letters/programs/convertPlain.ipynb
```

This notebook controls the complete workflow from ingest of the scans through the
execution steps of the conversion and ending with the export of the results
to the right locations.

You need to create a file `env` in this `programs` directory, which will not be
version controlled, and not pushed to gitlab, with contents as in
code.huc.knaw.nl.

The notebook has three parts:

1. The whole process in a single cell, with standard settings. 
   *N.B.:* This will mill through all the 9000 scans, generates thumbnails from them
   and recomputes their sizes. Not recommended.
2. The whole process divided into 5-10 main steps. Here you can skip the ingest of the
   scans. Every step is a command line instruction, so there no debugging possibilities.
3. The whole process straight from Python, where the intermediate data remains stored
   in memory. Recommended for fine control and debugging.

# About

[Project](https://www.huygens.knaw.nl/en/projecten/correspondence-of-christofforo-suriano/)

[Ph.D. thesis Pieter Geyl, 1913](https://archive.org/details/christofforosuri00geyl/page/n3/mode/2up)

