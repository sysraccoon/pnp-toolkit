# Print&Play ToolKit

_[Note: RU version of readme under development]_

_[**Disclaimer**: The project is under development. Application interface (console and API) may change a lot in the future]_

**pnp-toolkit** - library and cli tool collection for prepare scan files or separate images to complete PnP (Print&Play).

## Installation

```bash
# clone this repository to any directory and make python virtual environment
pip install .
```

## Command Line Usage

Bulding pdf from separate images by specification (just yaml file)

```bash
pnp-toolkit build-pdf --built-in-spec specification_name.yaml source_directory output_directory
```
