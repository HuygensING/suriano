[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/HuygensING/suriano/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/HuygensING/suriano)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13950093.svg)](https://doi.org/10.5281/zenodo.13950093)

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

# Access the corpus

This repo also contains a [text-fabric](https://github.com/annotation/text-fabric)
copy of the corpus (in fact, that copy has been instrumental to build the data for the
website).

This copy contains the transcriptions and thumbnails of the scans.

Here are the express instructions to get going:

1.  install Python
1.  `pip install 'text-fabric[all]'`
1.  `tf HuygensING/suriano`

This will first download the data, and note that the thumbnails occupy 300 MB of space,
so this may take a while.
After that a browser window opens with an interface on the Suriano correspondence.
You can read the text, and if you click on a camera icons (📷) you see the scan
of the corresponding page.

You can also run your own programs on the corpus, through the Text-Fabric API.
Here is a
[tutorial to get started](https://nbviewer.org/github/HuygensING/suriano/blob/main/tutorial/start.ipynb).

# Authors and contributors

The following people all played a role in the construction of this dataset.

*Research at [Huygens](https://www.huygens.knaw.nl/en/projecten/)*

*   **[Nina Lamal](https://www.huygens.knaw.nl/en/medewerkers/nina-lamal-2/)**
    Researcher, deeply familiar with all ins and outs of the corpus;
*   **[Helmer Helmers](https://nl-lab.net/en/about-nl-lab/how-are-nl-lab/helmer-helmers/)**
    researcher and leader of the Suriano project.

*Funder*

*   **[Menno Witteveen](https://nl.linkedin.com/in/menno-witteveen-b4887315)**
    Entrepreneur and historian.

*Transcribers*

*   Alexa Bianchini
*   Ruben Celani
*   Michele Correra
*   Flavia di Giampaolo
*   Federica D’Uonno
*   Vera Frantellizzi
*   Cristina Lezzi
*   Giorgia Priotti
*   Angelo Restaino
*   Filippo Sedda

*Development by [TeamText](https://di.huc.knaw.nl/text-analysis-en.html)*

*   **[Dirk Roorda](https://github.com/dirkroorda)**
    Developer, wrote the conversion code and new functions for
    Text-Fabric for Named Entity Recognition;
*   **[Sebastiaan van Daalen](https://www.huygens.knaw.nl/en/medewerkers/sebastiaan-van-daalen-2/)**
    Front-end developer of TextAnnoViz (the main framework of the website)
    *and* having exquisite knowledge of historical manuscript editions;
*   **[Bram Buitendijk](https://github.com/brambg)**
    Back-end developer on the annotation infrastructure
    ([un-t-ann-gle](https://github.com/knaw-huc/un-t-ann-gle) and AnnoRepo);
*   **[Hayco de Jong](https://github.com/hayco)**
    Back-end developer on the search infrastructure (TextRepo, Broccoli and Brinta);
*   **[Bas Leenknegt](https://nl.linkedin.com/in/basleenknegt)**
    Allround developer on back-end and front-end matters (TAV, TextRepo);
*   **[Hennie Brugman](https://www.researchgate.net/profile/Hennie-Brugman)**
    team leader, connecting the dots with time and budget and people.

# Construction of the dataset

Here we describe how we have constructed the Suriano dataset (and how you can replicate
it).

We proceed as follows:

1.  there are incoming page scans, they are renamed and checked for completeness;
1.  there are incoming transcriptions in Word, they are converted to TEI, and
    in the process the page sequences in the transcriptions are compared with
    the pages in the scans;
1.  the TEI is converted to [Text-Fabric](https://github.com/annotation/text-fabric);
1.  using Text-Fabric and a spreadsheet of named entity triggers, we mark thousands
    of named entities in the text;
1.  by means of Text-Fabric we generate a WATM export: a set of text fragments
    and annotations;
1.  by means of Text-Fabric we generate IIIF manifests for the page scans;
1.  the WATM output is exported to the TeamText virtual machine;
1.  the manifests and other static files are exported to a persistent volume on
    our k8s network.

This is where the control of this repo stops. The infrastructure of TeamText takes
over from here:

1.  the WATM is imported in TextRepo and AnnoRepo: essentially it is a stream of
    tokens and a set of web annotations;
1.  additional configuration to steer the final display and the search indexes
    is added to Broccoli and Brinta;
1.  finally, TextAnnoViz displays the letters on the website, fed by the contents of
    AnnoRepo, TextRepo, Brinta and Broccoli.

There is a large degree of isomorphism between the Text-Fabric data and the final 
website data.

Researchers can use Text-Fabric to download the letters to their computer and browse
and search them in a local browser.
Or they can access them by means of Python programs and Jupyter notebooks.

We'll provide a tutorials for that, see below.

# Curated data

The source data and the TEI that we derived from it, and more, is available on
[SurfDrive (public readonly link)](https://surfdrive.surf.nl/files/index.php/s/L1bhixOQKMdXPjT).
This does not include the original high resolution scans, since they are not
available as a downloadable package. These scans are also at SurfDrive, but not
accessible via a public link. If you are interested in these scans, contact Nina Lamal.

Note that (very) low resolution versions of these scans are provided in this repo:
[thumb](thumb).

Many aspects of the curation process have been carried out by programs, in a rule-based
way. These processes have produced a number of report files.

There are extensive README files in the report directory.

*   [README_DATASOURCE](report/README_DATASOURCE.md): description of the contents of
    the
    [datasource directory on SurfDrive](https://surfdrive.surf.nl/files/index.php/s/L1bhixOQKMdXPjT);
*   [README_SCANS](report/README_SCANS.md): description of the contents of the
    scan directory on SurfDrive;
*   [README](report/README.md): description of the report files.

# How to carry out the conversion

See the [README.md](programs/README.md) in the programs directory.
