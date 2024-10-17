# Suriano - Letters (Reports of the conversions/curation)

The scans and transcriptions of the Suriano dataset have been analyzed,
corrected and checked during the conversion from source to website.
Here is an overview of the reports generated during the process.

The reports are grouped as follows:

*   [scanreports](scans):
    result of scan processing;
*   [pages](pages):
    results of composing a catalog of pages out of the scans and the transcriptions;
*   [trans](trans):
    results of analysing the transcriptions;
*   [tei](tei):
    results of converting the TEI to TF.

## `scans`

*   [cfgerrors](scanreports/cfgerrors.txt):
    errors in the configuration files for the scans;
*   [scanerrors](scanreports/scanerrors.txt):
    a list of errors during the processing of the scans;  expect an empty file;
*   [thumberrors](scanreports/thumberrors.txt):
    a list of errors during the generation of thumbnails of the scans; expect
    an empty file;
*   [thumbpages](scanreports/thumbpages.txt):
    a list of the generated thumbnails.

## `pages`

*   [pageinfo](pages/pageinfo.txt):
    the component structure of the corpus in filzas, letters, texts and pages;
*   [pagescan](pages/pagescan.tsv):
    for each page, whether there is a scan and whether there is a
    transcription; if both are present, the status field is `OK`; expect `OK`
    in every row.
*   [pageseq](pages/pageseq.json):
    for each filza the exact sequence of pages in it, formatted as JSON;
*   [pagetranscriber](pages/pagetranscriber.tsv):
    table with the transcriber for each page;
*   [pagewarnings](pages/pagewarnings.txt):
    all page related irregularities encountered during the conversion of DOCX
    to TEI; expect an empty file.

## `trans`

*   [decodified](trans/decodified.txt):
    all passages with decodified text;
*   [displaced](trans/displaced.txt):
    all passages with text from a different page that shows on the same scan;
*   [footnoteexamples](trans/footnoteexamples.txt) and
    [footnoteuntrans](trans/footnoteuntrans.txt):
    examples of footnotes that have not yet been translated; ideally this
    should be an empty file;
*   [footnotes](trans/footnotes.txt):
    list of all footnotes, their Italian original and their English translation;
*   [headers](trans/headers.txt):
    all page headers as extracted from the `docx` files;
*   [letterdate](trans/letterdate.yml):
    the dates of all letters; 
*   [lettermeta](trans/lettermeta.yml):
    contains the result of reading this spreadsheet and extracting the fields
    needed for the website;
*   [lettertranscriber](trans/lettertranscriber.txt):
    the transcribers of each letter;
*   [metamarks](trans/metamarks.txt):
    all editorial remarks, as encountered in the text, with the translations
    into English;
*   [warnings](trans/warnings.txt):
    all non-page related irregularities encountered during the conversion of
    DOCX to TEI; expect an empty file;

## `tei`

*   [elements](tei/elements.txt):
    inventory of TEI-elements and attributes and their occurrence statistics
    including those of attribute values;
*   [errors](tei/errors.txt):
    XML-validation errors; expect an empty file;
*   [ids](tei/ids.txt):
    an overview of all xml:identifiers in the TEI, plus how often they occur
    and how often they are referenced;
*   [lb-parents](tei/lb-parents.txt):
    all possible parent elements of an `<lb>` element and how many `<lb>`
    elements have that parent;
*   [namespaces](tei/namespaces.txt):
    for each element name in the TEI, in which namespaces that element is used;
*   [refs](tei/refs.txt):
    a lot like `ids.txt`, but now it counts the references to xml:ids;
*   [types](tei/types.txt):
    for each element in the TEI source, the schemas that define the element and
    whether it is complex or simple and pure or mixed. 
