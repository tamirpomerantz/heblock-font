# Heblock

Heblock is a geometric sans serif for Latin and Hebrew. Latin is based on
[DM Sans](https://github.com/googlefonts/dm-fonts) by Colophon Foundry. Hebrew and selected Latin changes are by
Tamir Pomerantz.

![Heblock specimen](documentation/specimen.png)

## About

- **Latin:** Colophon Foundry, Jonny Pinhorn
- **Hebrew:** Tamir Pomerantz
- **Styles:** static Thin through Black (100–900)
- **Scripts:** Latin (GF Latin Core and above, inherited from DM Sans) and Hebrew, including niqqud

## Building

Fonts are built with [gftools](https://github.com/googlefonts/gftools) / Fontmake.

```
make build
```

Quality checks:

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
