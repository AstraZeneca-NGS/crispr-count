.PHONY: help
# Double-hashed comments on the targets get converted into help text: see
# https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## show this help text
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

export DOCKER_BUILDKIT=1
export DOCKER_SCAN_SUGGEST=false
export BUILDKIT_PROGRESS=plain

.PHONY: build-candidate
build-candidate: ## build Docker container as :candidate for testing
	hadolint Dockerfile
	docker build --target build --build-arg START_FROM='.' --tag count_guides_dual:candidate .

release: build-candidate test ## tag :candidate build as :latest if the tests passed
	docker tag count_guides_dual:candidate count_guides_dual:latest

.PHONY: test python-test
test: build-dev python-test test-single-guide test-dual-guide test-python-expected-output ## run all tests

.PHONY: build-dev
build-dev:
	docker build --target dev --build-arg START_FROM='.' --tag count_guides_dual:dev .

%.fq: %.fq.gz
	gzip --decompress --to-stdout $< > $@

.PHONY: python-test
python-test: build-dev test-data/plasmid.fq test-data/dual_guide_library.tsv ## run tests in dev container
	docker run count_guides_dual:dev python -m unittest

	docker run --mount type=bind,source="$$(pwd)/test-data/test-compare-c-python/",target=/data/test-data/test-compare-c-python/ \
	count_guides_dual:dev python -m pytest --keep-workflow-wd-on-fail --symlink

# NB this relies on you having the right python environment activated to run the local tests (see python/runbooks/create-python-env.md).
.PHONY: python-test-locally
python-test-locally: test-data/plasmid.fq test-data/dual_guide_library.tsv ## run tests locally
	python -m unittest
	pytest --keep-workflow-wd-on-fail --symlink

test-single-guide: build-dev ## run end-to-end tests of the Docker container with single-guide
	docker run --mount type=bind,source="$$(pwd)/test-data",target=/assets count_guides_dual:dev \
		count.py --processes 2 \
			--lib /assets/test-single-guide-count/test-single-guide-annot-library--cleanr.txt \
			--in /assets/test-single-guide-count/test-single-revcomp.tsv \
			--out /dev/stdout

test-dual-guide: build-dev ## run dual-guide end-to-end tests of the Docker container
	docker run --mount type=bind,source="$$(pwd)/test-data",target=/assets count_guides_dual:dev \
		count.py --processes 2 \
			--lib /assets/test-dual-guide-count/test-dual-guide-annot-library--cleanr.tsv \
			--in /assets/test-dual-guide-count/test-dual-revcomp.tsv \
			--out /dev/stdout

# This target requires the containers for the C code and the Python code to be
# built, and tagged with count_guides:latest and count_guides_dual:latest
# respectively. It runs them both against the same sequence, and compares the
# output in test-output.
.PHONY: test-compare-c-python
test-compare-c-python: ## compare count output from the C and the Python containers ##FIXME Test is failing, c results differ from python and from shell implementations
	@if ! docker images count_guides      | awk '{ print $$2 }' | grep -q -F latest; then echo "C container count_guides:latest not found; try `make --directory=../c release`"; false; fi
	@if ! docker images count_guides_dual | awk '{ print $$2 }' | grep -q -F latest; then echo "Python container count_guides_dual:latest not found; try `make release`"; false; fi
	@echo "i718 comparison, C vs Python"
	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_dual:latest bash -c 'count.py --lib /data/libraries/az-cruk-count--c-python-test-cleanr-lib.tsv --in <(gzip -dc /data/sequences/SLX-20830.i718_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz | awk "NR%4==2") --out /tmp/test-output/python.count-1'

	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides:latest sh -c "gzip -dc /data/sequences/SLX-20830.i718_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz | count_guides -cleanr /data/libraries/az-cruk-count--c-python-test-cleanr-lib--c-format-lib.tsv > /tmp/test-output/c.count-1"

	@diff --side-by-side "$(shell pwd)/test-output/c.count-1" "$(shell pwd)/test-output/python.count-1" || echo "test failed: counts from C (on the left) differ from Python"
	@echo "i716 comparison, C vs Python"
	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_dual:latest bash -c 'count.py --lib /data/libraries/az-cruk-count--c-python-test-cleanr-lib.tsv --in <(gzip -dc /data/sequences/SLX-20830.i716_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz | awk "NR%4==2") --out /tmp/test-output/python.count-2'
	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides:latest sh -c "gzip -dc /data/sequences/SLX-20830.i716_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz | count_guides -cleanr /data/libraries/az-cruk-count--c-python-test-cleanr-lib--c-format-lib.tsv > /tmp/test-output/c.count-2"
	@diff --side-by-side "$(shell pwd)/test-output/c.count-2" "$(shell pwd)/test-output/python.count-2" || echo "test failed: counts from C (on the left) differ from Python"

# same as the above, but compare the output from the shell container to the Python one
.PHONY: test-compare-shell-python
test-compare-shell-python: ## compare output from shell implementation to the Python
	@if ! docker images count_guides_shell | awk '{ print $$2 }' | grep -q -F latest; then echo "Shell container count_guides_shell:latest not found; try `make --directory=../shell release`"; false; fi
	@if ! docker images count_guides_dual  | awk '{ print $$2 }' | grep -q -F latest; then echo "Python container count_guides_dual:latest not found; try `make release`"; false; fi
	@echo "i716 comparison, Python vs Shell"
	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_dual:latest bash -c 'count.py --lib /data/libraries/az-cruk-count--c-python-test-cleanr-lib.tsv --in <(gzip -dc /data/sequences/SLX-20830.i716_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz | awk "NR%4==2") --out /tmp/test-output/python.count-2'
	gzip -d -k -f test-data/test-compare-c-python/sequences/SLX-20830.i716_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz
	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_shell:latest bash -c '/app/count.sh /data/libraries/az-cruk-count--c-python-test-cleanr-lib.tsv /data/sequences/SLX-20830.i716_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq | sort > /tmp/test-output/shell.count-2'
	diff --side-by-side "$(shell pwd)/test-output/shell.count-2" "$(shell pwd)/test-output/python.count-2" || echo "test failed: counts from shell (on the left) differ from Python"

	@echo "i718 comparison, Python vs Shell"
	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_dual:latest bash -c 'count.py --lib /data/libraries/az-cruk-count--c-python-test-cleanr-lib.tsv --in <(gzip -dc /data/sequences/SLX-20830.i718_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz | awk "NR%4==2") --out /tmp/test-output/python.count-1'
	gzip -d -k -f test-data/test-compare-c-python/sequences/SLX-20830.i718_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz
	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_shell:latest bash -c '/app/count.sh /data/libraries/az-cruk-count--c-python-test-cleanr-lib.tsv /data/sequences/SLX-20830.i718_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq | sort > /tmp/test-output/shell.count-1'
	diff --side-by-side "$(shell pwd)/test-output/shell.count-1" "$(shell pwd)/test-output/python.count-1" || echo "test failed: counts from shell (on the left) differ from Python"
clean: ## remove test output files from test-output directory
	@rm -f test-output/*

.PHONY: test-python-expected-output
test-python-expected-output: ## compare count output from the Python container against the expected outputs
	@if ! docker images count_guides_dual | awk '{ print $$2 }' | grep -q -F dev; then echo "Python container count_guides_dual:dev not found; try `make build-dev`"; false; fi
	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_dual:dev bash -c 'count.py --lib /data/libraries/az-cruk-count--c-python-test-cleanr-lib.tsv --in <(gzip -dc /data/sequences/SLX-20830.i718_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz | awk "NR%4==2") --out /tmp/test-output/python-actual.count-1'

	diff "$(shell pwd)/test-output/expected/python-expected.count-1" "$(shell pwd)/test-output/python-actual.count-1" || echo "test failed: counts python expected does not match with actual output"

	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-compare-c-python",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_dual:dev bash -c 'count.py --lib /data/libraries/az-cruk-count--c-python-test-cleanr-lib.tsv --in <(gzip -dc /data/sequences/SLX-20830.i716_i502.HTN5LDRXY.s_2.r_1--c-py-diff-test.fq.gz | awk "NR%4==2") --out /tmp/test-output/python-actual.count-2'

	diff "$(shell pwd)/test-output/expected/python-expected.count-2" "$(shell pwd)/test-output/python-actual.count-2" || echo "test failed: counts python expected does not match with actual output"

	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-single-guide-count/",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_dual:dev bash -c 'count.py --lib /data/test-single-guide-annot-library--cleanr.txt --in /data/test-single-revcomp.tsv --out /tmp/test-output/python-actual.count-3'

	diff "$(shell pwd)/test-output/expected/python-expected.count-3" "$(shell pwd)/test-output/python-actual.count-3" || echo "test failed: counts python expected does not match with actual output"

	docker run \
		--mount type=bind,source="$(shell pwd)/test-data/test-dual-guide-count/",target="/data",readonly \
		--mount type=bind,source="$(shell pwd)/test-output",target="/tmp/test-output" \
		count_guides_dual:dev bash -c 'count.py --lib /data/test-dual-guide-annot-library--cleanr.tsv --in /data/test-dual-revcomp.tsv --out /tmp/test-output/python-actual.count-4'

	diff "$(shell pwd)/test-output/expected/python-expected.count-4" "$(shell pwd)/test-output/python-actual.count-4" || echo "test failed: counts python expected does not match with actual output"
