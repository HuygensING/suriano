[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

![ok](docs/images/logo.png)
![huc](docs/images/huc.png)
![tf](docs/images/tf-small.png)

# The correspondence of Christofforo Suriano

From [suriano.huygens.knaw.nl](https://suriano.huygens.knaw.nl):

> Christofforo Suriano was the first Venetian envoy to the Dutch Republic. His
arrival in The Hague marks the beginning of official Dutch-Venetian diplomatic
relations. This digital edition presents all 725 letters sent by Suriano to the
Venetian Senate between 1616 and 1623, totaling approximately 7,000 pages. His
correspondence is of great importance for Dutch, Venetian, and European history
in the first phase of the Thirty Years’ War.

For more info, see the
[Suriano project](https://www.huygens.knaw.nl/en/projecten/correspondence-of-christofforo-suriano/).


In this repo we prepare the data for the website of the correspondence of
Christofforo Suriano:

*   the entrance of that website is
    [suriano.huygens.knaw.nl](https://suriano.huygens.knaw.nl), this contains
    materials not covered in this repo;
*   the correspondence itself is served by
    [edition.suriano.huygens.knaw.nl](https://edition.suriano.huygens.knaw.nl).

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

We'll provide a tutorials for that, see below.

# Curated data

The source data and the TEI that we derived from it and more is available on
[SurfDrive (public readonly link)](https://surfdrive.surf.nl/files/index.php/s/L1bhixOQKMdXPjT).

There is an extensive
[README](https://surfdrive.surf.nl/files/index.php/s/L1bhixOQKMdXPjT#editor)
that describes the contents of that data.

# How to operate this repo (and the tutorial)

See the [README.md](programs/README.md) in the programs directory.

There you see how to clone this repository. After that, you can follow a tutorial
here: 
[start.ipynb](https://gitlab.huc.knaw.nl/suriano/letters/-/blob/main/tutorial/start.ipynb)

Note that the online version of the tutorial is not rendered optimally, it is
recommended use the clone of the repo on your computer to work through the tutorial.

