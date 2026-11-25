000100*================================================================
000200* BILLREC  DAILY BILLING FILE RECORD   CORV.PRM.BILLING.DAILY
000300*          FB LRECL=64, WRITTEN BY PRMBILL (PRMNIGHT STEP030)
000400*
000500* SENT BY SFTP TO /landing/billing/ (STEP040) AND LOADED BY
000600* warehouse-loader load_billing_file INTO dw.premium_billing_stage
000700* THEN dw.fn_merge_billing() INTO dw.premium_billing.
000800*
000900* LAYOUT (OFFSETS FROM 1):
001000*   1-12  POLICY-NO       X(12)
001100*  13-15  LINE-CODE       X(03)
001200*  16-23  BILL-DATE       9(08)   CCYYMMDD
001300*  24-34  PREMIUM-AMT     S9(09)V99 ZONED, SIGN OVERPUNCHED IN
001400*                                  THE LAST BYTE, 2 IMPLIED DP
001500*  35-43  IPT-AMT         S9(07)V99 ZONED, SAME SIGN RULE
001600*  44-46  CURRENCY        X(03)   GBP OR USD
001700*  47-48  REGION          X(02)   UK OR US
001800*  49-64  FILLER          X(16)   SPACES, RESERVED (2019)
001900* THE CURRENCY FIELD IS NAMED BILL-CURRENCY BELOW BECAUSE
002000* CURRENCY IS A COBOL RESERVED WORD.
002100* ANY CHANGE HERE BREAKS warehouse-loader AND THE dw LOAD.
002200*================================================================
002300 01  BILL-RECORD.
002400     05  POLICY-NO               PIC X(12).
002500     05  LINE-CODE               PIC X(03).
002600     05  BILL-DATE               PIC 9(08).
002700     05  PREMIUM-AMT             PIC S9(09)V99.
002800     05  IPT-AMT                 PIC S9(07)V99.
002900     05  BILL-CURRENCY           PIC X(03).
003000     05  REGION                  PIC X(02).
003100     05  FILLER                  PIC X(16).
