# Snapshot-Decoder

Windows desktop app to interpret engine data saved in a Bobcat Engine Analyzer Snapshot. 
This app can open specific .xls and .xlsx files previously saved by Bobcat Engine Analyzer, parse the Snapshot data 
in order to determine what type of Snapshot file has been opened and pull useful general machine information from the 
Snapshot file. Snapshot Decoder can then read-in all frames of all PIDs in the Snapshot delineated file and store 
them in a Data Frame. Snapshot Decoder currently reads V1 Delphi ECUs, V2 Bosch ECUs, and V1 Engine Use Data. 

The PIDs can be searched, selected, and charted. There are also 'Quick Chart' commands with PIDs pre-selected based 
on troubleshooting success for common diagnostic tasks available at a click of a button. Charts can be zoomed and paned.
Multiple charts can be broken out into separate windows for comparison. 

Charts can be saved as a single page or multi-page .pdf file.


This project is dual-licensed.

## Licensing Options

### 1. Open-Source License
[![License: MIT/GPL-3.0](https://img.shields.io/badge/License-MIT%20or%20GPL--3.0-blue.svg)](#license)

The project is available under the open-source license found in the file:

**LICENSE**

You may use, modify, and distribute the software under the terms of that license.

### 2. Commercial License
If you would like to use this project under different terms—such as
including it in proprietary software or using it without the conditions
of the open-source license—you may obtain a commercial license.

Contact:
Nathan Ladd
nathan_ladd@comcast.net

## Contributions
By submitting a pull request, you agree that your contribution may be
licensed under both the open-source license and the commercial license.
