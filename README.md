* Author: Asif Nadaf
* Language: python3.x
* Platform: GNU/LINUX
* Spyder version: 5.3.3  (conda)
* Python version: 3.9.12 64-bit
* Qt version: 5.15.2
* PyQt5 version: 5.15.7
* Operating System: Linux 5.19.0-35-generic

log_parser_extractor_xcel_dumper.py:
This python3.x script is a low-level parser-cum-dumper intended to check the integrity of the logs received at the MS Azure end.
Regex is the hero for any parser written in OOPs unless you want to experiment with UNIX/LINUX tools SED and AWK.
Along with the Python Regex library, the script utilizes pythonic data structures to extract and dump temperature values to an excel sheet.

This script was written to perform the required functionalities on the logs:
1) Parsing for tokens matching the ones from a particular device at a timestamp.
2) Checking for sub-log integrity for the particular device(no encryption, 4-byte, 8-byte).
3) Dump data through Python library for GNU/Linux OpenOffice Writer or MS Excel.

MS_Azure_Logs:
The logs are received on the cloud, MS Azure, and the log buffer limit is 1000 lines for every session that times out.
These logs were consolidated after successful sessions. 
Hence they contain over 1000 lines.4-byte and 8-byte encrypted device logs are received separately from the devices which don't have any encryption set.

Krypto_MTE_Azure_Logs.xlsx:
This excel sheet contains the dumped data. Once the data is dumped in the EXCEL file, the crux of finding the trade-offs with transmit times, on-air latency, decryption time, etc... can be analyzed threadbare.


* NOTE: Platform Agnostic and a work in progress!