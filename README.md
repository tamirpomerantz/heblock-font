# Heblock

Heblock is a geometric Hebrew and Latin sans-serif for everyday use:
presentations, headlines, interfaces, and running text. It is meant to be
neutral and highly legible — a relatively transparent vessel so the content
stays in front, rather than the letters competing for attention.

Hebrew draws on the skeletons of Zvi Narkiss (especially Narkiss Block and
Narkiss Tam) and on the everyday presence of Arial. Latin is based on
[DM Sans](https://fonts.google.com/specimen/DM+Sans) by Colophon Foundry
([sources](https://github.com/googlefonts/dm-fonts)), with selected letters
adjusted so both scripts belong to one system. Hebrew and Latin production
are by Tamir Pomerantz.

![Heblock specimen](documentation/specimen.png)

## The Connection to DM Sans

The work began next to Roboto, then moved to
[DM Sans](https://fonts.google.com/specimen/DM+Sans) as a Latin foundation that
would sit more naturally with contemporary Latin typography. Hebrew letters
were widened slightly to approach the Latin proportions and to even out the
texture between the two scripts.

Heblock is not a direct translation of DM Sans into Hebrew. The DM Sans
masters were also changed so the two scripts form one system. In Latin, the
lowercase *a* has a more diagonal join to the stem; *t* and *f* are slightly
more square; some square punctuation became round; *Y*, *M*, *V*, and *W*
lost some of the breaks of original DM Sans; *G* has a more stable leg; and
*R* has a slightly more distinctive join, to relate to the Hebrew connections.

![Heblock and DM Sans](documentation/heblock-vs-dmsans.png)

The aim is not a “Hebrew DM Sans,” but a bilingual family in which Hebrew and
Latin feel as if they belong to the same typographic world.

## About

- **Hebrew design and production:** Tamir Pomerantz
- **Latin (DM Sans):** Colophon Foundry, Jonny Pinhorn; selected Latin
  adjustments by Tamir Pomerantz
- **Styles:** static Thin through Black (100–900)
- **Scripts:** Hebrew (including niqqud) and Latin (GF Latin Core, from DM Sans)

## Building

Fonts are built with [gftools](https://github.com/googlefonts/gftools) / Fontmake.

```
make build
```

Quality checks (FontBakery / Fontspector):

```
make test
```

Binaries are written to `fonts/ttf` and `fonts/webfonts`.

## Changelog

**25 August 2026. Version 1.000**

- SIGNIFICANT New family Heblock, based on DM Sans Latin with added Hebrew.

## License

This Font Software is licensed under the SIL Open Font License, Version 1.1.
This license is available with a FAQ at https://openfontlicense.org

## Repository Layout

This font repository structure follows the
[Google Fonts Project Template](https://github.com/googlefonts/googlefonts-project-template)
and the [Google Fonts Guide](https://googlefonts.github.io/gf-guide/).
