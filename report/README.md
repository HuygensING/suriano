# Suriano - Letters (Reports of the conversions/curation)

The scans and transcriptions of the Suriano dataset have been analyzed,
corrected and checked during the conversion from source to website.
Here is an overview of the reports generated during the process.

The reports are grouped as follows:

*   `scans`: result of scan processing;
*   `pages`: results of composing a catalog of pages out of the scans and the
    transcriptions;
*   `trans`: results of analysing the transcriptions;
*   `tei`: results of converting the TEI to TF.

## `scans`

*   `cfgerrors.txt`: errors in the configuration files for the scans;
*   `scanerrors.txt`: A list of errors during the processing of the scans. Expect an
    empty file.
*   `thumberrors.txt`: A list of errors during the generation of thumbnails of
    the scans. Expect an empty file.
*   `thumbpages.txt`: A list of the generated thumbnails.

## `pages`

*   `pageinfo.txt`: the component structure of the corpus in filzas, letters, texts
    and pages;
*   `pagescan.tsv`: for each page, whether there is a scan and whether there is a
    transcription. If both are present, the status field is `OK`. Expect `OK` in every
    row.
*   `pageseq.json`: for each filza the exact sequence of pages in it, formatted as JSON;
*   `pagetranscriber.tsv`: table with the transcriber for each page;
*   `pagewarnings.txt`: all page related irregularities encountered during the
    conversion of DOCX to TEI; expect an empty file;

## `trans`

*   `decodified.txt`: all passages with decodified text;
*   `displaced.txt`: all passages with text from a different page that shows on
    the same scan;
*   `footnoteexamples.txt` and `footnoteuntrans.txt`: examples of footnotes
    that have not yet been translated; ideally this should be an empty file;
*   `footnotes.txt`: list of all footnotes, their Italian original and their English
    translation;
*   `headers.txt`: all page headers as extracted from the `docx` files;
*   `letterdate.yml`: the dates of all letters; 
*   `lettermeta.yml` contains the result of reading this spreadsheet and extracting
    the fields needed for the website.
*   `lettertranscriber.txt`: the transcribers of each letter;
*   `metamarks.txt`: all editorial remarks, as encountered in the text, with the
    translations into English;
*   `warnings.txt`: all non-page related irregularities encountered during the
    conversion of DOCX to TEI; expect an empty file;

## `tei`

*   `elements.txt`: an inventory of elements, attributes, and attribute values
    encountered in the TEI;
*   `errors.txt`: validation errors of the TEI; expect an empty file;
*   `ids.txt`: XML-IDs encountered and how often they are have been referred to;
*   `lb-parents.txt`: which elements contain `lb` elements and how many times;
*   `namespaces.txt`: show which namespaces have been used in the TEI; expect exactly
    one; if more, there is the risk that elements with the same name in
    different namespaces are treated equally while this might not be intended;
*   `refs.txt`: how many occurrences of elements that refer to an XML-ID, and how many
    resolve, are dangling, etc.
*   `types.txt`: for each element that occurs, whether the element is complex or simple
    and mixed or pure.

Various files that report on the conversion from TEI to TF:

*   `elements.txt`: inventory of TEI-elements and attributes and their occurrence
    statistics;
*   `errors.txt`: XML-validation errors. Expect an empty file.
*   `ids.txt`: An overview of all xml:identifiers in the TEI, plus how often they occur
    and how often they are referenced;
*   `lb-parents.txt`: all possible parent elements of an `<lb>` element and how many
    `<lb>` elements have that parent;
*   `namespaces.txt`: for each element name in the TEI, in which namespaces that element
    is used;
*   `refs.txt`: a lot like `ids.txt`, but now it counts the references to xml:ids.
*   `types.txt`: for each element in the TEI source, the schemas that define the element
    and whether it is complex or simple and pure or mixed. 

