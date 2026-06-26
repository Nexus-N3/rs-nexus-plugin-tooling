# RS Nexus Plugin SDK

This package contains the minimal shared contracts needed by RS Nexus plugins.

These modules are copied from `rs-nexus-os` as an initial compatibility step.
They are intentionally duplicated for now so plugin development can proceed
without changing the currently working `rs-nexus-os` runtime.

Note there are sample types for ecg and hr that can be used independently or combined.

For example, Movesense outputs both ECG and HR and this will present issues in writing to file in rs-nexus-os. Polar H10 only outputs HR so is easy to handle.