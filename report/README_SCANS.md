# Suriano - Letters (Scans)

Here is the data set of the original, high resolution scans of the letters of
Christofforo Suriano.

The data we describe here is not in this repo but resides in a SurfDrive folder that is
not publicly accessible. Ask Nina Lamal for permission to access these scans.

Note that these scans are being served by the final website; only the collective
downloading of them all is prohibited.

# Overview of the contents

## `scans`

Contains the scans and additional information in the following subfolders:

### `config`

*   `exclusions.yaml`: some scans are not referred to by the transcriptions; this
    file sums up which scans should be excluded from checks and reports.
*   `missing.yaml`: a few scans that you would expect are not present. Here they are
    listed. These scans are also not used by transcriptions.
*   `rotate.yaml`: the scans are all oriented in portrait, recto pages with
    margin right, verso pages with margin left. However, this is not the optimal
    orientation for reading in quite a few cases. This file specifies the rotation
    that needs to be applied for optimal reading.

### `covers`

These are scans of the covers of the filzas, which are physical carton folders
containing the letters. These covers are not transcribed, since they do not contain
original text.

### `logo`

The logo of the archive in Venice that holds the physical filzas and their content.

### `pages`

The scans of all transcribed pages, ca. 9150 in total. The file names start
with the filza number,
`02`, `03`, `04`, `05`, `06`, `07`, `08`, `09`, `09b`, `10`, `11`, `12`, followed
bij the letter number, possibly followed by `bis` or `ter`, followed by `r` or `v`
(recto/verso), followed by `.jpg`.

Remarks:

*   the initial pages of filza 02 are not transcribed, the transcriptions start
    at page 71;
*   The resolution of the pages is moderate and variable: 300 x 300 and 400 x 400,
    the file sizes are roughly between 500KB and 3MB.
*   The orientation of the pages is portrait, and you see all recto pages on
    the right side of the binding and all verso pages on the left side of the binding.
*   However, the written material is often in different orientations.
*   We provide a file `rotate.yaml` that specifies the best orientation for reading for
    each page that needs to be rotated for that. The amount of rotation is specified in 
    degrees (0-360) in the clockwise direction.
    IIIF applications that want to display these pages can use this information
    to present a readable view to end users.

# Provenance of the scans

The scans have been provided in 2020 by
[L'Archivio di Stato di Venezia (Archive of the State of Venice)](https://www.archiviodistatovenezia.it/it).
to the
[KNAW/Huygens Institute](https://www.huygens.knaw.nl/en/)
in the course of the
[Suriano project](https://www.huygens.knaw.nl/en/projecten/correspondence-of-christofforo-suriano/).

## Context

The scans have been transcribed into Word documents by an Italian team, and on these
Word documents a searchable web-version is based.
This website,
[edition.suriano.huygens.knaw.nl](https://edition.suriano.huygens.knaw.nl)
has been developed by
[KNAW/HuC/Team Text](https://di.huc.knaw.nl/text-analysis-en.html).

A reasearchers interface via Text-Fabric is available, see
[Text-Fabric/suriano](https://annotation.github.io/text-fabric/tf/about/corpora.html#knawhuygensing-and-gitlabhucknawnl).

A quite sophisticated pipeline has been built to convert the Word documents into TEI,
the TEI into Text-Fabric, the Text-Fabric into text streams and annotations, which
is the input for the web site.
In that pipeline a lot of consistency checks have been applied, and the data has been
enriched with named entity annotations.

## Curation

It appeared that the dataset of scans, in the form that it was given to us, had some
problems that needed to be addressed.

### Folder structure

The directories and files had names with a very long and mostly identical prefix:

```
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-
```

We have stripped this prefix everywhere.

Then, the toplevel directories somehow contained the pages of the filze, but it was
not completely clear how:

```
144-19_mancanti-busta-6/
Immagini filza 7/
Senato, Dispacci, Dispacci degli ambasciatori e residenti, Signori Stati-Filza-8/
Senato-Dispacci degli ambasciatori e residenti-Signori Stati-f-9/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-10/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-11/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-12/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-2/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-3_I-parte/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-3_II-parte/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-4/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-5/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-6/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-7/
Senato-dispacci-ambasciatori-e-residenti-Signori-Stati-filza-9-bis/
```

It appeared that the files in `144-19_mancanti-busta-6` were already present in the
normal filza-6 folder, with the same file sizes and mostly the same attributes.
So we could safely discard this directory.

The files in `Immagini filza 7/` consisted of roughly half of the pages in filza 7,
in a somewhat higher resolution than the ones in the normal filza-7 folder, and
with very different file names. We decided that it was not worth the hassle to merge
these files in, so we also discarded these.

Sometimes there were several copies of the same image in a filza folder, for example
26 ones in the filza-2 folder. They were identical in most metadata and file size,
but had different dates. We have discarded the copies.

We then made directories for the filzas, given by their number, with a leading zero
for the numbers less than 10. The folder for filza 9-bis is called `09b`.
In this way, the filzas can naturally be sorted by their folder name.

Inside the filzas, the file names start with the name of the filza. We replaced
this by the filza names according to our new convention.

### Checks

We ran a rigorous check to see whether the order of the pages was correct, without
gaps in them.

We found a few gaps and a few order problems.

#### Gaps

The gaps are listed in `missing.yaml`.

The pages with missing scans are:

*   filza 9, pages 120r and 120v;
*   filza 12, pages 278r and 278v.

There are no transcriptions for these pages.

#### Order problems

Somewhere in filza 11 there was a misnomer: the scan of page 299r has been named with
page 300v. That had to be renamed. But in a whole stretch after that, pages had got 
a file name that was slightly off. After a thorough inspection this has been remedied
by a one-time script.

Somewhere in filza 9 something like that happened too: hundreds of pages had a page
number in their file name that was one off. Again, after thorough inspection and with
a one-time script, this has been straightened out.

### Manual inspection for rotation

We have inspected all pages in the corpus, one by one, for rotation.
When a page did not have the expected orientation for a recto or verso page,
we have rotated it to the correct position.

Whenever the optimal reading orientation differs from the normal orientation for a page,
we have made an entry in the `rotate.yaml` file with a rotation to apply to obtain a
good reading experience.

This is a bit subjective, because often such pages contain pieces of writing in
different  orientations. We have adapted the rotation to the most salient piece of
writing on the page. Often that was the biggest piece of the page, but in other cases
the most conspicuous writing was just a formula, with some smaller, more content-rich
writing in an other direction. Then we went for that smaller piece.
