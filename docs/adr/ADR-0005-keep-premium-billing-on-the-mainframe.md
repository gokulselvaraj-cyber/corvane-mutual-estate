# ADR-0005: Keep premium billing on the mainframe

- **Status:** Accepted
- **Date:** 2021-08-11
- **Deciders:** Platform architecture board

## Decision

Nightly premium billing (PRMNIGHT) stays in COBOL on the mainframe. The billing file is sent by SFTP to a landing host and loaded into the warehouse.

## Consequences

The billing rules stay in one place for now. The warehouse depends on a fixed-width file layout (BILLREC).
