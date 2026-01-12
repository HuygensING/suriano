.PHONY: clean untangle webannotations annorepo start stop up down html
.SECONDARY:
.DELETE_ON_ERROR:

HOSTNAME ?= $(shell hostname -f)
export HOSTNAME
export PATH := $(HOME)/.cargo/bin:$(PATH) 

#----------------- read environment variables from external file(s) ------------
ifneq ($(INCLUDE_ENV),0)
include common.env
export $(shell sed '/^\#/d; s/=.*//' common.env)

ifneq (,$(wildcard $(HOSTNAME).env))
#hostname config exists
include $(HOSTNAME).env
export $(shell sed '/^\#/d; s/=.*//' $(HOSTNAME).env)
endif
ifneq (,$(wildcard custom.env))
#custom config exists
include custom.env
export $(shell sed '/^\#/d; s/=.*//' custom.env)
endif
endif
#--------------------------------------------------------------------------------
tei_dir := datasource/tei
intro_files := $(tei_dir)/about/Inleiding_introduction.xml $(tei_dir)/about/Verantwoording_Notes_for_the_reader.xml $(tei_dir)/about/colofon.xml $(tei_dir)/about/woord-van-dank.xml
tei_files := $(wildcard $(tei_dir)/letters/*.xml) $(tei_dir)/intro/intro.xml
#tei_flattened contains the 'virtual' files where one layer of nesting is removed
tei_flattened := $(subst letters/,,$(tei_files))
tei_flattened := $(subst intro/,,$(tei_flattened))
tei_flattened := $(subst about/,,$(tei_flattened))
stam_files := $(tei_flattened:$(tei_dir)/%.xml=work/%.store.stam.json)
webannotation_files := $(tei_flattened:$(tei_dir)/%.xml=work/%.webannotations.jsonl)
html_files := $(tei_flattened:$(tei_dir)/%.xml=data/html/%.html)


all: index
untangle: $(stam_files)
stam: $(stam_files)
webannotations: $(webannotation_files)
html: $(html_files)


work:
	mkdir -p $@

$(tei_dir)/intro/intro.xml: $(intro_files)
	mkdir -p $(tei_dir)/intro
	. env/bin/activate && merge-intro-texts $(intro_files) > $@

# untangle from XML source
#  also produces plain text files in *.txt and work/*.normal.txt (normalised)
#  look in multiple subdirectories for the sources (VPATH)
VPATH = $(tei_dir)/letters:$(tei_dir)/intro
work/%.store.stam.json: %.xml etc/stam/fromxml/tei.toml etc/stam/translatetext/norm.toml $(tei_dir)/intro/intro.xml | work
	@echo "--- Preparing $< ---">&2
	echo "nginx_url = \"$(NGINX_URL)\"" > work/$*.context.toml
	echo "iiifbaseurl = \"https://iiif-text.huc.knaw.nl/iiif/3/suriano|illustrations|\"" >> work/$*.context.toml
	echo "iiifextension = \".jpg\"" >> work/$*.context.toml
	@echo "--- Untangling $< ---">&2
	stam fromxml --config etc/stam/fromxml/tei.toml \
		--context-file work/$*.context.toml \
		--id-prefix "urn:mace:huc.knaw.nl:suriano:{resource}#" --force-new $@ -f $<
	@echo "--- Creating normalised variants ---">&2
	stam translatetext --rules etc/stam/translatetext/norm.toml $@ 
	@if [ -e $*.normal.txt ]; then \
		echo "--- Translating annotations to normalised variant ---">&2; \
		stam translate --verbose --no-translations --no-resegmentations --ignore-errors \
			--id-strategy suffix=.normal \
			--query "SELECT ANNOTATION WHERE DATA \"http://www.w3.org/1999/02/22-rdf-syntax-ns#\" \"type\";" $@; \
	fi;

vpath #reset VPATH

#this defines context variables that will be available to the templating engine globally, for a given resource
work/%.context.toml:
	echo "nginx_url: \"$(NGINX_URL)\"" > $@
	echo "iiifbaseurl: \"https://iiif-text.huc.knaw.nl/iiif/3/suriano|illustrations|\"" >> $@
	echo "iiifextension: \".jpg\"" >> $@

work/%.webannotations.jsonl: work/%.store.stam.json data/apparatus | env 
	@echo "--- Exporting web annotations for $< ---">&2
	. env/bin/activate && stam query \
		--add-context "https://ns.huc.knaw.nl/text.jsonld" \
		--add-context "https://ns.huc.knaw.nl/textannodata.jsonld" \
		--ns "tei: http://www.tei-c.org/ns/1.0#" \
		--ns "xml: http://www.w3.org/XML/1998/namespace/" \
		--extra-target-template "$(TEXTSURF_URL)/api2/$(PROJECT)|{resource}/{begin},{end}" \
		--annotation-prefix "$(ANNOREPO_URL)/$(PROJECT)/" \
		--resource-prefix "$(TEXTSURF_URL)/$(PROJECT)" \
		--format w3anno \
		$< | consolidate-web-annotations --apparatus-dir data/apparatus --body-id-prefix "urn:mace:huc.knaw.nl:suriano:$*#body" > $@;
	@rm .annorepo-uploaded 2> /dev/null || true

validate: tei-info
tei-info: etc/tei.yml
	@echo "--- Validating TEI ---">&2
	mkdir $@
	. env/bin/activate && validate-tei --tei-dir $(tei_dir) --output-dir $@  --schema-dir schema --config etc/tei.yml

scans: data/scans
data/scans:
	@echo "--- Downloading scans from surfdrive ---">&2
	@echo "   Note: The scans are on a private server for now">&2
	mkdir -p $@
ifneq (,$(TT_USERNAME))
	scp $(TT_USERNAME)@n-195-169-89-124.diginfra.net:/data/scans/suriano-scans.zip $@/suriano-scans.zip
else
	@echo "   Note: Set \$TT_USERNAME to your username on the private server if the next step fails">&2
	scp n-195-169-89-124.diginfra.net:/data/scans/suriano-scans.zip $@/suriano-scans.zip
endif
	UNZIP_DISABLE_ZIPBOMB_DETECTION=TRUE unzip $@/suriano-scans.zip -d data/suriano-scans
	mv data/suriano-scans/* data/scans/
	rm -rf data/suriano-scans*


manifests: data/manifests
data/manifests: tei-info data/scans etc/iiif.yml
	@echo "--- Creating manifests ---">&2
	mkdir -p $@
	. env/bin/activate && generate-manifests --tei-info-dir $< --tei-dir $(tei_dir) --scaninfo-dir data/scans --output-dir $@ --config etc/iiif.yml --title $(PROJECT) --base-uri $(CANTALOUPE_URL) --iiif-base-uri $(CANTALOUPE_URL)

apparatus: data/apparatus
data/apparatus:
	@echo "--- Converting apparatus from TEI XML ---">&2
	mkdir -p $@
	. env/bin/activate && editem-apparatus-convert --inputdir $(tei_dir)/apparatus --outputdir $@ --sizes scanInfo/sizes_illustrations.tsv --project $(PROJECT) --base-url $(CANTALOUPE_URL)/iiif/3


work/%.html.batch: work/%.store.stam.json etc/stam/query.template
	@echo "--- Building script from template for HTML visualisation ---">&2
	#get a list of all resources in the annotation store and output a batch script for each resource (this will usually just be 1 resource)
	stam query --no-header --query 'SELECT RESOURCE ?res' $< | cut -f 2 | sort -n | programs/makebatch.sh etc/stam/query.template html html > $@ 

data/html/%.html: work/%.store.stam.json work/%.html.batch | env
	@echo "--- HTML visualisation via STAM ---">&2
	mkdir -p data/html
	stam batch $< < work/$*.html.batch

ingest: annorepo textsurf nginx

annorepo: .annorepo-uploaded
.annorepo-uploaded: .started env $(webannotation_files)
	@echo "--- Clearing Broccoli cache (prior) ---">&2
	-curl -X DELETE "$(BROCCOLI_URL)/projects/$(PROJECT)/cache"
	@echo "--- Exporting web annotations to Annorepo ---">&2
	. env/bin/activate && upload-web-annotations \
		--annorepo-base-url "$(ANNOREPO_URL)" \
		--container-id "$(PROJECT)" \
		--api-key "$(ANNOREPO_ROOT_API_KEY)" \
		--overwrite-existing-container $(webannotation_files)
	@echo "--- Clearing Broccoli cache (post) ---">&2
	-curl -X DELETE "$(BROCCOLI_URL)/projects/$(PROJECT)/cache"
	@touch $@

textsurf: data/textsurf/.populated
data/textsurf/.populated: .started $(stam-files)
	mkdir -p data/textsurf/$(PROJECT)
	chmod a+w data/textsurf/$(PROJECT) #TODO: temporary patch, this is obviously not smart in production settings
	cp -f work/*.txt data/textsurf/$(PROJECT)
	@touch $@

nginx: data/nginx/.populated
data/nginx/.populated: .started data/apparatus data/manifests
	mkdir -p data/nginx/files/$(PROJECT)/apparatus
	cp -f data/apparatus/artwork-entities.json data/nginx/files/$(PROJECT)/apparatus
	cp -f data/apparatus/bio-entities.json data/nginx/files/$(PROJECT)/apparatus
	cp -f data/apparatus/bibliolist-en.html data/nginx/files/$(PROJECT)/apparatus
	cp -f data/apparatus/bibliolist-nl.html data/nginx/files/$(PROJECT)/apparatus
	cp -rf data/manifests data/nginx/files/$(PROJECT)
	@touch $@

index: .index
.index: ingest etc/indexer/config.yml | env
	. env/bin/activate && peen-indexer \
		--annorepo-host=$(ANNOREPO_URL) \
		--annorepo-container=$(PROJECT) \
		--config etc/indexer/config.yml \
		--elastic-host=$(ELASTIC_URL) \
		--elastic-index=$(PROJECT) \
		--trace \
		--progress
	@touch $@

install-dependencies: 
	@echo "--- Checking global prerequisites---">&2
	@command -v cargo || (echo "Missing dependency: cargo" && false)
	@command -v rustc || (echo "Missing dependency: rustc" && false)
	@command -v curl || (echo "Missing dependency: curl" && false)
	@command -v python3 || (echo "Missing dependency: python3" && false)
	@command -v docker || (echo "Missing dependency: docker" && false)
	@echo "--- Installing local dependencies ---">&2
	cargo install stam-tools
	make env

env: requirements.txt
	@echo "--- Setting up virtual environment ---">&2
	python3 -m venv env && . env/bin/activate && pip install -r requirements.txt
	touch $@
	
clean: clean-services
	-rm -Rf *.stam.json work tei-info manifests

clean-services:
	-make stop
	-rm -Rf .started .annorepo-uploaded .index data/*

clean-annorepo:
	-rm -rf data/mongo
	-rm .annorepo-uploaded

clean-textsurf:
	-rm -rf data/textsurf

clean-nginx:
	-rm -rf data/nginx

clean-index:
	-rm -rf data/elastic
	-rm .index

clean-apparatus:
	-rm -rf data/apparatus

clean-manifests:
	-rm -rf data/manifests

clean-scans:
	-rm -rf data/scans

clean-dependencies:
	@echo "--- Cleaning dependencies ---">&2
	-rm -Rf env

clean-all: clean clean-dependencies

logs:
	docker compose --env-file common.env logs --follow

up: .started
start: .started
.started:
ifeq ($(MANAGE_SERVICES),1)
	mkdir -p data/elastic
	chmod a+rwx data/elastic #temporary patch, this is obviously not smart in production settings
	@ping -c 1 $(HOSTNAME) || (echo "Sanity check failed: detected hostname ($HOSTNAME) does not resolve" && false)
	@touch $@
ifneq (,$(wildcard custom.env))
	@echo "--- Starting services (with custom config) ---">&2
	docker compose --env-file common.env --env-file "custom.env" up -d
else ifneq (,$(wildcard $(HOSTNAME).env))
	@echo "--- Starting services for $(HOSTNAME) ---">&2
	docker compose --env-file common.env --env-file "$(HOSTNAME).env" up -d
else
	@echo "--- Starting services (common configuration only) ---">&2
	docker compose --env-file common.env up -d
endif
	@echo "--- Use 'make logs' to see docker logs" >&2
else
	@echo "--- Services are not managed, not starting them ---">&2
	@touch $@
endif

down: stop
stop:
ifeq ($(MANAGE_SERVICES),1)
	@echo "--- Stopping services ---">&2 
	docker compose --env-file common.env down
	@rm .started || true
else
	@echo "--- Services are not managed, not stopping them ---">&2
	@rm .started || true
endif

architecture.svg: architecture.mmd
	mmdc -i $< -o $@

architecture.png: architecture.mmd
	mmdc -w 3820 -i $< -o $@


help:
	@echo "Please use \`make <target>', where <target> is one of:"
	@echo "  install-dependencies       - to install the necessary dependencies for the data processing pipeline"
	@echo
	@echo "  start                      - to start all services (docker compose up)"
	@echo "  stop                       - to stop all services (docker compose down)"
	@echo "  logs                       - to view/follow the logs of all services (docker compose logs)"
	@echo 
	@echo "(individual steps in ascending/chronological dependency order where applicable):"
	@echo "  validate                   - to validate TEI XML input"
	@echo "  scans                      - download scans (from surfdrive, must have been shared with you)"
	@echo "  manifests                  - create IIIF manifests"
	@echo "  apparatus                  - convert apparatus from TEI XML"
	@echo ""
	@echo "  untangle                   - to untangle TEI XML into STAM JSON and plain text"
	@echo "  html                       - to create static HTML visualisations per letter"
	@echo "  webannotations             - to generate webannotations"
	@echo "  ingest                     - to populate the various services with data. Subtargets "
	@echo "      annorepo               - to upload the webannotations to Annorepo"
	@echo "      textsurf               - to add the texts to TextSurf"
	@echo "      index                  - to build the search index"
	@echo "      nginx                  - to copy apparatus files to nginx"
	@echo
	@echo "(cleaning targets):"
	@echo "  clean                      - clean all generated targets (including services, but keeps dependencies intact)"
	@echo "   clean-services             - cleans all data pertaining to the services. subtargets:"
	@echo "  	clean-apparatus"
	@echo "  	clean-scans"
	@echo "  	clean-manifests"
	@echo "  	clean-annorepo"
	@echo "  	clean-textsurf"
	@echo "  	clean-index"
	@echo "  	clean-nginx"
	@echo "  clean-dependencies         - clean local dependencies (python env)"
	@echo "  clean-all                  - clean targets and dependencies"
