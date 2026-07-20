# Nexus N3 Plugin SDK

This package contains the minimal shared contracts needed by Nexus N3 plugins.

These modules are copied from `nexus-n3-core` as an initial compatibility step.
They are intentionally duplicated for now so plugin development can proceed
without changing the currently working `nexus-n3-core` runtime.

Note there are sample types for ecg and hr that can be used independently or combined.

For example, Movesense outputs both ECG and HR and this will present issues in writing to file in nexus-n3-core. Polar H10 only outputs HR so is easy to handle.