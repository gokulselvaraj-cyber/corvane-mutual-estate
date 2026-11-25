000100*================================================================
000200* CLMINQS  SYMBOLIC MAP FOR MAPSET CLMINQS, MAP CLMINQM
000300*          (ASSEMBLED FROM mainframe/cics/CLMINQS.bms)
000400*================================================================
000500 01  CLMINQMI.
000600     05  FILLER                  PIC X(12).
000700     05  CLMNOL                  PIC S9(4) COMP.
000800     05  CLMNOF                  PIC X.
000900     05  CLMNOI                  PIC X(14).
001000     05  POLNOL                  PIC S9(4) COMP.
001100     05  POLNOF                  PIC X.
001200     05  POLNOI                  PIC X(12).
001300     05  STATL                   PIC S9(4) COMP.
001400     05  STATF                   PIC X.
001500     05  STATI                   PIC X(03).
001600     05  LOSSDTL                 PIC S9(4) COMP.
001700     05  LOSSDTF                 PIC X.
001800     05  LOSSDTI                 PIC X(10).
001900     05  CAUSEL                  PIC S9(4) COMP.
002000     05  CAUSEF                  PIC X.
002100     05  CAUSEI                  PIC X(06).
002200     05  RESVL                   PIC S9(4) COMP.
002300     05  RESVF                   PIC X.
002400     05  RESVI                   PIC X(14).
002500     05  PAIDL                   PIC S9(4) COMP.
002600     05  PAIDF                   PIC X.
002700     05  PAIDI                   PIC X(14).
002800     05  FRAUDL                  PIC S9(4) COMP.
002900     05  FRAUDF                  PIC X.
003000     05  FRAUDA REDEFINES FRAUDF PIC X.
003100     05  FRAUDI                  PIC X(05).
003200     05  ADJL                    PIC S9(4) COMP.
003300     05  ADJF                    PIC X.
003400     05  ADJI                    PIC X(08).
003500     05  CLMTL                   PIC S9(4) COMP.
003600     05  CLMTF                   PIC X.
003700     05  CLMTI                   PIC X(40).
003800     05  MSGL                    PIC S9(4) COMP.
003900     05  MSGF                    PIC X.
004000     05  MSGI                    PIC X(60).
004100 01  CLMINQMO REDEFINES CLMINQMI.
004200     05  FILLER                  PIC X(12).
004300     05  FILLER                  PIC X(3).
004400     05  CLMNOO                  PIC X(14).
004500     05  FILLER                  PIC X(3).
004600     05  POLNOO                  PIC X(12).
004700     05  FILLER                  PIC X(3).
004800     05  STATO                   PIC X(03).
004900     05  FILLER                  PIC X(3).
005000     05  LOSSDTO                 PIC X(10).
005100     05  FILLER                  PIC X(3).
005200     05  CAUSEO                  PIC X(06).
005300     05  FILLER                  PIC X(3).
005400     05  RESVO                   PIC X(14).
005500     05  FILLER                  PIC X(3).
005600     05  PAIDO                   PIC X(14).
005700     05  FILLER                  PIC X(2).
005800     05  FRAUDC                  PIC X.
005900     05  FRAUDO                  PIC X(05).
006000     05  FILLER                  PIC X(3).
006100     05  ADJO                    PIC X(08).
006200     05  FILLER                  PIC X(3).
006300     05  CLMTO                   PIC X(40).
006400     05  FILLER                  PIC X(3).
006500     05  MSGO                    PIC X(60).
