# RS Nexus Plugin CLI

Developer CLI for scaffolding RS Nexus plugins.

## Commands

```bash
rsnexus-plugin init sensor my-sensor-plugin
rsnexus-plugin init algorithm my-algorithm-plugin
rsnexus-plugin init algorithm my-algorithm-plugin --with-intermediate --with-consolidation
```

Run this from the directory where the plugin repository should be created.
The CLI must be installed in the active Python environment or otherwise
available on `PATH`.

Algorithm scaffolds always include `intermediate_executor.py` and
`consolidation_executor.py`. The `--with-intermediate` and
`--with-consolidation` flags enable those stages in the generated manifest and
config; without the flags, the executor files are disabled no-op placeholders.

From the tooling repo root, run:

```bash
./install.sh
```
