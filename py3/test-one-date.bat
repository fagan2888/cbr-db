call ini.bat
python bankform.py reset database raw
python bankform.py reset database final
REM goto no_download
python bankform.py download 101 --date 2015-01-01
python bankform.py unpack   101 --date 2015-01-01
python bankform.py make csv 101 --date 2015-01-01
:no_download
python bankform.py import csv  101 --date 2015-01-01
python bankform.py make dataset 101
python bankform.py migrate dataset 101
python bankform.py import alloc
python bankform.py import tables    
python bankform.py make balance 
python bankform.py report balance
