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

### `images`

Here are all the scans, in subdirectories according to the filzas (folders).
Each filza directory is in turn divided in directories of 100 full pages (all pages
whose number start with the same hundredth, i.e. 100 recto-verso pairs).

There is a separate directory `covers` that contains all the cover pages of the
filzas. These pages do not have textual content, and do not belong to letters.

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

## Content organization

The physical letters in the archive are bound into folders (*filze*, plural of *filza*).

The corpus consists of filze 02, 03, 04, 05, 06, 07, 08, 09, 09b, 10, 11, 12, and
contains ca. 9150 scans.

The transcriptions cover the vast majority of these scans, the exceptions being:

* the initial pages of filza 02 are not transcribed, the transcriptions start
  at page 71;
* the entire filza 9b (marked as 9-bis) is not transcribed.

The cover pages of the filze are taken together in the subdirectory `covers`.

Every filza corresponds with a subdirectory of the same name, and they contain the
proper recto and verso pages.

Inside every filza directory you find the pages divided in subfolders by the hundred:
folders 0, 1, 2, 3, etc. containing the pages 1-99, 100-199, 200-299, 300-399, etc.

Every page corresponds to one `.jpg` file, with the file name built up as

```
ff_ssss_ppp-rv.jpg
```

where

*   `ff` is the *filza*
*   `ssss` is the sequence number of the page in the filza
*   `ppp` is the page number within the filza; it is a number, and sometimes there is 
    `bis` or `ter` appended
*   `rv` is either `r` (recto) or `v` (verso)

The resolution of the pages is moderate and variable: 300 x 300 and 400 x 400,
the file sizes are rpughly between 500KB and 3MB.

The orientation of the pages is portrait, and you see all recto pages on the right side
of the binding and all verso pages on the left side of the binding.

However, the written material is often in different orientations.

We provide a file `rotate.yaml` that specifies the best orientation for reading for
each page that needs to be rotated for that. The amount of rotation is specified in 
degrees (0-360) in the clockwise direction.

IIIF applications that want to display these pages can use this information to present
a readable view to end users.

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

Somewherein filza 9 something like that happened too: hundreds of pages had a page
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

## How to use this set of scans

The division of files in folders of 100 pages might seem arbitrary, but it is actually
helpful if you need to transport the pages in smaller chunks. Some cloud services, such
as Dropbox, Surfdrive and others fail in mysterious ways if you ask them to handle
a lot of files, or they do not resume an upload of download after a glitch in the
network connection.

However, if you use this dataset in an application, it is recommended to let the
files land in one single directory, or possibly in directories per filza.
There will be no clashes, since every file has a unique name within the dataset.

Except for the pages in `covers`, you can also leave out the sequence numbers, which
may or may not be handy. There will be no clashes, and the ordering will be the same.

This hinges on two things:

*   we have checked that the page numbers do increase: there are no two pages with
    a different sequence number while the combination of their page number and`rv` 
    specifier are identical;
*   in the case of `bis` and `ter` pages: in the natural sort order `bis` comes
    before `ter`, and the page without these suffixes comes before the two;
*   in the natural sort order `r` comes before `v`.

In our pipeline to produce the Suriano corpus on the web, we have done exactly this:
we made a flat directory of all scans, with simplified file names.
