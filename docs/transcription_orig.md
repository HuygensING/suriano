
# Corpus suriano - letters

## How a TF dataset represents a corpus

A TF dataset contains: 

*   textual objects as a set of nodes;
*   textual positions as a range of slots, which are also nodes;
*   nodes are represented as numbers;
*   nodes are divided in types, which have a name;
*   non-slot nodes are linked to slots;
*   all data about textual positions and objects are in features,
    which map nodes to values;
*   features have a name, and each feature is stored in a separate file with that name;
*   in particular, the text itself is stored in one or more features;
*   there are a few standard features that are present in every TF dataset;
*   See the
    [Text-Fabric data model](https://annotation.github.io/text-fabric/tf/about/datamodel.html).

In this dataset, **chars** fulfill the role of slots.

## How TEI maps to TF

*   Text-Fabric *char nodes* correspond to **characters** in TEI element content;
*   Text-Fabric *node types* correspond to TEI *element names (tags)*;
*   Text-Fabric *non-char nodes* correspond to TEI *elements in the source*;
*   Text-Fabric *features* correspond to TEI *attributes*;
*   Text-Fabric *edges* correspond to *relationships* between TEI elements;


*   Here are the [TEI elements and attributes](elements.md) used in this corpus.

*   Text-Fabric *node types* that start with a `?` correspond to TEI processing 
    instruction with that node type as target. The attributes of the processing
    instruction translate to TF features. As to the link to slots: it is
    treated as if it were an empty element.


*   Processing instructions in the TEI are ignored and do not leave any trace in the
    TF data.



The conversion may invoke custom code which may generate extra features.
For these features, metadata may have been declared, and it will show in the
generated documentation.



The TEI to TF conversion is an almost literal and very faithful transformation from
the TEI source files to a Text-Fabric data set.

## TF nodes and features overview

(only in as far they are not in 1-1 correspondence with TEI elements and attributes)



### node type `folder`

*The type of subfolders of TEI documents.*

**Section level 1**

**Features**

feature | description
--- | ---
`folder` | name of the subfolder

### node type `file`

*The type of individual TEI documents.*

**Section level 2**

**Features**

feature | description
--- | ---
`file` | name of the file, without the `.xml` extension. Other extensions are included.





### node type `chunk`


*Top-level division of material in a TEI document.*




**Section level 3**

**Features**



feature | description
--- | ---
`chunk` | sequence number of the chunk within the file, starting with 1.







### node type `word`

*Individual words, without space or punctuation.*






**Features**

feature | description
--- | ---
`str` | the characters of the word, without soft hyphens.
`after` | the non-word characters after the word, up till the next word.
`is_meta` | whether a word is in the `teiHeader` element
`is_note` | whether a word is in a note element
`rend_r` | whether a word is under the influence of a `rend="r"` attribute.




### node type `char`

*Unicode characters.*

**Slot type.**

The characters of the text of the elements.
Ignorable white-space has been discarded, and is not present in the TF dataset.
Meaningful white-space has been condensed to single spaces.

**Features**

feature | description
--- | ---
`ch` | the unicode character in that char.
`empty` | whether a char has been inserted in an empty element
`extraspace` | whether this is an extra space or newline, added by the conversion
`is_meta` | whether a character is in the `teiHeader` element
`is_note` | whether a character is in a note element
`rend_r` | whether a character is under the influence of a `rend="r"` attribute.




## Edge features

feature | description
--- | ---

Note that edges can be traversed in both directions, see the
[docs](https://annotation.github.io/text-fabric/tf/core/edgefeature.html).





## Extra features





The conversion has not generated extra features by means of custom code.


## Sectioning

The material is divided into 3 levels of sections, mainly for the purposes
of text display.

But how these levels relate to the source material is a different matter.

The conversion supports a few sectioning models that specify this.
This aspect is *work-in-progress*, because TEI sources differ wildly in how they
are sectioned.
The sectioning models that are currently supported correspond to cases we have
encountered, we have not done exhaustive research into TEI sectioning in practice.

This corpus is converted with section **Model I**.



### Model I: folders and files

This model assumes that the source is a directory consisting of folders
consisting of XML files, the TEI files.

There are three section levels:

*   *folder* Level 1 heading corresponding to folders with TEI files;
    heading: the name of the folder;
*   *file* Level 2 heading corresponding to individual TEI files;
    heading: the name of the file;
*   *chunk* Level 3 heading corresponding to top-level divisions in a TEI file;
    heading: the sequence number of the chunk within the file.

All section headings are stored in a feature with the same name as the type of the section:
*folder*, *file*, *chunk*.

#### Details

1.  *chunk* nodes have been made as follows:

    *   `<facsimile>`, `<fsdDecl>`, `<sourceDoc>`, and `<standOff>` are chunks;
    *   immediate children of `<teiHeader>` are chunks;
    *   immediate children of `<text>` are chunks,
        except the *text structure* elements
        `<front>`, `<body>`, `<back>` and `<group>`;
    *   immediate children of the text structure elements are chunks,
    *   but not necessarily empty elements such as `<lb/>` and `<pb/>`.

1.  files and folder are sorted in the lexicographic ordering of their names;
1.  the folder `__ignore__` is ignored.
1.  the headings consist of the names of the files and folders
1.  the slots generated for empty elements are linked to the current chunk if there is
    a current chunk; otherwise they will be linked to the upcoming chunk.

There are no additional switches for tweaking the model further, at the moment.






## Word detection

Words have been be detected.
They are maximally long sequences of alphanumeric characters
and hyphens.

1.  What is alphanumeric is determined by the unicode class of the character,
    see the Python documentation of the function
    [`isalnum()`](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str)
1.  Hyphens are Unicode characters 002D (ASCII hyphen) and 2010 (unicode hyphen).
1.  Words get the following features:
    *   `str`: the alphanumeric string that is the word;
    *   `after`: the non-alphanumeric string after the word until the following word.




## Chars

Whether characters of words  or tokens are taken as the basic unit (*slot*) is decided
by the parameter `wordAsSlot`, passed to the conversion, and whether tokens have been
provided later on.
(for this corpus the slot type is **char**).

### Chars and empty elements

When empty elements occur, something must be done to anchor them to the text stream.

To such elements we add an empty char with the ZERO-WIDTH-SPACE (Unicode 200B) as
character/string value.

Such slots get the feature `empty` assigned with value 1.

### Chars in general

1.  Spaces are stripped when they are between elements whose parent does not allow
    mixed content; other white-space is reduced to a single space.
1.  However, after direct child elements of pure elements we add a single space
    or newline: if there is an ancestor with mixed content, we add a space;
    if the whole ancestry consists of pure elements (typically in the TEI header),
    we add a newline.
    
    
1.  All chars inside the `teiHeader` will get the feature `is_meta` set to 1;
    for chars inside the body, `is_meta` has no value.



## More about characters

The basic unit is the unicode character.
For each character in the input we make a slot, but the correspondence is not
quite 1-1, because of the white-space handling.

1.  *char* nodes get this defining feature:
    *   `ch`: the character of the slot






## Text kinds and styled formatting

We record in additional features whether text occurs in metadata elements and
in note elements and what formatting specifiers influence the text.
These features are provided for `char` and `word` nodes, and have only one value: 1.
The absence of values means that the corresponding property does not hold.

The following features are added:

*   `is_meta`: 1 if the word occurs in inside the `<teiHeader>`, no
    value otherwise.
*   `is_note`: 1 if the word occurs in inside the `<note>`, no value otherwise.
*   `rend_r`: for any `r` that is the value of a `rend` attribute.

All these features are defined for `char` and `word` nodes.
For word nodes, the value of these features is set equal to what these features
are for their first character.

Special formatting for the `rend_r` features is supported for some values of `r`.
The conversion supports these out-of-the-box:

value | description
--- | ---
`above` | above the line
`b` | bold font weight
`below` | below the line
`bold` | bold font weight
`center` | horizontally centred text
`h1` | heading of level 1
`h2` | heading of level 2
`h3` | heading of level 3
`h4` | heading of level 4
`h5` | heading of level 5
`h6` | heading of level 6
`i` | cursive font style
`italic` | cursive font style
`italics` | cursive font style
`large` | large font size
`margin` | in the margin
`sc` | small-caps font variation
`small_caps` | small-caps font variation
`smallcaps` | small-caps font variation
`spaced` | widely spaced between characters
`spat` | widely spaced between characters
`sub` | as subscript
`sup` | as superscript
`super` | as superscript
`ul` | underlined text
`underline` | underlined text

It is possible for the corpus designer to add more formatting on a per-corpus
basis by adding it to the `display.css` in the app directory of the corpus.
Unsupported values get a generic kind of special format: an orange-like color.

Special formatting becomes visible when material is rendered in a `layout` text
format.

## Text formats

Text-formats regulate how text is displayed, and they can also determine
what text is displayed.

There are two kind of text-formats: those that start with the word `layout` and
those that start with `text`.

The `text` formats do not apply any kind of special formatting, the `layout` formats
do.

We have the following formats:

*   `text-orig-full`: all text
*   `layout-orig-full`: all text, formatted in HTML

## Boundary conditions

XML is complicated, the TEI guidelines use that complexity to the full.
In particular, it is difficult to determine what the set of TEI elements is
and what their properties are, just by looking at the schemas, because they are full
of macros, indirections, and abstractions, which can be overridden in any particular
TEI application.

On the other hand, the resulting TF should consist of clearly demarcated node types
and a simple list of features. In order to make that happen, we simplify matters
a bit.


1.  Processing instructions (`<?proc a="b">`) are treated as empty elements with as tag
    the *target* with preceding `?` and as attributes its pseudo attributes.


1.  Processing instructions (`<?proc a="b">`) are ignored.
1.  Comments (`<!-- this is a comment -->`) are ignored.
1.  Declarations (`<?xml ...>` `<?xml-model ...>` `<?xml-stylesheet ...>`) are
    read by the parser, but do not leave traces in the TF output.
1.  The attributes of the root-element (`<TEI>`) are ignored.
1.  Namespaces (`xmlns="http://www.tei-c.org/ns/1.0"`) are read by the parser,
    but only the unqualified names are distinguishable in the output as feature names.
    So if the input has elements `tei:abb` and `ns:abb`, we'll see just the node
    type `abb` in the output.

### Validation

We have used [lxml](https://lxml.de) for XML parsing. During `convert` it is not used
in validating mode, but we can trigger a validation step during `check`.

However, some information about the elements, in particular whether they allow
mixed content or not, has been gleaned from the schemas, and has been used
during conversion.

Care has been taken that the names of these extra nodes and features do not collide
with element/attribute names of the TEI.


## See also

*   [about](about.md)



