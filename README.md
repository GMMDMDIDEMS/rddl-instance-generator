# rddl-instance-generator
<img align="right" src="docs/icon.png" width="300px">
This repository provides a RDDL (Relational Dynamic Influence Diagram Language) instance generator, designed to automate the domain-specific process of generating instance files.

### Background
Generating unique instances for RDDL domains is crucial for evaluating and testing sequential-decision-making algorithms. However, creating these instances manually for each domain can be time-consuming and complex. This project aims to simplify this process by providing an automated way to generate these instances.


## Features
- Generate RDDL instance files from domain-specific configuration files.
- Support for multiple domains, with flexibility to define and add custom domains.
- Easy-to-use command-line interface for quick instance file generation.
- Highly customizable parameters for instance generation, allowing control over problem complexity and size.

<br clear="right"/>

## Installation
The `rddl-instance-generator` is built using [Poetry](https://python-poetry.org/), a dependency management and packaging tool for Python. To install the `rddl-instance-generator` using Poetry, follow these steps:

1. Make sure you have Poetry installed. If you don't have it installed, you can install it by running:
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Clone the `rddl-instance-generator` repository:
   ```
   git clone https://github.com/GMMDMDIDEMS/rddl-instance-generator
   ```

3. Navigate to the project directory:
   ```
   cd rddl-instance-generator
   ```

4. Spawns a shell activates the virtual environment:
   ```
   poetry shell
   ```

5. Install the dependencies using Poetry:
   ```
   poetry install --all-extras
   ```

## Usage
To generate RDDL instance files, use the rddl-instance-generator command. Below are the available options and their descriptions:
```
rddl-instance-generator --domain-name Domain --num-instances 100 --size 10
```

For additional help and options, use:
```
rddl-instance-generator --help
```

