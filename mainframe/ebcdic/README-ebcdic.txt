CLMHIST.cbl in this folder is EBCDIC, not UTF-8.

It is a byte-for-byte download of member CLMHIST from CORV.PROD.COBOL, taken with a
binary FTP transfer, so it is still in IBM code page 037. Line breaks are the EBCDIC
line-feed byte X'25' that the download tool inserted after each 80-byte card image.
Opened as UTF-8 it looks like noise; decoded with cp037 it is an ordinary COBOL program.

Program: CLMHIST, claims history extract, run by JCL CLMDAILY step STEP020.
Reads CORV.CLMMAST (copybook CLMREC), writes CORV.CLM.HISTORY(+1).
History window: CLMPARM01 HISTORY-MONTHS=13.

Every other file under mainframe/ was converted to UTF-8 when it was checked in.
