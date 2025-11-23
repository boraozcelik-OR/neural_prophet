.PHONY: diagnostics bootstrap dev prod install-deps

diagnostics:
python ops/diagnostics.py

bootstrap:
python ops/bootstrap.py

install-deps:
bash ops/shell/install_dependencies.sh

dev:
bash ops/shell/run_dev.sh

prod:
bash ops/shell/run_prod.sh
