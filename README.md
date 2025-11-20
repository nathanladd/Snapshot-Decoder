# Snapshot-Decoder
Windows desktop app to interpret engine data saved in a Bobcat Engine Analyzer Snapshot.
This app can open specific .xls and .xlsx files previously saved by Bobcat Engine Analyzer,
parse the Snapshot data in order to determine what type of Snapshot file has been opened 
and pull any general machine information from the Snapshot header. Snapshot Decoder can then
read-in all frames af all PIDs in the Snapshot delineated file and store them in a Data Frame.

The PIDs can be searched, selected, and charted. There are also 'Quick Chart' commands with PIDs
pre-selected based on troubleshooting succes for common diagnostic tasks avaiolable at a click 
of a button.

Charts can be saved as a single page or multi-page .pdf file.
