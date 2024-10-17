# Suriano - Letters (Everything but the scans)

Here is the data set that represents the letters of Christofforo Suriano.

The data we describe here is not in this repo but resides in the publicly accessible 
[SurfDrive folder](https://surfdrive.surf.nl/files/index.php/s/L1bhixOQKMdXPjT).

The dataset consists of source material and representations of the source in
TEI and other formats, and metadata and XML schemas.

# Overview of the contents

## `entities`

Contains the metadata of all entities in json format, in a single file
`entitymeta.json`.

## `logo`

Contains the logo of the provider of the scans, the Archive of the State of Venice.

## `metadata`

Contains various kinds of metadata in various representations:

### named entities

The Excel file `persons.xslx` contains the source of the named entity
annotations: full names plus biographical properties, plus triggers by which
these names can be found in the text.

### letter properties

The Excel file `summaries.xlsx` contains dates, senders and recipients and
their locations of the letters, plus the shelfmarks, editor notes and resources.
Moreover, English summaries of the letters are provided here.

## `schema`

The XML schemas for this resource:

*   `suriano.xsd`, the top-level schema, in XMLSchema format;
*   `suriano.rng`, the top-level schema, in RelaxNG format;
*   `dcr.xsd`, schema to add data categories to the top-level schema (`datcat`
    attributes;
*   `xml.xsd`, schema for the XML formalism itself;

The top-level schema is based on the TEI schema, which is invoked via a
[copy inside Text-Fabric](https://github.com/annotation/text-fabric/tree/master/tf/tools/tei). 

## `tei`

TEI files per letter, organized in folders by filza.
This is the TEI where most of the source information comes together: 

*   the transcriptions in Word, including their page headers;
*   the metadata and summaries;
*   *but not the named entities!*.

## `transcriptions`

Source material and the results of the first conversion step plus some reports.
Plus  translation table.

*   `translation.txt`: table of italian phrases encountered in editorial remarks in
    the text (e.g. *Bianca* = *Blank page*) and in the foornotes.

### `docx`

The transcriptions, for each filza a single file, with the filza number in the name:

*   `01.docx`, `02.docx`, ... , `12.docx`

### `teiSimple`

The direct conversions of the `docx` files by Pandoc into simple `tei`.
No special logic or configuration has been applied in this conversion.
Note that Pandoc loses all page headings during conversion, so we have extracted
the page headings by other means, using the Python library 
[doxc2python](https://pypi.org/project/docx2python/).

