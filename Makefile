SOURCES=$(shell python3 scripts/read-config.py --sources )
FAMILY=$(shell python3 scripts/read-config.py --family )

help:
	@echo "###"
	@echo "# Build targets for $(FAMILY)"
	@echo "###"
	@echo
	@echo "  make build: Builds the fonts and places them in the fonts/ directory"
	@echo "  make test: Tests the fonts with FontBakery"
	@echo

build: build.stamp

venv: venv/touchfile

build.stamp: venv sources/config.yaml $(SOURCES)
	cp scripts/roundCorner.py $$(. venv/bin/activate; python3 -c "import ufo2ft.filters,pathlib; print(pathlib.Path(ufo2ft.filters.__file__).parent / 'roundCorner.py')")
	rm -rf fonts
	. venv/bin/activate; gftools builder sources/config.yaml && touch build.stamp

venv/touchfile: requirements.txt scripts/roundCorner.py
	test -d venv || python3 -m venv venv
	. venv/bin/activate; pip install -Ur requirements.txt
	. venv/bin/activate; python3 -c "import pathlib,ufo2ft.filters; pathlib.Path(ufo2ft.filters.__file__).parent.joinpath('roundCorner.py').write_bytes(pathlib.Path('scripts/roundCorner.py').read_bytes())"
	touch venv/touchfile

test: build.stamp
	. venv/bin/activate; mkdir -p out; fontbakery check-googlefonts -l WARN --full-lists --succinct --html out/fontbakery-report.html --ghmarkdown out/fontbakery-report.md $$(find fonts -type f -name "*.ttf") || echo "FontBakery reported issues. See out/fontbakery-report.md"

clean:
	rm -rf venv fonts build.stamp out

.PHONY: help build test clean
