"""Builder A, part 2: data/oracle, vendor SDK, generated TS client, contracts. Run: python3 -I a_core2.py <estate_root>"""
import os
import sys

ROOT = sys.argv[1]


def w(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.lstrip("\n"))


O = "data/oracle/"
w(O + "README.md", r'''
# LEDGER schema (Oracle 19c, PDB LEDGERPDB)

The policy premium ledger. policy-admin `LedgerClient` calls `PKG_POLICY_LEDGER.post_premium` when a policy is bound.
Owned by @corvane/policy-core.

| File | Contents |
|---|---|
| `01_ledger_tables.sql` | PARTY, POLICY_ACCOUNT, PREMIUM_POSTING, IPT_RETURN_LINE |
| `02_ledger_views.sql` | V_POLICY_BALANCE, V_IPT_QUARTER |
| `03_ledger_triggers.sql` | audit and balance triggers |
| `PKG_POLICY_LEDGER.pks/.pkb` | posting API |
| `LEDGER_ARCHIVE.pls` | 2019 archive procedure, kept for reference; not deployed since the 2022 partitioning change |

PARTY is the ledger's name for the policy holder (policy-admin `PolicyHolder`, COBOL `INSURED`, portal `Customer`).
''')

w(O + "01_ledger_tables.sql", r'''
-- LEDGER schema: premium ledger for bound policies.
-- PARTY = the policy holder. Same entity as policy-admin policy_holder (joined on PARTY_REF).

CREATE TABLE LEDGER.PARTY (
    PARTY_ID        NUMBER(12)      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    PARTY_REF       VARCHAR2(20)    NOT NULL,
    PARTY_TYPE      VARCHAR2(10)    DEFAULT 'PERSON' NOT NULL CHECK (PARTY_TYPE IN ('PERSON', 'BUSINESS')),
    DISPLAY_NAME    VARCHAR2(200)   NOT NULL,
    COUNTRY_CODE    CHAR(2)         DEFAULT 'GB' NOT NULL,
    TAX_REGION      VARCHAR2(2),
    CREATED_AT      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT UQ_PARTY_REF UNIQUE (PARTY_REF)
);

COMMENT ON TABLE LEDGER.PARTY IS 'Policy holder as known to the ledger. Name only; no NI number or date of birth here.';

CREATE TABLE LEDGER.POLICY_ACCOUNT (
    ACCOUNT_ID      NUMBER(12)      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    POLICY_NO       VARCHAR2(12)    NOT NULL,
    PARTY_ID        NUMBER(12)      NOT NULL REFERENCES LEDGER.PARTY (PARTY_ID),
    LINE_CODE       CHAR(3)         NOT NULL,
    CURRENCY        CHAR(3)         DEFAULT 'GBP' NOT NULL,
    BALANCE         NUMBER(13,2)    DEFAULT 0 NOT NULL,
    OPENED_ON       DATE            NOT NULL,
    STATUS          VARCHAR2(10)    DEFAULT 'OPEN' NOT NULL,
    CONSTRAINT UQ_POLICY_ACCOUNT UNIQUE (POLICY_NO)
);

CREATE TABLE LEDGER.PREMIUM_POSTING (
    POSTING_ID      NUMBER(14)      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ACCOUNT_ID      NUMBER(12)      NOT NULL REFERENCES LEDGER.POLICY_ACCOUNT (ACCOUNT_ID),
    POSTING_TYPE    VARCHAR2(12)    NOT NULL CHECK (POSTING_TYPE IN ('PREMIUM', 'IPT', 'REFUND', 'ADJUSTMENT')),
    AMOUNT          NUMBER(13,2)    NOT NULL,
    EFFECTIVE_DATE  DATE            NOT NULL,
    SOURCE_SYSTEM   VARCHAR2(20)    DEFAULT 'policy-admin' NOT NULL,
    POSTED_AT       TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL,
    POSTED_BY       VARCHAR2(30)    DEFAULT USER NOT NULL
)
PARTITION BY RANGE (EFFECTIVE_DATE) INTERVAL (NUMTOYMINTERVAL(1, 'MONTH'))
(PARTITION P_START VALUES LESS THAN (DATE '2022-01-01'));

CREATE TABLE LEDGER.IPT_RETURN_LINE (
    RETURN_QUARTER  CHAR(6)         NOT NULL,
    LINE_CODE       CHAR(3)         NOT NULL,
    IPT_RATE        NUMBER(4,3)     NOT NULL,
    TAXABLE_PREMIUM NUMBER(15,2)    NOT NULL,
    IPT_DUE         NUMBER(13,2)    NOT NULL,
    CONSTRAINT PK_IPT_RETURN_LINE PRIMARY KEY (RETURN_QUARTER, LINE_CODE)
);

CREATE TABLE LEDGER.POSTING_AUDIT (
    AUDIT_ID        NUMBER(14)      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    POSTING_ID      NUMBER(14)      NOT NULL,
    ACTION          VARCHAR2(10)    NOT NULL,
    OLD_AMOUNT      NUMBER(13,2),
    NEW_AMOUNT      NUMBER(13,2),
    CHANGED_BY      VARCHAR2(30)    NOT NULL,
    CHANGED_AT      TIMESTAMP       DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX LEDGER.IX_POSTING_ACCOUNT ON LEDGER.PREMIUM_POSTING (ACCOUNT_ID, EFFECTIVE_DATE);
CREATE INDEX LEDGER.IX_ACCOUNT_PARTY ON LEDGER.POLICY_ACCOUNT (PARTY_ID);
''')

w(O + "02_ledger_views.sql", r'''
CREATE OR REPLACE VIEW LEDGER.V_POLICY_BALANCE AS
SELECT a.POLICY_NO,
       a.LINE_CODE,
       p.PARTY_REF,
       p.DISPLAY_NAME,
       SUM(CASE WHEN pp.POSTING_TYPE = 'PREMIUM' THEN pp.AMOUNT ELSE 0 END) AS PREMIUM_POSTED,
       SUM(CASE WHEN pp.POSTING_TYPE = 'IPT' THEN pp.AMOUNT ELSE 0 END)     AS IPT_POSTED,
       SUM(CASE WHEN pp.POSTING_TYPE = 'REFUND' THEN pp.AMOUNT ELSE 0 END)  AS REFUNDED,
       a.BALANCE
  FROM LEDGER.POLICY_ACCOUNT a
  JOIN LEDGER.PARTY p ON p.PARTY_ID = a.PARTY_ID
  LEFT JOIN LEDGER.PREMIUM_POSTING pp ON pp.ACCOUNT_ID = a.ACCOUNT_ID
 GROUP BY a.POLICY_NO, a.LINE_CODE, p.PARTY_REF, p.DISPLAY_NAME, a.BALANCE;

-- Feeds the quarterly IPT return to the tax authority (finance team, not this repo).
CREATE OR REPLACE VIEW LEDGER.V_IPT_QUARTER AS
SELECT TO_CHAR(pp.EFFECTIVE_DATE, 'YYYY') || 'Q' || TO_CHAR(pp.EFFECTIVE_DATE, 'Q') AS RETURN_QUARTER,
       a.LINE_CODE,
       SUM(CASE WHEN pp.POSTING_TYPE = 'PREMIUM' THEN pp.AMOUNT ELSE 0 END) AS TAXABLE_PREMIUM,
       SUM(CASE WHEN pp.POSTING_TYPE = 'IPT' THEN pp.AMOUNT ELSE 0 END)     AS IPT_COLLECTED
  FROM LEDGER.PREMIUM_POSTING pp
  JOIN LEDGER.POLICY_ACCOUNT a ON a.ACCOUNT_ID = pp.ACCOUNT_ID
 WHERE a.CURRENCY = 'GBP'
 GROUP BY TO_CHAR(pp.EFFECTIVE_DATE, 'YYYY') || 'Q' || TO_CHAR(pp.EFFECTIVE_DATE, 'Q'), a.LINE_CODE;
''')

w(O + "03_ledger_triggers.sql", r'''
-- Triggers on the posting table. Postings are append-only: updates are audited, deletes are refused.
ALTER TABLE LEDGER.PREMIUM_POSTING ADD CONSTRAINT CK_POSTING_NONZERO CHECK (AMOUNT <> 0);

CREATE OR REPLACE TRIGGER LEDGER.TRG_POSTING_BALANCE
AFTER INSERT ON LEDGER.PREMIUM_POSTING
FOR EACH ROW
BEGIN
    UPDATE LEDGER.POLICY_ACCOUNT
       SET BALANCE = BALANCE + CASE WHEN :NEW.POSTING_TYPE = 'REFUND' THEN -ABS(:NEW.AMOUNT) ELSE :NEW.AMOUNT END
     WHERE ACCOUNT_ID = :NEW.ACCOUNT_ID;
END;
/

CREATE OR REPLACE TRIGGER LEDGER.TRG_POSTING_AUDIT
BEFORE UPDATE OR DELETE ON LEDGER.PREMIUM_POSTING
FOR EACH ROW
BEGIN
    IF DELETING THEN
        RAISE_APPLICATION_ERROR(-20010, 'Premium postings are append-only; post an ADJUSTMENT instead');
    END IF;
    INSERT INTO LEDGER.POSTING_AUDIT (POSTING_ID, ACTION, OLD_AMOUNT, NEW_AMOUNT, CHANGED_BY)
    VALUES (:OLD.POSTING_ID, 'UPDATE', :OLD.AMOUNT, :NEW.AMOUNT, USER);
END;
/
''')

w(O + "PKG_POLICY_LEDGER.pks", r'''
CREATE OR REPLACE PACKAGE LEDGER.PKG_POLICY_LEDGER AS
    -- Posting API for policy-admin (LedgerClient). One call per bound policy.

    E_UNKNOWN_LINE EXCEPTION;
    PRAGMA EXCEPTION_INIT(E_UNKNOWN_LINE, -20001);

    PROCEDURE post_premium (
        p_policy_no   IN  VARCHAR2,
        p_party_ref   IN  VARCHAR2,
        p_line_code   IN  CHAR,
        p_premium     IN  NUMBER,
        p_ipt         IN  NUMBER,
        p_currency    IN  CHAR,
        p_effective   IN  DATE,
        p_posting_id  OUT NUMBER
    );

    PROCEDURE post_refund (
        p_policy_no   IN  VARCHAR2,
        p_amount      IN  NUMBER,
        p_effective   IN  DATE
    );

    FUNCTION balance_of (p_policy_no IN VARCHAR2) RETURN NUMBER;
END PKG_POLICY_LEDGER;
/
''')

w(O + "PKG_POLICY_LEDGER.pkb", r'''
CREATE OR REPLACE PACKAGE BODY LEDGER.PKG_POLICY_LEDGER AS

    c_lines CONSTANT VARCHAR2(60) := 'MTR,HOM,CNT,TRV,PET,LLD,MAR,CPR,PLB,PIN,CYB,GDG';

    FUNCTION party_id_for (p_party_ref IN VARCHAR2) RETURN NUMBER IS
        v_id LEDGER.PARTY.PARTY_ID%TYPE;
    BEGIN
        SELECT PARTY_ID INTO v_id FROM LEDGER.PARTY WHERE PARTY_REF = p_party_ref;
        RETURN v_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            -- First posting for this holder: create the PARTY with a placeholder name; the nightly party sync
            -- from policy-admin fills DISPLAY_NAME.
            INSERT INTO LEDGER.PARTY (PARTY_REF, DISPLAY_NAME) VALUES (p_party_ref, '(pending sync)')
            RETURNING PARTY_ID INTO v_id;
            RETURN v_id;
    END party_id_for;

    FUNCTION account_for (p_policy_no IN VARCHAR2, p_party_id IN NUMBER, p_line IN CHAR,
                          p_currency IN CHAR, p_effective IN DATE) RETURN NUMBER IS
        v_id LEDGER.POLICY_ACCOUNT.ACCOUNT_ID%TYPE;
    BEGIN
        SELECT ACCOUNT_ID INTO v_id FROM LEDGER.POLICY_ACCOUNT WHERE POLICY_NO = p_policy_no;
        RETURN v_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            INSERT INTO LEDGER.POLICY_ACCOUNT (POLICY_NO, PARTY_ID, LINE_CODE, CURRENCY, OPENED_ON)
            VALUES (p_policy_no, p_party_id, p_line, p_currency, p_effective)
            RETURNING ACCOUNT_ID INTO v_id;
            RETURN v_id;
    END account_for;

    PROCEDURE post_premium (
        p_policy_no IN VARCHAR2, p_party_ref IN VARCHAR2, p_line_code IN CHAR, p_premium IN NUMBER,
        p_ipt IN NUMBER, p_currency IN CHAR, p_effective IN DATE, p_posting_id OUT NUMBER
    ) IS
        v_account NUMBER;
    BEGIN
        IF INSTR(c_lines, p_line_code) = 0 THEN
            RAISE_APPLICATION_ERROR(-20001, 'Unknown line code ' || p_line_code);
        END IF;
        v_account := account_for(p_policy_no, party_id_for(p_party_ref), p_line_code, p_currency, p_effective);
        INSERT INTO LEDGER.PREMIUM_POSTING (ACCOUNT_ID, POSTING_TYPE, AMOUNT, EFFECTIVE_DATE)
        VALUES (v_account, 'PREMIUM', p_premium - p_ipt, p_effective)
        RETURNING POSTING_ID INTO p_posting_id;
        IF p_ipt > 0 THEN
            INSERT INTO LEDGER.PREMIUM_POSTING (ACCOUNT_ID, POSTING_TYPE, AMOUNT, EFFECTIVE_DATE)
            VALUES (v_account, 'IPT', p_ipt, p_effective);
        END IF;
    END post_premium;

    PROCEDURE post_refund (p_policy_no IN VARCHAR2, p_amount IN NUMBER, p_effective IN DATE) IS
    BEGIN
        INSERT INTO LEDGER.PREMIUM_POSTING (ACCOUNT_ID, POSTING_TYPE, AMOUNT, EFFECTIVE_DATE)
        SELECT ACCOUNT_ID, 'REFUND', ABS(p_amount), p_effective
          FROM LEDGER.POLICY_ACCOUNT WHERE POLICY_NO = p_policy_no;
        IF SQL%ROWCOUNT = 0 THEN
            RAISE_APPLICATION_ERROR(-20002, 'No ledger account for ' || p_policy_no);
        END IF;
    END post_refund;

    FUNCTION balance_of (p_policy_no IN VARCHAR2) RETURN NUMBER IS
        v_balance NUMBER;
    BEGIN
        SELECT BALANCE INTO v_balance FROM LEDGER.POLICY_ACCOUNT WHERE POLICY_NO = p_policy_no;
        RETURN v_balance;
    END balance_of;

END PKG_POLICY_LEDGER;
/
''')

w(O + "LEDGER_ARCHIVE.pls", r'''
-- LEDGER_ARCHIVE: moved postings older than 7 years to LEDGER.PREMIUM_POSTING_ARCH.
-- Written 2019. NOT DEPLOYED since 2022, when PREMIUM_POSTING became interval-partitioned and old partitions are
-- dropped by the DBA job instead. Kept for audit reference only.
CREATE OR REPLACE PROCEDURE LEDGER.LEDGER_ARCHIVE (p_before IN DATE DEFAULT ADD_MONTHS(TRUNC(SYSDATE), -84)) AS
    CURSOR c_old IS
        SELECT POSTING_ID FROM LEDGER.PREMIUM_POSTING WHERE EFFECTIVE_DATE < p_before FOR UPDATE SKIP LOCKED;
    v_moved PLS_INTEGER := 0;
BEGIN
    FOR r IN c_old LOOP
        INSERT INTO LEDGER.PREMIUM_POSTING_ARCH SELECT * FROM LEDGER.PREMIUM_POSTING WHERE POSTING_ID = r.POSTING_ID;
        DELETE FROM LEDGER.PREMIUM_POSTING WHERE CURRENT OF c_old;
        v_moved := v_moved + 1;
        IF MOD(v_moved, 5000) = 0 THEN
            COMMIT;
        END IF;
    END LOOP;
    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Archived ' || v_moved || ' postings before ' || TO_CHAR(p_before, 'YYYY-MM-DD'));
END LEDGER_ARCHIVE;
/
''')

# ---------------- vendored SDK ----------------
V = "vendor/sentinel-exchange-sdk/"
VS = V + "src/main/java/com/sentinelexchange/sdk/"
w(V + "README.md", r'''
# Sentinel Claims Exchange Java SDK 2.0.3 — VENDORED COPY, DO NOT EDIT

Third-party SDK from Sentinel Exchange Ltd for the industry claims-history bureau (SOAP,
`https://soap.sentinel-exchange.example/ClaimsExchange`). Vendored into the Corvane estate because the vendor does not
publish to a Maven repository. Licence: see LICENSE.txt (proprietary, redistribution not permitted).

Used by claims-service `SentinelExchangeAdapter` only. Upgrade by replacing this folder with the vendor's release zip.

```java
SentinelClient client = SentinelClient.builder()
    .endpoint(SentinelClient.DEFAULT_ENDPOINT)
    .memberId("CORV01")
    .credentials(user, password)
    .timeout(Duration.ofSeconds(4))
    .maxRetries(1)
    .build();
SearchResult r = client.searchPriorClaims(new SearchRequest().withMember("CORV01"));
```
''')

w(V + "LICENSE.txt", r'''
Sentinel Exchange Ltd — SDK Licence Agreement v3 (summary)

Copyright (c) 2021-2026 Sentinel Exchange Ltd. All rights reserved.
This SDK is licensed, not sold, to exchange members for the sole purpose of calling the Sentinel Claims Exchange.
You may not modify, sublicense or redistribute the SDK outside your organisation. Provided "as is" without warranty.
''')

w(V + "CHANGELOG.md", r'''
# Changelog — Sentinel Claims Exchange Java SDK

## 2.0.3 (2026-03-02)
- Fix: `SoapTransport` now honours `maxRetries` on HTTP 503 only, not on SOAP faults.

## 2.0.0 (2025-09-15) — breaking
- **Renamed** `SentinelClient.searchClaims(SearchRequest)` to `searchPriorClaims(SearchRequest)`.
- **Renamed** result type `ClaimSearchResponse` to `SearchResult`; `getHits()` replaced by the public field `matches`.
- New `riskBand` (A–E) on `SearchResult`; `hasUndisclosedClaims()` is true for bands D and E.
- `lookbackYears` default changed from 3 to 5.
- Minimum Java version is now 17.

## 1.4.2 (2024-11-20)
- `searchClaims` accepts `vehicleRegistration` for motor searches.

## 1.4.0 (2024-06-01)
- Added `registerClaim` and `updateClaimStatus`.
- Credentials moved from a properties file to `Builder.credentials(user, password)`.
''')

w(V + "pom.xml", r'''
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.sentinelexchange</groupId>
  <artifactId>sentinel-exchange-sdk</artifactId>
  <version>2.0.3</version>
  <packaging>jar</packaging>
  <properties>
    <maven.compiler.release>17</maven.compiler.release>
  </properties>
  <dependencies>
    <dependency><groupId>jakarta.xml.bind</groupId><artifactId>jakarta.xml.bind-api</artifactId><version>4.0.1</version></dependency>
  </dependencies>
</project>
''')

w(VS + "SentinelClient.java", r'''
package com.sentinelexchange.sdk;

import com.sentinelexchange.sdk.model.ClaimStatus;
import com.sentinelexchange.sdk.model.SearchRequest;
import com.sentinelexchange.sdk.model.SearchResult;

import java.time.Duration;
import java.util.List;

/** Entry point of the Sentinel Claims Exchange SDK. Thread-safe; create one per application. */
public final class SentinelClient implements AutoCloseable {

    public static final String DEFAULT_ENDPOINT = "https://soap.sentinel-exchange.example/ClaimsExchange";

    private final SoapTransport transport;
    private final String memberId;

    private SentinelClient(Builder b) {
        this.memberId = b.memberId;
        this.transport = new SoapTransport(b.endpoint, b.username, b.password, b.timeout, b.maxRetries);
    }

    public static Builder builder() { return new Builder(); }

    /** Since 2.0 (was searchClaims in 1.x). Returns prior claims for the subject across member insurers. */
    public SearchResult searchPriorClaims(SearchRequest request) {
        if (request.memberId == null) {
            request.withMember(memberId);
        }
        request.validate();
        return transport.call("SearchPriorClaims", request, SearchResult.class);
    }

    public void updateClaimStatus(String exchangeRef, ClaimStatus status) {
        transport.call("UpdateClaimStatus", new Object[] {memberId, exchangeRef, status.name()}, Void.class);
    }

    public List<String> supportedLossTypes() {
        return List.of("MOTOR_ACCIDENT", "MOTOR_THEFT", "ESCAPE_OF_WATER", "FIRE", "THEFT", "STORM", "LIABILITY", "TRAVEL_MEDICAL");
    }

    @Override
    public void close() { transport.close(); }

    public static final class Builder {
        private String endpoint = DEFAULT_ENDPOINT;
        private String memberId;
        private String username;
        private String password;
        private Duration timeout = Duration.ofSeconds(10);
        private int maxRetries = 2;

        public Builder endpoint(String e) { this.endpoint = e; return this; }
        public Builder memberId(String m) { this.memberId = m; return this; }
        public Builder credentials(String user, String password) { this.username = user; this.password = password; return this; }
        public Builder timeout(Duration t) { this.timeout = t; return this; }
        public Builder maxRetries(int r) { this.maxRetries = r; return this; }

        public SentinelClient build() {
            if (memberId == null || username == null) {
                throw new SentinelException("memberId and credentials are required");
            }
            return new SentinelClient(this);
        }
    }
}
''')

w(VS + "SoapTransport.java", r'''
package com.sentinelexchange.sdk;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Base64;

/** Minimal SOAP 1.1 transport over java.net.http. Retries only on HTTP 503 (2.0.3). */
final class SoapTransport implements AutoCloseable {

    private final HttpClient http;
    private final URI endpoint;
    private final String authHeader;
    private final Duration timeout;
    private final int maxRetries;

    SoapTransport(String endpoint, String user, String password, Duration timeout, int maxRetries) {
        this.http = HttpClient.newBuilder().connectTimeout(timeout).build();
        this.endpoint = URI.create(endpoint);
        this.authHeader = "Basic " + Base64.getEncoder().encodeToString((user + ":" + password).getBytes(StandardCharsets.UTF_8));
        this.timeout = timeout;
        this.maxRetries = maxRetries;
    }

    <T> T call(String operation, Object body, Class<T> type) {
        String envelope = XmlCodec.envelope(operation, body);
        for (int attempt = 0; ; attempt++) {
            try {
                HttpResponse<String> r = http.send(HttpRequest.newBuilder(endpoint)
                        .timeout(timeout)
                        .header("Content-Type", "text/xml; charset=utf-8")
                        .header("SOAPAction", "urn:sentinel:claims:" + operation)
                        .header("Authorization", authHeader)
                        .POST(HttpRequest.BodyPublishers.ofString(envelope)).build(), HttpResponse.BodyHandlers.ofString());
                if (r.statusCode() == 503 && attempt < maxRetries) {
                    continue;
                }
                if (r.statusCode() >= 300) {
                    throw new SentinelException(operation + " failed with HTTP " + r.statusCode());
                }
                return XmlCodec.decode(r.body(), type);
            } catch (java.io.IOException e) {
                throw new SentinelException(operation + " transport error: " + e.getMessage());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new SentinelException(operation + " interrupted");
            }
        }
    }

    @Override
    public void close() { /* java.net.http.HttpClient has no close before Java 21 */ }
}
''')

w(VS + "XmlCodec.java", r'''
package com.sentinelexchange.sdk;

import jakarta.xml.bind.JAXB;
import java.io.StringReader;
import java.io.StringWriter;

final class XmlCodec {
    private XmlCodec() { }

    static String envelope(String operation, Object body) {
        StringWriter w = new StringWriter();
        JAXB.marshal(body, w);
        return "<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"><soap:Body><" + operation
                + " xmlns=\"urn:sentinel:claims:v2\">" + w + "</" + operation + "></soap:Body></soap:Envelope>";
    }

    static <T> T decode(String xml, Class<T> type) {
        return type == Void.class ? null : JAXB.unmarshal(new StringReader(xml), type);
    }
}
''')

w(VS + "SentinelException.java", r'''
package com.sentinelexchange.sdk;

public class SentinelException extends RuntimeException {
    public SentinelException(String message) { super(message); }
}
''')

w(VS + "model/SearchRequest.java", r'''
package com.sentinelexchange.sdk.model;

import com.sentinelexchange.sdk.SentinelException;
import java.time.LocalDate;

/** Search subject. At least surname + dateOfBirth, or vehicleRegistration, is required. Default lookback 5 years (2.0). */
public class SearchRequest {
    public String memberId;
    public String surname;
    public String forename;
    public LocalDate dateOfBirth;
    public String nationalId;
    public String postcode;
    public String vehicleRegistration;
    public int lookbackYears = 5;

    public SearchRequest withMember(String m) { this.memberId = m; return this; }

    public void validate() {
        boolean person = surname != null && dateOfBirth != null;
        if (!person && vehicleRegistration == null) {
            throw new SentinelException("surname and dateOfBirth, or vehicleRegistration, are required");
        }
        if (lookbackYears < 1 || lookbackYears > 10) {
            throw new SentinelException("lookbackYears must be 1..10");
        }
    }
}
''')

w(VS + "model/SearchResult.java", r'''
package com.sentinelexchange.sdk.model;

import java.util.ArrayList;
import java.util.List;

public class SearchResult {
    public String searchRef;
    public int matchCount;
    public List<PriorClaim> matches = new ArrayList<>();
    /** A (clean) to E (high risk). */
    public String riskBand;

    public boolean hasUndisclosedClaims() { return "D".equals(riskBand) || "E".equals(riskBand); }
}
''')

w(VS + "model/PriorClaim.java", r'''
package com.sentinelexchange.sdk.model;

import java.math.BigDecimal;
import java.time.LocalDate;

public class PriorClaim {
    public String exchangeRef;
    public String insurerCode;
    public String lossType;
    public LocalDate lossDate;
    public BigDecimal settledAmount;
    public ClaimStatus status;
    public int matchScore; // 0..100
}
''')

w(VS + "model/ClaimStatus.java", r'''
package com.sentinelexchange.sdk.model;

public enum ClaimStatus { OPEN, SETTLED, WITHDRAWN, REPUDIATED }
''')

# ---------------- generated TS client ----------------
G = "generated/policy-client-ts/"
HDR = '''/* tslint:disable */
/* eslint-disable */
/**
 * Corvane policy-admin API 4.12.0
 * Generated by OpenAPI Generator (typescript-fetch 7.4.0) from contracts/policy-admin.openapi.yaml.
 * DO NOT EDIT: regenerate with `npm run generate` in this folder.
 */
'''
w(G + "README.md", r'''
# @corvane/policy-client (generated)

TypeScript fetch client for policy-admin, **generated by OpenAPI Generator** from
`contracts/policy-admin.openapi.yaml`. Do not edit by hand; run `npm run generate`.
Consumed by `web/customer-portal`.
''')
w(G + "package.json", r'''
{
  "name": "@corvane/policy-client",
  "version": "4.12.0",
  "description": "Generated client for the Corvane policy-admin API. DO NOT EDIT.",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "generate": "openapi-generator-cli generate -i ../../contracts/policy-admin.openapi.yaml -g typescript-fetch -o .",
    "build": "tsc"
  },
  "devDependencies": {
    "@openapitools/openapi-generator-cli": "2.13.4",
    "typescript": "5.4.5"
  }
}
''')
w(G + "src/models.ts", HDR + r'''
export type ProductLine = 'MTR' | 'HOM' | 'CNT' | 'TRV' | 'PET' | 'LLD' | 'MAR' | 'CPR' | 'PLB' | 'PIN' | 'CYB' | 'GDG';

export interface QuoteRequest {
    line: ProductLine;
    fullName: string;
    dateOfBirth: string;
    postcode: string;
    sumInsured: number;
    voluntaryExcess?: number;
    priorClaims?: number;
    factors?: { [key: string]: string; };
}

export interface QuoteResponse {
    quoteId: string;
    line: ProductLine;
    premium: number;
    ipt: number;
    total: number;
    excess: number;
    referred: boolean;
    referralReason?: string | null;
    validUntil: string;
}

export interface BindRequest {
    inceptionDate?: string;
    brokerCode?: string;
}

export interface PolicyView {
    policyNumber: string;
    line: ProductLine;
    status: 'QUOTED' | 'BOUND' | 'LAPSED' | 'CANCELLED' | 'RENEWAL_DUE';
    partyRef: string;
    holderName: string;
    postcode: string;
    inceptionDate?: string;
    expiryDate?: string;
    annualPremium?: number;
    voluntaryExcess?: number;
    currency: string;
}

export interface Problem {
    type?: string;
    title?: string;
    status?: number;
    detail?: string;
}
''')
w(G + "src/runtime.ts", HDR + r'''
export interface ConfigurationParameters {
    basePath?: string;
    accessToken?: () => Promise<string>;
    fetchApi?: typeof fetch;
}

export class Configuration {
    constructor(private readonly params: ConfigurationParameters = {}) {}
    get basePath(): string { return this.params.basePath ?? 'https://api.corvane.internal/policy'; }
    get fetchApi(): typeof fetch { return this.params.fetchApi ?? fetch; }
    async token(): Promise<string | undefined> { return this.params.accessToken ? this.params.accessToken() : undefined; }
}

export class ResponseError extends Error {
    constructor(public response: Response, msg?: string) { super(msg ?? `HTTP ${response.status}`); }
}

export class BaseAPI {
    constructor(protected configuration = new Configuration()) {}

    protected async request<T>(method: string, path: string, body?: unknown): Promise<T> {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        const token = await this.configuration.token();
        if (token) { headers['Authorization'] = `Bearer ${token}`; }
        const response = await this.configuration.fetchApi(this.configuration.basePath + path, {
            method, headers, body: body === undefined ? undefined : JSON.stringify(body),
        });
        if (response.status >= 200 && response.status < 300) { return await response.json() as T; }
        throw new ResponseError(response, 'Response returned an error code');
    }
}
''')
w(G + "src/apis/QuotesApi.ts", HDR + r'''
import { BaseAPI } from '../runtime';
import type { QuoteRequest, QuoteResponse } from '../models';

export class QuotesApi extends BaseAPI {
    /** POST /v1/quotes — operationId createQuote */
    async createQuote(quoteRequest: QuoteRequest): Promise<QuoteResponse> {
        return this.request<QuoteResponse>('POST', '/v1/quotes', quoteRequest);
    }
}
''')
w(G + "src/apis/PoliciesApi.ts", HDR + r'''
import { BaseAPI } from '../runtime';
import type { BindRequest, PolicyView } from '../models';

export class PoliciesApi extends BaseAPI {
    /** GET /v1/policies/{policyNumber} — operationId getPolicy */
    async getPolicy(policyNumber: string): Promise<PolicyView> {
        return this.request<PolicyView>('GET', `/v1/policies/${encodeURIComponent(policyNumber)}`);
    }

    /** POST /v1/policies/{quoteId}/bind — operationId bindQuote */
    async bindQuote(quoteId: string, bindRequest: BindRequest): Promise<PolicyView> {
        return this.request<PolicyView>('POST', `/v1/policies/${encodeURIComponent(quoteId)}/bind`, bindRequest);
    }
}
''')
w(G + "src/index.ts", HDR + r'''
export * from './runtime';
export * from './models';
export * from './apis/QuotesApi';
export * from './apis/PoliciesApi';
''')

# ---------------- contracts ----------------
w("contracts/policy-admin.openapi.yaml", r'''
openapi: 3.0.3
info:
  title: Corvane policy-admin API
  version: 4.12.0
  description: Quote, bind and read policies. Owned by team-policy-core.
servers:
  - url: https://api.corvane.internal/policy
security:
  - bearerAuth: []
paths:
  /v1/quotes:
    post:
      operationId: createQuote
      tags: [Quotes]
      summary: Price a quote (J4). Roles CUSTOMER or BROKER.
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/QuoteRequest' }
      responses:
        '201':
          description: Priced quote, valid 30 days
          content:
            application/json:
              schema: { $ref: '#/components/schemas/QuoteResponse' }
        '400': { $ref: '#/components/responses/Problem' }
  /v1/policies/{policyNumber}:
    get:
      operationId: getPolicy
      tags: [Policies]
      summary: Read one policy. Used by claims-service during FNOL.
      parameters:
        - { name: policyNumber, in: path, required: true, schema: { type: string, pattern: '^[A-Z]{3}[0-9]{9}$' } }
      responses:
        '200':
          description: The policy
          content:
            application/json:
              schema: { $ref: '#/components/schemas/PolicyView' }
        '404': { $ref: '#/components/responses/Problem' }
  /v1/policies/{quoteId}/bind:
    post:
      operationId: bindQuote
      tags: [Policies]
      summary: Bind a quote into a policy; posts to the ledger and publishes policies.bound.v1.
      parameters:
        - { name: quoteId, in: path, required: true, schema: { type: string, format: uuid } }
      requestBody:
        content:
          application/json:
            schema: { $ref: '#/components/schemas/BindRequest' }
      responses:
        '201':
          description: Bound policy
          content:
            application/json:
              schema: { $ref: '#/components/schemas/PolicyView' }
        '409': { $ref: '#/components/responses/Problem' }
components:
  securitySchemes:
    bearerAuth: { type: http, scheme: bearer, bearerFormat: JWT }
  responses:
    Problem:
      description: RFC 7807 problem
      content:
        application/problem+json:
          schema: { $ref: '#/components/schemas/Problem' }
  schemas:
    ProductLine:
      type: string
      enum: [MTR, HOM, CNT, TRV, PET, LLD, MAR, CPR, PLB, PIN, CYB, GDG]
    QuoteRequest:
      type: object
      required: [line, fullName, dateOfBirth, postcode, sumInsured]
      properties:
        line: { $ref: '#/components/schemas/ProductLine' }
        fullName: { type: string }
        dateOfBirth: { type: string, format: date }
        postcode: { type: string, maxLength: 10 }
        sumInsured: { type: number, minimum: 1 }
        voluntaryExcess: { type: number, minimum: 0 }
        priorClaims: { type: integer, minimum: 0 }
        factors: { type: object, additionalProperties: { type: string } }
    QuoteResponse:
      type: object
      properties:
        quoteId: { type: string, format: uuid }
        line: { $ref: '#/components/schemas/ProductLine' }
        premium: { type: number }
        ipt: { type: number, description: 'Insurance Premium Tax: 12% standard, 20% for TRV and GDG' }
        total: { type: number }
        excess: { type: number, description: 'Compulsory 250 + voluntary' }
        referred: { type: boolean }
        referralReason: { type: string, nullable: true }
        validUntil: { type: string, format: date-time }
    BindRequest:
      type: object
      properties:
        inceptionDate: { type: string, format: date }
        brokerCode: { type: string }
    PolicyView:
      type: object
      properties:
        policyNumber: { type: string }
        line: { $ref: '#/components/schemas/ProductLine' }
        status: { type: string, enum: [QUOTED, BOUND, LAPSED, CANCELLED, RENEWAL_DUE] }
        partyRef: { type: string }
        holderName: { type: string }
        postcode: { type: string }
        inceptionDate: { type: string, format: date }
        expiryDate: { type: string, format: date }
        annualPremium: { type: number }
        voluntaryExcess: { type: number }
        currency: { type: string }
    Problem:
      type: object
      properties:
        type: { type: string }
        title: { type: string }
        status: { type: integer }
        detail: { type: string }
''')

w("contracts/sentinel-claims-exchange.wsdl", r'''
<?xml version="1.0" encoding="UTF-8"?>
<!-- Sentinel Claims Exchange v2 (third party). Copied from the vendor portal for reference; endpoint is external. -->
<wsdl:definitions xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
                  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                  xmlns:tns="urn:sentinel:claims:v2"
                  xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                  name="ClaimsExchange" targetNamespace="urn:sentinel:claims:v2">
  <wsdl:types>
    <xsd:schema targetNamespace="urn:sentinel:claims:v2">
      <xsd:include schemaLocation="sentinel-claims-exchange.xsd"/>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="SearchPriorClaimsRequest"><wsdl:part name="body" element="tns:SearchPriorClaims"/></wsdl:message>
  <wsdl:message name="SearchPriorClaimsResponse"><wsdl:part name="body" element="tns:SearchResult"/></wsdl:message>
  <wsdl:message name="UpdateClaimStatusRequest"><wsdl:part name="body" element="tns:UpdateClaimStatus"/></wsdl:message>
  <wsdl:message name="UpdateClaimStatusResponse"><wsdl:part name="body" element="tns:Ack"/></wsdl:message>
  <wsdl:portType name="ClaimsExchangePort">
    <wsdl:operation name="SearchPriorClaims">
      <wsdl:input message="tns:SearchPriorClaimsRequest"/>
      <wsdl:output message="tns:SearchPriorClaimsResponse"/>
    </wsdl:operation>
    <wsdl:operation name="UpdateClaimStatus">
      <wsdl:input message="tns:UpdateClaimStatusRequest"/>
      <wsdl:output message="tns:UpdateClaimStatusResponse"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="ClaimsExchangeBinding" type="tns:ClaimsExchangePort">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="SearchPriorClaims">
      <soap:operation soapAction="urn:sentinel:claims:SearchPriorClaims"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
    <wsdl:operation name="UpdateClaimStatus">
      <soap:operation soapAction="urn:sentinel:claims:UpdateClaimStatus"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="ClaimsExchangeService">
    <wsdl:port name="ClaimsExchangePort" binding="tns:ClaimsExchangeBinding">
      <soap:address location="https://soap.sentinel-exchange.example/ClaimsExchange"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
''')

w("contracts/sentinel-claims-exchange.xsd", r'''
<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:sentinel:claims:v2"
            xmlns:tns="urn:sentinel:claims:v2" elementFormDefault="qualified">
  <xsd:simpleType name="ClaimStatus">
    <xsd:restriction base="xsd:string">
      <xsd:enumeration value="OPEN"/><xsd:enumeration value="SETTLED"/>
      <xsd:enumeration value="WITHDRAWN"/><xsd:enumeration value="REPUDIATED"/>
    </xsd:restriction>
  </xsd:simpleType>
  <xsd:element name="SearchPriorClaims">
    <xsd:complexType><xsd:sequence>
      <xsd:element name="memberId" type="xsd:string"/>
      <xsd:element name="surname" type="xsd:string" minOccurs="0"/>
      <xsd:element name="forename" type="xsd:string" minOccurs="0"/>
      <xsd:element name="dateOfBirth" type="xsd:date" minOccurs="0"/>
      <xsd:element name="nationalId" type="xsd:string" minOccurs="0"/>
      <xsd:element name="postcode" type="xsd:string" minOccurs="0"/>
      <xsd:element name="vehicleRegistration" type="xsd:string" minOccurs="0"/>
      <xsd:element name="lookbackYears" type="xsd:int" default="5"/>
    </xsd:sequence></xsd:complexType>
  </xsd:element>
  <xsd:element name="SearchResult">
    <xsd:complexType><xsd:sequence>
      <xsd:element name="searchRef" type="xsd:string"/>
      <xsd:element name="matchCount" type="xsd:int"/>
      <xsd:element name="riskBand" type="xsd:string"/>
      <xsd:element name="matches" minOccurs="0" maxOccurs="unbounded">
        <xsd:complexType><xsd:sequence>
          <xsd:element name="exchangeRef" type="xsd:string"/>
          <xsd:element name="insurerCode" type="xsd:string"/>
          <xsd:element name="lossType" type="xsd:string"/>
          <xsd:element name="lossDate" type="xsd:date"/>
          <xsd:element name="settledAmount" type="xsd:decimal"/>
          <xsd:element name="status" type="tns:ClaimStatus"/>
          <xsd:element name="matchScore" type="xsd:int"/>
        </xsd:sequence></xsd:complexType>
      </xsd:element>
    </xsd:sequence></xsd:complexType>
  </xsd:element>
  <xsd:element name="UpdateClaimStatus">
    <xsd:complexType><xsd:sequence>
      <xsd:element name="memberId" type="xsd:string"/>
      <xsd:element name="exchangeRef" type="xsd:string"/>
      <xsd:element name="status" type="tns:ClaimStatus"/>
    </xsd:sequence></xsd:complexType>
  </xsd:element>
  <xsd:element name="Ack"><xsd:complexType><xsd:attribute name="ok" type="xsd:boolean"/></xsd:complexType></xsd:element>
</xsd:schema>
''')
print("a_core2 done")
