"""Builder A, part 1: services/policy-admin hand-written core. Run: python3 -I a_core1.py <estate_root>"""
import os
import sys

ROOT = sys.argv[1]
PA = "services/policy-admin/"
J = PA + "src/main/java/com/corvane/policy/"
T = PA + "src/test/java/com/corvane/policy/"
R = PA + "src/main/resources/"


def w(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.lstrip("\n"))


w(PA + "pom.xml", r'''
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.5</version>
    <relativePath/>
  </parent>
  <groupId>com.corvane</groupId>
  <artifactId>policy-admin</artifactId>
  <version>4.12.0</version>
  <name>policy-admin</name>
  <description>Corvane Mutual policy administration: quote, rate, bind, renew</description>
  <properties>
    <java.version>17</java.version>
    <jackson.version>2.17.1</jackson.version>
    <ctg.version>9.3.0</ctg.version>
  </properties>
  <dependencies>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-security</artifactId></dependency>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-oauth2-resource-server</artifactId></dependency>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-validation</artifactId></dependency>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-actuator</artifactId></dependency>
    <dependency><groupId>org.springframework.kafka</groupId><artifactId>spring-kafka</artifactId></dependency>
    <dependency><groupId>org.liquibase</groupId><artifactId>liquibase-core</artifactId></dependency>
    <dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId><version>${jackson.version}</version></dependency>
    <dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId><scope>runtime</scope></dependency>
    <dependency><groupId>com.oracle.database.jdbc</groupId><artifactId>ojdbc11</artifactId><version>23.3.0.23.09</version></dependency>
    <!-- IBM CICS Transaction Gateway client, used only by MainframePremiumAdapter -->
    <dependency><groupId>com.ibm.ctg</groupId><artifactId>ctgclient</artifactId><version>${ctg.version}</version></dependency>
    <dependency><groupId>io.github.resilience4j</groupId><artifactId>resilience4j-spring-boot3</artifactId><version>2.2.0</version></dependency>
    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-test</artifactId><scope>test</scope></dependency>
    <dependency><groupId>org.springframework.security</groupId><artifactId>spring-security-test</artifactId><scope>test</scope></dependency>
    <dependency><groupId>org.springframework.kafka</groupId><artifactId>spring-kafka-test</artifactId><scope>test</scope></dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin><groupId>org.springframework.boot</groupId><artifactId>spring-boot-maven-plugin</artifactId></plugin>
      <plugin><groupId>org.jacoco</groupId><artifactId>jacoco-maven-plugin</artifactId><version>0.8.11</version>
        <executions><execution><goals><goal>prepare-agent</goal></goals></execution>
          <execution><id>check</id><goals><goal>check</goal></goals>
            <configuration><rules><rule><limits><limit><counter>LINE</counter><value>COVEREDRATIO</value><minimum>0.80</minimum></limit></limits></rule></rules></configuration>
          </execution></executions></plugin>
    </plugins>
  </build>
</project>
''')

w(PA + "Dockerfile", r'''
FROM eclipse-temurin:17-jre-alpine
LABEL org.opencontainers.image.source="services/policy-admin" team="policy-core"
RUN addgroup -S corvane && adduser -S policy -G corvane
WORKDIR /app
COPY target/policy-admin-*.jar app.jar
USER policy
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/actuator/health/readiness || exit 1
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "/app/app.jar"]
''')

w(PA + "catalog-info.yaml", r'''
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: policy-admin
  description: Quotes, rates, binds and renews Corvane Mutual policies for all twelve product lines.
  annotations:
    corvane.io/runbook: ops/runbooks/policy-admin.md
  tags: [java, spring-boot, monolith]
spec:
  type: service
  lifecycle: production
  owner: team-policy-core
  system: corvane-insurance-platform
  providesApis: [policy-admin-api]
  consumesApis: [postcode-lookup-api]
  dependsOn:
    - resource:ledger-oracle
    - resource:policy-postgres
    - component:corvmf-premium-engine
---
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: policy-admin-api
spec:
  type: openapi
  lifecycle: production
  owner: team-policy-core
  system: corvane-insurance-platform
  definition:
    $text: ../../contracts/policy-admin.openapi.yaml
''')

w(PA + "README.md", r'''
# policy-admin

Layered Spring Boot monolith (controller → service → domain → repository) that owns the policy lifecycle for all
twelve Corvane product lines: **quote → rate → bind → renew**.

| Concern | Where |
|---|---|
| REST API | `api/QuoteController`, `api/PolicyController` (contract: `contracts/policy-admin.openapi.yaml`) |
| Rating | `service/RatingService` + per-line `rating/<Line>RatingRules` |
| Premium engine switch | `service/PremiumEngineRouter` reads `policy.premium-engine` (`java` or `mainframe`) |
| Ledger | `ledger/LedgerClient` calls Oracle `LEDGER.PKG_POLICY_LEDGER.post_premium` |
| Events | `events/PolicyEventPublisher` publishes `policies.bound.v1` |

## Premium engine (migration seam)
Until the mainframe rating engine (CICS program `PRMCALC0` behind CTG server `CORVCTG1`) is retired, production
keeps `policy.premium-engine: mainframe`. Dev and test run the Java port (`JavaRatingService`). See ADR-0009.

## Running locally
`docker compose up policy-admin` from the estate root, or `mvn spring-boot:run -Dspring-boot.run.profiles=dev`.
The service listens on **8080** in every environment.

## Renewals
`RenewalService` finds policies due in the next 30 days and prices them. Sending the renewal invitations is still
TODO (POL-1184); nothing is emailed yet.
''')

w(R + "application.yml", r'''
server:
  port: 8080
spring:
  application:
    name: policy-admin
  datasource:
    url: jdbc:postgresql://${POLICY_DB_HOST:localhost}:5432/policydb
    username: ${POLICY_DB_USER}
    password: ${POLICY_DB_PASSWORD}
  jpa:
    open-in-view: false
    hibernate:
      ddl-auto: validate
  liquibase:
    change-log: classpath:db/changelog/db.changelog-master.yaml
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP:localhost:9092}
    producer:
      acks: all
      properties:
        enable.idempotence: true
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://login.corvane.internal

policy:
  # Migration seam (ADR-0009): java | mainframe. Overridden per environment.
  premium-engine: java
  ipt:
    standard-rate: 0.12
    higher-rate: 0.20
    higher-rate-lines: [TRV, GDG]
  excess:
    compulsory: 250
  renewals:
    window-days: 30
  topics:
    bound: policies.bound.v1

ledger:
  url: jdbc:oracle:thin:@${LEDGER_DB_HOST}:1521/LEDGERPDB
  username: ${LEDGER_DB_USER}
  password: ${LEDGER_DB_PASSWORD}

ctg:
  server: CORVCTG1
  host: ${CTG_HOST}
  port: 2006
  program: PRMCALC0
  timeout-ms: 4000

postcode:
  base-url: https://postcode.lookup.example/v1
  api-key: ${POSTCODE_API_KEY}

management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus
  endpoint:
    health:
      probes:
        enabled: true
''')

w(R + "application-dev.yml", r'''
policy:
  premium-engine: java
spring:
  kafka:
    bootstrap-servers: kafka.dev.corvane.internal:9092
logging:
  level:
    com.corvane.policy: DEBUG
''')

w(R + "application-test.yml", r'''
policy:
  premium-engine: java
spring:
  kafka:
    bootstrap-servers: kafka.test.corvane.internal:9092
ctg:
  host: ctg.test.corvane.internal
''')

w(R + "application-prod.yml", r'''
# Production: the mainframe stays the rating engine of record until ADR-0009 step 3 signs off.
policy:
  premium-engine: mainframe
spring:
  kafka:
    bootstrap-servers: kafka.prod.corvane.internal:9092
ctg:
  host: ctg.prod.corvane.internal
  timeout-ms: 2500
resilience4j:
  circuitbreaker:
    instances:
      ctg:
        sliding-window-size: 20
        failure-rate-threshold: 50
        wait-duration-in-open-state: 30s
''')

w(R + "db/changelog/db.changelog-master.yaml", r'''
databaseChangeLog:
  - include:
      file: db/changelog/changes/001-policy.yaml
  - include:
      file: db/changelog/changes/002-quote.yaml
  - include:
      file: db/changelog/changes/010-rating-factors.yaml
''')

w(R + "db/changelog/changes/001-policy.yaml", r'''
databaseChangeLog:
  - changeSet:
      id: 001-policy-holder
      author: policy-core
      changes:
        - createTable:
            tableName: policy_holder
            remarks: "The insured person or business. Same party as LEDGER.PARTY and the COBOL INSURED-* fields."
            columns:
              - column: { name: id, type: BIGINT, autoIncrement: true, constraints: { primaryKey: true } }
              - column: { name: party_ref, type: VARCHAR(20), constraints: { nullable: false, unique: true } }
              - column: { name: full_name, type: VARCHAR(200), constraints: { nullable: false } }
              - column: { name: date_of_birth, type: DATE }
              - column: { name: national_id, type: VARCHAR(20), remarks: "UK NI number or US SSN (PII)" }
              - column: { name: email, type: VARCHAR(254) }
              - column: { name: address_line1, type: VARCHAR(120) }
              - column: { name: postcode, type: VARCHAR(10) }
              - column: { name: country, type: CHAR(2), defaultValue: GB }
  - changeSet:
      id: 001-policy
      author: policy-core
      changes:
        - createTable:
            tableName: policy
            columns:
              - column: { name: id, type: BIGINT, autoIncrement: true, constraints: { primaryKey: true } }
              - column: { name: policy_number, type: VARCHAR(12), constraints: { nullable: false, unique: true } }
              - column: { name: line_code, type: CHAR(3), constraints: { nullable: false } }
              - column: { name: holder_id, type: BIGINT, constraints: { nullable: false, foreignKeyName: fk_policy_holder, references: policy_holder(id) } }
              - column: { name: status, type: VARCHAR(12), constraints: { nullable: false } }
              - column: { name: inception_date, type: DATE }
              - column: { name: expiry_date, type: DATE }
              - column: { name: annual_premium, type: DECIMAL(11,2) }
              - column: { name: ipt_amount, type: DECIMAL(9,2) }
              - column: { name: voluntary_excess, type: DECIMAL(9,2), defaultValueNumeric: 0 }
              - column: { name: currency, type: CHAR(3), defaultValue: GBP }
              - column: { name: premium_engine, type: VARCHAR(10), remarks: "java or mainframe: which engine priced it" }
        - createIndex:
            tableName: policy
            indexName: ix_policy_expiry
            columns: [ { column: { name: expiry_date } } ]
''')

w(R + "db/changelog/changes/002-quote.yaml", r'''
databaseChangeLog:
  - changeSet:
      id: 002-quote
      author: policy-core
      changes:
        - createTable:
            tableName: quote
            columns:
              - column: { name: id, type: VARCHAR(36), constraints: { primaryKey: true } }
              - column: { name: line_code, type: CHAR(3), constraints: { nullable: false } }
              - column: { name: holder_id, type: BIGINT, constraints: { foreignKeyName: fk_quote_holder, references: policy_holder(id) } }
              - column: { name: base_premium, type: DECIMAL(11,2) }
              - column: { name: total_premium, type: DECIMAL(11,2) }
              - column: { name: ipt_amount, type: DECIMAL(9,2) }
              - column: { name: excess_total, type: DECIMAL(9,2) }
              - column: { name: referral_reason, type: VARCHAR(200) }
              - column: { name: valid_until, type: TIMESTAMP }
              - column: { name: bound_policy_id, type: BIGINT, constraints: { foreignKeyName: fk_quote_policy, references: policy(id) } }
''')

# ---------------- Java main ----------------
w(J + "PolicyAdminApplication.java", r'''
package com.corvane.policy;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@ConfigurationPropertiesScan
@EnableScheduling
public class PolicyAdminApplication {
    public static void main(String[] args) {
        SpringApplication.run(PolicyAdminApplication.class, args);
    }
}
''')

w(J + "domain/ProductLine.java", r'''
package com.corvane.policy.domain;

/** The twelve Corvane product lines. The three-letter code is shared with the mainframe (POLREC LINE-CODE). */
public enum ProductLine {
    MTR("Motor"), HOM("Home buildings"), CNT("Home contents"), TRV("Travel"), PET("Pet"), LLD("Landlord"),
    MAR("Marine cargo"), CPR("Commercial property"), PLB("Public liability"), PIN("Professional indemnity"),
    CYB("Cyber"), GDG("Gadget");

    private final String label;

    ProductLine(String label) { this.label = label; }

    public String label() { return label; }
}
''')

w(J + "domain/PolicyStatus.java", r'''
package com.corvane.policy.domain;

public enum PolicyStatus { QUOTED, BOUND, LAPSED, CANCELLED, RENEWAL_DUE }
''')

w(J + "domain/PolicyHolder.java", r'''
package com.corvane.policy.domain;

import jakarta.persistence.*;
import java.time.LocalDate;

/**
 * The person or business that holds a policy.
 *
 * <p>Naming across the estate: the mainframe calls this the INSURED (copybook POLREC, INSURED-NAME), the Oracle
 * ledger calls it a PARTY, the customer portal calls it a Customer and claims-service stores it as the
 * policyholder row of claims.claim_party. They are the same real-world entity, joined on {@code partyRef}.</p>
 */
@Entity
@Table(name = "policy_holder")
public class PolicyHolder {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "party_ref", nullable = false, unique = true)
    private String partyRef;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    @Column(name = "date_of_birth")
    private LocalDate dateOfBirth;

    /** UK National Insurance number or US SSN. Personal data: masked in every log line. */
    @Column(name = "national_id")
    private String nationalId;

    private String email;

    @Column(name = "address_line1")
    private String addressLine1;

    private String postcode;
    private String country = "GB";

    protected PolicyHolder() { }

    public PolicyHolder(String partyRef, String fullName, LocalDate dateOfBirth, String postcode) {
        this.partyRef = partyRef;
        this.fullName = fullName;
        this.dateOfBirth = dateOfBirth;
        this.postcode = postcode;
    }

    public Long getId() { return id; }
    public String getPartyRef() { return partyRef; }
    public String getFullName() { return fullName; }
    public LocalDate getDateOfBirth() { return dateOfBirth; }
    public String getNationalId() { return nationalId; }
    public void setNationalId(String nationalId) { this.nationalId = nationalId; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getAddressLine1() { return addressLine1; }
    public void setAddressLine1(String a) { this.addressLine1 = a; }
    public String getPostcode() { return postcode; }
    public String getCountry() { return country; }
    public void setCountry(String country) { this.country = country; }

    public String maskedNationalId() {
        return nationalId == null || nationalId.length() < 4 ? "****" : "****" + nationalId.substring(nationalId.length() - 3);
    }
}
''')

w(J + "domain/Policy.java", r'''
package com.corvane.policy.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * An insurance policy: the contract between Corvane and a {@link PolicyHolder} for one product line.
 *
 * <p>Not to be confused with {@code com.corvane.claims.security.Policy} in claims-service, which is an
 * access-control policy and has nothing to do with insurance cover.</p>
 */
@Entity
@Table(name = "policy")
public class Policy {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "policy_number", nullable = false, unique = true, length = 12)
    private String policyNumber;

    @Enumerated(EnumType.STRING)
    @Column(name = "line_code", nullable = false, length = 3)
    private ProductLine line;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "holder_id")
    private PolicyHolder holder;

    @Enumerated(EnumType.STRING)
    private PolicyStatus status = PolicyStatus.QUOTED;

    @Column(name = "inception_date") private LocalDate inceptionDate;
    @Column(name = "expiry_date") private LocalDate expiryDate;
    @Column(name = "annual_premium") private BigDecimal annualPremium;
    @Column(name = "ipt_amount") private BigDecimal iptAmount;
    @Column(name = "voluntary_excess") private BigDecimal voluntaryExcess = BigDecimal.ZERO;
    private String currency = "GBP";
    @Column(name = "premium_engine") private String premiumEngine;

    protected Policy() { }

    public Policy(String policyNumber, ProductLine line, PolicyHolder holder) {
        this.policyNumber = policyNumber;
        this.line = line;
        this.holder = holder;
    }

    public void bind(LocalDate inception, BigDecimal premium, BigDecimal ipt, String engine) {
        if (status != PolicyStatus.QUOTED) {
            throw new IllegalStateException("Policy " + policyNumber + " is " + status + ", only QUOTED can be bound");
        }
        this.inceptionDate = inception;
        this.expiryDate = inception.plusYears(1).minusDays(1);
        this.annualPremium = premium;
        this.iptAmount = ipt;
        this.premiumEngine = engine;
        this.status = PolicyStatus.BOUND;
    }

    public void markRenewalDue() { this.status = PolicyStatus.RENEWAL_DUE; }

    public Long getId() { return id; }
    public String getPolicyNumber() { return policyNumber; }
    public ProductLine getLine() { return line; }
    public PolicyHolder getHolder() { return holder; }
    public PolicyStatus getStatus() { return status; }
    public LocalDate getInceptionDate() { return inceptionDate; }
    public LocalDate getExpiryDate() { return expiryDate; }
    public BigDecimal getAnnualPremium() { return annualPremium; }
    public BigDecimal getIptAmount() { return iptAmount; }
    public BigDecimal getVoluntaryExcess() { return voluntaryExcess; }
    public void setVoluntaryExcess(BigDecimal v) { this.voluntaryExcess = v; }
    public String getCurrency() { return currency; }
    public String getPremiumEngine() { return premiumEngine; }
}
''')

w(J + "domain/Quote.java", r'''
package com.corvane.policy.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "quote")
public class Quote {

    @Id
    private String id = UUID.randomUUID().toString();

    @Enumerated(EnumType.STRING)
    @Column(name = "line_code", length = 3)
    private ProductLine line;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "holder_id")
    private PolicyHolder holder;

    @Column(name = "base_premium") private BigDecimal basePremium;
    @Column(name = "total_premium") private BigDecimal totalPremium;
    @Column(name = "ipt_amount") private BigDecimal iptAmount;
    @Column(name = "excess_total") private BigDecimal excessTotal;
    @Column(name = "referral_reason") private String referralReason;
    @Column(name = "valid_until") private Instant validUntil;
    @Column(name = "bound_policy_id") private Long boundPolicyId;

    protected Quote() { }

    public Quote(ProductLine line, PolicyHolder holder, RatingResult r, Instant validUntil) {
        this.line = line;
        this.holder = holder;
        this.basePremium = r.basePremium();
        this.totalPremium = r.totalPremium();
        this.iptAmount = r.ipt();
        this.excessTotal = r.excessTotal();
        this.referralReason = r.referralReason();
        this.validUntil = validUntil;
    }

    public boolean isReferred() { return referralReason != null; }
    public boolean isExpired(Instant now) { return now.isAfter(validUntil); }
    public void markBound(Long policyId) { this.boundPolicyId = policyId; }

    public String getId() { return id; }
    public ProductLine getLine() { return line; }
    public PolicyHolder getHolder() { return holder; }
    public BigDecimal getBasePremium() { return basePremium; }
    public BigDecimal getTotalPremium() { return totalPremium; }
    public BigDecimal getIptAmount() { return iptAmount; }
    public BigDecimal getExcessTotal() { return excessTotal; }
    public String getReferralReason() { return referralReason; }
    public Instant getValidUntil() { return validUntil; }
    public Long getBoundPolicyId() { return boundPolicyId; }
}
''')

w(J + "domain/RatingResult.java", r'''
package com.corvane.policy.domain;

import java.math.BigDecimal;

/** What a premium engine returns. {@code engine} is "java" or "mainframe" so the policy records who priced it. */
public record RatingResult(BigDecimal basePremium, BigDecimal ipt, BigDecimal totalPremium,
                           BigDecimal excessTotal, String referralReason, String engine) {
}
''')

w(J + "domain/RatingInput.java", r'''
package com.corvane.policy.domain;

import java.math.BigDecimal;
import java.util.Map;

/** Risk facts captured by the quote form. {@code factors} holds the line-specific answers (e.g. vehicleAge). */
public record RatingInput(ProductLine line, String postcode, int holderAge, BigDecimal sumInsured,
                          BigDecimal voluntaryExcess, int priorClaims, Map<String, String> factors) {
}
''')

w(J + "repository/PolicyRepository.java", r'''
package com.corvane.policy.repository;

import com.corvane.policy.domain.Policy;
import com.corvane.policy.domain.PolicyStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface PolicyRepository extends JpaRepository<Policy, Long> {

    Optional<Policy> findByPolicyNumber(String policyNumber);

    @Query("select p from Policy p where p.status = :status and p.expiryDate between :from and :to")
    List<Policy> findExpiring(PolicyStatus status, LocalDate from, LocalDate to);

    @Query(value = "select nextval('policy_number_seq')", nativeQuery = true)
    long nextPolicySequence();
}
''')

w(J + "repository/QuoteRepository.java", r'''
package com.corvane.policy.repository;

import com.corvane.policy.domain.Quote;
import org.springframework.data.jpa.repository.JpaRepository;

public interface QuoteRepository extends JpaRepository<Quote, String> {
}
''')

w(J + "repository/PolicyHolderRepository.java", r'''
package com.corvane.policy.repository;

import com.corvane.policy.domain.PolicyHolder;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface PolicyHolderRepository extends JpaRepository<PolicyHolder, Long> {
    Optional<PolicyHolder> findByPartyRef(String partyRef);
}
''')

w(J + "api/QuoteController.java", r'''
package com.corvane.policy.api;

import com.corvane.policy.api.dto.QuoteRequest;
import com.corvane.policy.api.dto.QuoteResponse;
import com.corvane.policy.service.QuoteService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

/** J4 entry point: the customer portal's QuotePage posts here. */
@RestController
@RequestMapping("/v1/quotes")
public class QuoteController {

    private final QuoteService quoteService;

    public QuoteController(QuoteService quoteService) {
        this.quoteService = quoteService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('CUSTOMER','BROKER')")
    public QuoteResponse quote(@Valid @RequestBody QuoteRequest request) {
        return QuoteResponse.from(quoteService.quote(request));
    }
}
''')

w(J + "api/PolicyController.java", r'''
package com.corvane.policy.api;

import com.corvane.policy.api.dto.BindRequest;
import com.corvane.policy.api.dto.PolicyView;
import com.corvane.policy.service.PolicyService;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/v1/policies")
public class PolicyController {

    private final PolicyService policyService;

    public PolicyController(PolicyService policyService) {
        this.policyService = policyService;
    }

    /** Called by claims-service PolicyAdminClient.getPolicy during FNOL (J1) and by the portal's PolicyView. */
    @GetMapping("/{policyNumber}")
    @PreAuthorize("hasAnyRole('CUSTOMER','ADJUSTER','CLAIMS_MANAGER','BROKER')")
    public PolicyView get(@PathVariable String policyNumber) {
        return PolicyView.from(policyService.find(policyNumber));
    }

    /** J4: bind an accepted quote into a live policy. */
    @PostMapping("/{quoteId}/bind")
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('CUSTOMER','BROKER')")
    public PolicyView bind(@PathVariable String quoteId, @RequestBody BindRequest request) {
        return PolicyView.from(policyService.bind(quoteId, request.inceptionDate(), request.brokerCode()));
    }
}
''')

w(J + "api/ApiExceptionHandler.java", r'''
package com.corvane.policy.api;

import com.corvane.policy.service.QuoteNotBindableException;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(EntityNotFoundException.class)
    ProblemDetail notFound(EntityNotFoundException e) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, e.getMessage());
    }

    @ExceptionHandler(QuoteNotBindableException.class)
    ProblemDetail notBindable(QuoteNotBindableException e) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, e.getMessage());
    }
}
''')

w(J + "api/dto/QuoteRequest.java", r'''
package com.corvane.policy.api.dto;

import com.corvane.policy.domain.ProductLine;
import jakarta.validation.constraints.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Map;

public record QuoteRequest(
        @NotNull ProductLine line,
        @NotBlank String fullName,
        @NotNull @Past LocalDate dateOfBirth,
        @NotBlank @Size(max = 10) String postcode,
        @NotNull @Positive BigDecimal sumInsured,
        @PositiveOrZero BigDecimal voluntaryExcess,
        @PositiveOrZero int priorClaims,
        Map<String, String> factors) {
}
''')

w(J + "api/dto/QuoteResponse.java", r'''
package com.corvane.policy.api.dto;

import com.corvane.policy.domain.Quote;
import java.math.BigDecimal;
import java.time.Instant;

public record QuoteResponse(String quoteId, String line, BigDecimal premium, BigDecimal ipt, BigDecimal total,
                            BigDecimal excess, boolean referred, String referralReason, Instant validUntil) {

    public static QuoteResponse from(Quote q) {
        return new QuoteResponse(q.getId(), q.getLine().name(), q.getBasePremium(), q.getIptAmount(),
                q.getTotalPremium(), q.getExcessTotal(), q.isReferred(), q.getReferralReason(), q.getValidUntil());
    }
}
''')

w(J + "api/dto/BindRequest.java", r'''
package com.corvane.policy.api.dto;

import java.time.LocalDate;

public record BindRequest(LocalDate inceptionDate, String brokerCode) {
}
''')

w(J + "api/dto/PolicyView.java", r'''
package com.corvane.policy.api.dto;

import com.corvane.policy.domain.Policy;
import java.math.BigDecimal;
import java.time.LocalDate;

/** What claims-service and the portal see. National ID is never exposed; only the holder's party ref. */
public record PolicyView(String policyNumber, String line, String status, String partyRef, String holderName,
                         String postcode, LocalDate inceptionDate, LocalDate expiryDate, BigDecimal annualPremium,
                         BigDecimal voluntaryExcess, String currency) {

    public static PolicyView from(Policy p) {
        return new PolicyView(p.getPolicyNumber(), p.getLine().name(), p.getStatus().name(),
                p.getHolder().getPartyRef(), p.getHolder().getFullName(), p.getHolder().getPostcode(),
                p.getInceptionDate(), p.getExpiryDate(), p.getAnnualPremium(), p.getVoluntaryExcess(), p.getCurrency());
    }
}
''')

w(J + "service/QuoteNotBindableException.java", r'''
package com.corvane.policy.service;

public class QuoteNotBindableException extends RuntimeException {
    public QuoteNotBindableException(String message) { super(message); }
}
''')

w(J + "service/QuoteService.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.api.dto.QuoteRequest;
import com.corvane.policy.domain.*;
import com.corvane.policy.repository.PolicyHolderRepository;
import com.corvane.policy.repository.QuoteRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.Duration;
import java.time.LocalDate;
import java.time.Period;
import java.util.Map;
import java.util.UUID;

/** J4 step 2: turns a quote request into a priced, stored quote valid for 30 days. */
@Service
public class QuoteService {

    static final Duration QUOTE_VALIDITY = Duration.ofDays(30);

    private final RatingService ratingService;
    private final PostcodeLookupClient postcodes;
    private final PolicyHolderRepository holders;
    private final QuoteRepository quotes;
    private final Clock clock;

    public QuoteService(RatingService ratingService, PostcodeLookupClient postcodes, PolicyHolderRepository holders,
                        QuoteRepository quotes, Clock clock) {
        this.ratingService = ratingService;
        this.postcodes = postcodes;
        this.holders = holders;
        this.quotes = quotes;
        this.clock = clock;
    }

    @Transactional
    public Quote quote(QuoteRequest req) {
        String postcode = postcodes.normalise(req.postcode());
        int age = Period.between(req.dateOfBirth(), LocalDate.now(clock)).getYears();
        PolicyHolder holder = holders.save(new PolicyHolder("PTY" + UUID.randomUUID().toString().substring(0, 12).toUpperCase(),
                req.fullName(), req.dateOfBirth(), postcode));
        RatingInput input = new RatingInput(req.line(), postcode, age, req.sumInsured(),
                req.voluntaryExcess() == null ? BigDecimal.ZERO : req.voluntaryExcess(), req.priorClaims(),
                req.factors() == null ? Map.of() : req.factors());
        RatingResult result = ratingService.rate(input);
        return quotes.save(new Quote(req.line(), holder, result, clock.instant().plus(QUOTE_VALIDITY)));
    }
}
''')

w(J + "service/RatingService.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import com.corvane.policy.domain.RatingResult;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

/**
 * J4 step 3: rating. Delegates the base premium to whichever engine {@link PremiumEngineRouter} selects, then
 * applies the rules Corvane keeps outside both engines: excess and Insurance Premium Tax (IPT).
 *
 * <p>The excess rule is duplicated elsewhere: COBOL PRMCALC paragraph 3000-APPLY-EXCESS and claims-service
 * ClaimSettlementCalculator.applyExcess. Keep them in step (POL-977).</p>
 */
@Service
public class RatingService {

    /** Compulsory excess in GBP, added to the customer's voluntary excess. */
    public static final BigDecimal COMPULSORY_EXCESS = new BigDecimal("250");

    private final PremiumEngineRouter router;
    private final BigDecimal iptStandard;
    private final BigDecimal iptHigher;
    private final List<String> higherRateLines;

    public RatingService(PremiumEngineRouter router,
                         @Value("${policy.ipt.standard-rate}") BigDecimal iptStandard,
                         @Value("${policy.ipt.higher-rate}") BigDecimal iptHigher,
                         @Value("${policy.ipt.higher-rate-lines}") List<String> higherRateLines) {
        this.router = router;
        this.iptStandard = iptStandard;
        this.iptHigher = iptHigher;
        this.higherRateLines = higherRateLines;
    }

    public RatingResult rate(RatingInput input) {
        PremiumEngine engine = router.select();
        PremiumEngine.Priced priced = engine.price(input);
        BigDecimal base = priced.basePremium().setScale(2, RoundingMode.HALF_UP);
        BigDecimal ipt = base.multiply(iptRate(input.line())).setScale(2, RoundingMode.HALF_UP);
        BigDecimal excess = applyExcess(input.voluntaryExcess());
        return new RatingResult(base, ipt, base.add(ipt), excess, priced.referralReason(), engine.name());
    }

    /**
     * Total excess = compulsory 250 + voluntary, rounded HALF_UP to whole pounds.
     * (claims-service rounds DOWN and the mainframe still uses a compulsory 200.)
     */
    public BigDecimal applyExcess(BigDecimal voluntary) {
        BigDecimal v = voluntary == null ? BigDecimal.ZERO : voluntary.max(BigDecimal.ZERO);
        return COMPULSORY_EXCESS.add(v).setScale(0, RoundingMode.HALF_UP);
    }

    BigDecimal iptRate(ProductLine line) {
        return higherRateLines.contains(line.name()) ? iptHigher : iptStandard;
    }
}
''')

w(J + "service/PremiumEngine.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.RatingInput;
import java.math.BigDecimal;

/** A base-premium engine. Two implementations: the Java port and the mainframe adapter (ADR-0009). */
public interface PremiumEngine {

    record Priced(BigDecimal basePremium, String referralReason) { }

    String name();

    Priced price(RatingInput input);
}
''')

w(J + "service/PremiumEngineRouter.java", r'''
package com.corvane.policy.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Migration seam (ADR-0009 "strangle the mainframe rating engine").
 *
 * <p>{@code policy.premium-engine} chooses the engine at runtime: {@code mainframe} sends the request through the
 * CICS Transaction Gateway to PRMCALC0; {@code java} uses the Java port. Profiles: dev=java, test=java,
 * prod=mainframe.</p>
 */
@Component
public class PremiumEngineRouter {

    private static final Logger log = LoggerFactory.getLogger(PremiumEngineRouter.class);

    private final JavaRatingService javaEngine;
    private final MainframePremiumAdapter mainframeEngine;
    private final String selected;

    public PremiumEngineRouter(JavaRatingService javaEngine, MainframePremiumAdapter mainframeEngine,
                               @Value("${policy.premium-engine:java}") String selected) {
        this.javaEngine = javaEngine;
        this.mainframeEngine = mainframeEngine;
        this.selected = selected;
        log.info("Premium engine selected: {}", selected);
    }

    public PremiumEngine select() {
        return switch (selected) {
            case "mainframe" -> mainframeEngine;
            case "java" -> javaEngine;
            default -> throw new IllegalStateException("Unknown policy.premium-engine: " + selected);
        };
    }
}
''')

w(J + "service/JavaRatingService.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import com.corvane.policy.rating.LineRatingRules;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/** The Java port of the mainframe rating engine: one {@link LineRatingRules} per product line. */
@Service
public class JavaRatingService implements PremiumEngine {

    private final Map<ProductLine, LineRatingRules> rules = new EnumMap<>(ProductLine.class);

    public JavaRatingService(List<LineRatingRules> all) {
        all.forEach(r -> rules.put(r.line(), r));
    }

    @Override
    public String name() { return "java"; }

    @Override
    public Priced price(RatingInput input) {
        LineRatingRules r = rules.get(input.line());
        if (r == null) {
            throw new IllegalArgumentException("No Java rating rules for line " + input.line());
        }
        BigDecimal premium = r.basePremium(input);
        return new Priced(premium, r.referralReason(input).orElse(null));
    }
}
''')

w(J + "service/MainframePremiumAdapter.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.RatingInput;
import com.ibm.ctg.client.ECIRequest;
import com.ibm.ctg.client.JavaGateway;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.charset.Charset;

/**
 * Calls the mainframe rating engine: CICS program PRMCALC0 on CTG server CORVCTG1, COMMAREA layout PRMCOMM.
 * The COMMAREA is EBCDIC (cp037); amounts come back as zoned decimal with two implied decimals.
 */
@Component
public class MainframePremiumAdapter implements PremiumEngine {

    static final int COMMAREA_LENGTH = 200;
    private static final Charset EBCDIC = Charset.forName("Cp037");

    private final String host;
    private final int port;
    private final String server;
    private final String program;
    private final int timeoutMs;

    public MainframePremiumAdapter(@Value("${ctg.host}") String host, @Value("${ctg.port}") int port,
                                   @Value("${ctg.server}") String server, @Value("${ctg.program}") String program,
                                   @Value("${ctg.timeout-ms}") int timeoutMs) {
        this.host = host;
        this.port = port;
        this.server = server;
        this.program = program;
        this.timeoutMs = timeoutMs;
    }

    @Override
    public String name() { return "mainframe"; }

    @Override
    @CircuitBreaker(name = "ctg")
    public Priced price(RatingInput input) {
        byte[] commarea = toCommarea(input);
        try {
            JavaGateway gateway = new JavaGateway(host, port);
            try {
                ECIRequest req = new ECIRequest(ECIRequest.ECI_SYNC, server, null, null, program, null,
                        commarea, COMMAREA_LENGTH, ECIRequest.ECI_NO_EXTEND, 0);
                req.setECITimeout((short) (timeoutMs / 1000));
                gateway.flow(req);
                if (req.getCicsRc() != 0) {
                    throw new MainframeRatingException("PRMCALC0 returned CICS rc " + req.getCicsRc());
                }
                return fromCommarea(req.Commarea);
            } finally {
                gateway.close();
            }
        } catch (IOException e) {
            throw new MainframeRatingException("CTG " + server + " unreachable: " + e.getMessage());
        }
    }

    /** PRMCOMM: LINE-CODE X(3), POSTCODE X(8), HOLDER-AGE 9(3), SUM-INSURED 9(9)V99, VOL-EXCESS 9(5)V99, PRIOR-CLAIMS 9(2). */
    byte[] toCommarea(RatingInput in) {
        String s = String.format("%-3s%-8s%03d%011d%07d%02d", in.line().name(), in.postcode(), in.holderAge(),
                in.sumInsured().movePointRight(2).longValue(), in.voluntaryExcess().movePointRight(2).longValue(),
                Math.min(in.priorClaims(), 99));
        byte[] out = new byte[COMMAREA_LENGTH];
        byte[] b = s.getBytes(EBCDIC);
        System.arraycopy(b, 0, out, 0, b.length);
        return out;
    }

    /** Response area starts at offset 100: BASE-PREMIUM 9(9)V99, REFER-FLAG X, REFER-REASON X(60). */
    Priced fromCommarea(byte[] area) {
        String s = new String(area, EBCDIC);
        BigDecimal premium = new BigDecimal(s.substring(100, 111)).movePointLeft(2);
        String refer = s.charAt(111) == 'Y' ? s.substring(112, 172).trim() : null;
        return new Priced(premium, refer);
    }

    public static class MainframeRatingException extends RuntimeException {
        public MainframeRatingException(String m) { super(m); }
    }
}
''')

w(J + "service/PolicyService.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.Policy;
import com.corvane.policy.domain.Quote;
import com.corvane.policy.events.PolicyEventPublisher;
import com.corvane.policy.ledger.LedgerClient;
import com.corvane.policy.repository.PolicyRepository;
import com.corvane.policy.repository.QuoteRepository;
import jakarta.persistence.EntityNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.LocalDate;

/** J4 steps 4–6: bind a quote, post the premium to the Oracle ledger, publish policies.bound.v1. */
@Service
public class PolicyService {

    private final PolicyRepository policies;
    private final QuoteRepository quotes;
    private final LedgerClient ledger;
    private final PolicyEventPublisher events;
    private final Clock clock;

    public PolicyService(PolicyRepository policies, QuoteRepository quotes, LedgerClient ledger,
                         PolicyEventPublisher events, Clock clock) {
        this.policies = policies;
        this.quotes = quotes;
        this.ledger = ledger;
        this.events = events;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public Policy find(String policyNumber) {
        return policies.findByPolicyNumber(policyNumber)
                .orElseThrow(() -> new EntityNotFoundException("No policy " + policyNumber));
    }

    @Transactional
    public Policy bind(String quoteId, LocalDate inception, String brokerCode) {
        Quote quote = quotes.findById(quoteId).orElseThrow(() -> new EntityNotFoundException("No quote " + quoteId));
        if (quote.isReferred()) {
            throw new QuoteNotBindableException("Quote " + quoteId + " is referred to an underwriter: " + quote.getReferralReason());
        }
        if (quote.isExpired(clock.instant())) {
            throw new QuoteNotBindableException("Quote " + quoteId + " expired at " + quote.getValidUntil());
        }
        String number = PolicyNumbers.format(quote.getLine(), policies.nextPolicySequence());
        Policy policy = new Policy(number, quote.getLine(), quote.getHolder());
        LocalDate start = inception == null ? LocalDate.now(clock) : inception;
        policy.bind(start, quote.getTotalPremium(), quote.getIptAmount(), "java");
        policies.save(policy);
        quote.markBound(policy.getId());
        ledger.postPremium(policy);
        events.policyBound(policy, brokerCode);
        return policy;
    }
}
''')

w(J + "service/PolicyNumbers.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;

/** Policy numbers are 12 characters: line code + 9-digit sequence, e.g. MTR000123456 (POLREC POLICY-NO X(12)). */
public final class PolicyNumbers {
    private PolicyNumbers() { }

    public static String format(ProductLine line, long sequence) {
        if (sequence < 0 || sequence > 999_999_999L) {
            throw new IllegalArgumentException("Policy sequence out of range: " + sequence);
        }
        return line.name() + String.format("%09d", sequence);
    }
}
''')

w(J + "service/RenewalService.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.Policy;
import com.corvane.policy.domain.PolicyStatus;
import com.corvane.policy.domain.RatingInput;
import com.corvane.policy.domain.RatingResult;
import com.corvane.policy.repository.PolicyRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.LocalDate;
import java.time.Period;
import java.util.List;
import java.util.Map;

/**
 * Finds policies expiring in the renewal window and re-prices them.
 *
 * <p>TODO(POL-1184): send the renewal invitation. The priced renewal is only logged; no event is published and no
 * email is sent, so customers are not told about renewals by this service.</p>
 */
@Service
public class RenewalService {

    private static final Logger log = LoggerFactory.getLogger(RenewalService.class);

    private final PolicyRepository policies;
    private final RatingService rating;
    private final Clock clock;
    private final int windowDays;

    public RenewalService(PolicyRepository policies, RatingService rating, Clock clock,
                          @Value("${policy.renewals.window-days}") int windowDays) {
        this.policies = policies;
        this.rating = rating;
        this.clock = clock;
        this.windowDays = windowDays;
    }

    @Scheduled(cron = "0 0 6 * * MON-FRI", zone = "Europe/London")
    @Transactional
    public int priceDueRenewals() {
        LocalDate today = LocalDate.now(clock);
        List<Policy> due = policies.findExpiring(PolicyStatus.BOUND, today, today.plusDays(windowDays));
        for (Policy p : due) {
            int age = Period.between(p.getHolder().getDateOfBirth(), today).getYears();
            RatingResult r = rating.rate(new RatingInput(p.getLine(), p.getHolder().getPostcode(), age,
                    p.getAnnualPremium().multiply(BigDecimal.valueOf(40)), p.getVoluntaryExcess(), 0, Map.of()));
            p.markRenewalDue();
            log.info("Renewal priced policy={} old={} new={} engine={}", p.getPolicyNumber(), p.getAnnualPremium(),
                    r.totalPremium(), r.engine());
            // TODO(POL-1184): publish policies.renewal-offered.v1 and email the holder.
        }
        return due.size();
    }
}
''')

w(J + "service/PostcodeLookupClient.java", r'''
package com.corvane.policy.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.Locale;
import java.util.Map;

/** External postcode lookup (outside the boundary): normalises and validates UK postcodes. */
@Component
public class PostcodeLookupClient {

    private final RestClient http;

    public PostcodeLookupClient(@Value("${postcode.base-url}") String baseUrl, @Value("${postcode.api-key}") String apiKey) {
        this.http = RestClient.builder().baseUrl(baseUrl).defaultHeader("X-Api-Key", apiKey).build();
    }

    @SuppressWarnings("unchecked")
    public String normalise(String raw) {
        String compact = raw.replace(" ", "").toUpperCase(Locale.UK);
        Map<String, Object> body = http.get().uri("/postcodes/{pc}", compact).retrieve().body(Map.class);
        if (body == null || !Boolean.TRUE.equals(body.get("valid"))) {
            throw new IllegalArgumentException("Unknown postcode " + raw);
        }
        return (String) body.get("formatted");
    }
}
''')

w(J + "ledger/LedgerClient.java", r'''
package com.corvane.policy.ledger;

import com.corvane.policy.domain.Policy;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.simple.SimpleJdbcCall;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Date;
import java.util.Map;

/** Posts a bound premium to the Oracle ledger: LEDGER.PKG_POLICY_LEDGER.post_premium (data/oracle). */
@Component
public class LedgerClient {

    private final SimpleJdbcCall postPremium;

    public LedgerClient(@Qualifier("ledgerDataSource") DataSource ledger) {
        this.postPremium = new SimpleJdbcCall(ledger)
                .withSchemaName("LEDGER")
                .withCatalogName("PKG_POLICY_LEDGER")
                .withProcedureName("POST_PREMIUM");
    }

    public long postPremium(Policy p) {
        Map<String, Object> out = postPremium.execute(Map.of(
                "P_POLICY_NO", p.getPolicyNumber(),
                "P_PARTY_REF", p.getHolder().getPartyRef(),
                "P_LINE_CODE", p.getLine().name(),
                "P_PREMIUM", p.getAnnualPremium(),
                "P_IPT", p.getIptAmount(),
                "P_CURRENCY", p.getCurrency(),
                "P_EFFECTIVE", Date.valueOf(p.getInceptionDate())));
        return ((Number) out.get("P_POSTING_ID")).longValue();
    }
}
''')

w(J + "events/PolicyBoundEvent.java", r'''
package com.corvane.policy.events;

import java.math.BigDecimal;
import java.time.LocalDate;

/** Payload of policies.bound.v1 (contracts/avro/PolicyBound.avsc). Consumers: broker-commissions, notifications. */
public record PolicyBoundEvent(String policyNumber, String lineCode, String partyRef, String brokerCode,
                               BigDecimal annualPremium, BigDecimal iptAmount, String currency, LocalDate inceptionDate,
                               String premiumEngine) {
}
''')

w(J + "events/PolicyEventPublisher.java", r'''
package com.corvane.policy.events;

import com.corvane.policy.domain.Policy;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class PolicyEventPublisher {

    private final KafkaTemplate<String, PolicyBoundEvent> kafka;
    private final String boundTopic;

    public PolicyEventPublisher(KafkaTemplate<String, PolicyBoundEvent> kafka,
                                @Value("${policy.topics.bound}") String boundTopic) {
        this.kafka = kafka;
        this.boundTopic = boundTopic;
    }

    /** Keyed by policy number so all events of one policy land on one partition. */
    public void policyBound(Policy p, String brokerCode) {
        kafka.send(boundTopic, p.getPolicyNumber(), new PolicyBoundEvent(p.getPolicyNumber(), p.getLine().name(),
                p.getHolder().getPartyRef(), brokerCode, p.getAnnualPremium(), p.getIptAmount(), p.getCurrency(),
                p.getInceptionDate(), p.getPremiumEngine()));
    }
}
''')

w(J + "config/SecurityConfig.java", r'''
package com.corvane.policy.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter;
import org.springframework.security.oauth2.server.resource.authentication.JwtGrantedAuthoritiesConverter;
import org.springframework.security.web.SecurityFilterChain;

/** JWTs from https://login.corvane.internal; the "roles" claim maps to CUSTOMER, ADJUSTER, CLAIMS_MANAGER, BROKER. */
@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        http.csrf(c -> c.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(a -> a
                .requestMatchers("/actuator/health/**", "/actuator/info").permitAll()
                .requestMatchers("/actuator/prometheus").hasRole("OPS")
                .anyRequest().authenticated())
            .oauth2ResourceServer(o -> o.jwt(j -> j.jwtAuthenticationConverter(roles())));
        return http.build();
    }

    private JwtAuthenticationConverter roles() {
        JwtGrantedAuthoritiesConverter g = new JwtGrantedAuthoritiesConverter();
        g.setAuthoritiesClaimName("roles");
        g.setAuthorityPrefix("ROLE_");
        JwtAuthenticationConverter c = new JwtAuthenticationConverter();
        c.setJwtGrantedAuthoritiesConverter(g);
        return c;
    }
}
''')

w(J + "config/LedgerDataSourceConfig.java", r'''
package com.corvane.policy.config;

import com.zaxxer.hikari.HikariDataSource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;
import java.time.Clock;

@Configuration
public class LedgerDataSourceConfig {

    @Bean(name = "ledgerDataSource")
    DataSource ledgerDataSource(@Value("${ledger.url}") String url, @Value("${ledger.username}") String user,
                                @Value("${ledger.password}") String password) {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl(url);
        ds.setUsername(user);
        ds.setPassword(password);
        ds.setMaximumPoolSize(5);
        ds.setPoolName("ledger");
        return ds;
    }

    @Bean
    Clock clock() { return Clock.systemUTC(); }
}
''')

w(J + "rating/LineRatingRules.java", r'''
package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;

import java.math.BigDecimal;
import java.util.Optional;

/** One per product line; generated classes live alongside (e.g. MtrRatingRules). Ported from mainframe RATxxx01. */
public interface LineRatingRules {

    ProductLine line();

    BigDecimal basePremium(RatingInput input);

    /** A reason when an underwriter must review the quote; empty when it can be bound straight away. */
    Optional<String> referralReason(RatingInput input);
}
''')

# ---------------- tests ----------------
w(T + "service/RatingServiceTest.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import com.corvane.policy.domain.RatingResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;

class RatingServiceTest {

    private PremiumEngine engine;
    private RatingService rating;

    @BeforeEach
    void setUp() {
        engine = mock(PremiumEngine.class);
        PremiumEngineRouter router = mock(PremiumEngineRouter.class);
        when(router.select()).thenReturn(engine);
        when(engine.name()).thenReturn("java");
        rating = new RatingService(router, new BigDecimal("0.12"), new BigDecimal("0.20"), List.of("TRV", "GDG"));
    }

    private RatingInput input(ProductLine line, String voluntary) {
        return new RatingInput(line, "LS1 4AP", 40, new BigDecimal("20000"), new BigDecimal(voluntary), 0, Map.of());
    }

    @Test
    void excessIsCompulsory250PlusVoluntary() {
        assertThat(rating.applyExcess(new BigDecimal("100"))).isEqualByComparingTo("350");
    }

    @Test
    void excessRoundsHalfUp() {
        assertThat(rating.applyExcess(new BigDecimal("99.50"))).isEqualByComparingTo("350");
        assertThat(rating.applyExcess(new BigDecimal("99.49"))).isEqualByComparingTo("349");
    }

    @Test
    void negativeVoluntaryExcessIsIgnored() {
        assertThat(rating.applyExcess(new BigDecimal("-50"))).isEqualByComparingTo("250");
    }

    @Test
    void standardIptForMotor() {
        when(engine.price(any())).thenReturn(new PremiumEngine.Priced(new BigDecimal("500.00"), null));
        RatingResult r = rating.rate(input(ProductLine.MTR, "0"));
        assertThat(r.ipt()).isEqualByComparingTo("60.00");
        assertThat(r.totalPremium()).isEqualByComparingTo("560.00");
        assertThat(r.engine()).isEqualTo("java");
    }

    @Test
    void higherIptForTravelAndGadget() {
        when(engine.price(any())).thenReturn(new PremiumEngine.Priced(new BigDecimal("100.00"), null));
        assertThat(rating.rate(input(ProductLine.TRV, "0")).ipt()).isEqualByComparingTo("20.00");
        assertThat(rating.rate(input(ProductLine.GDG, "0")).ipt()).isEqualByComparingTo("20.00");
    }

    @Test
    void referralReasonIsPassedThrough() {
        when(engine.price(any())).thenReturn(new PremiumEngine.Priced(new BigDecimal("900.00"), "Sum insured above line limit"));
        assertThat(rating.rate(input(ProductLine.HOM, "0")).referralReason()).contains("line limit");
    }
}
''')

w(T + "service/PremiumEngineRouterTest.java", r'''
package com.corvane.policy.service;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.mock;

class PremiumEngineRouterTest {

    private final JavaRatingService javaEngine = mock(JavaRatingService.class);
    private final MainframePremiumAdapter mainframe = mock(MainframePremiumAdapter.class);

    @Test
    void javaFlagSelectsJavaPort() {
        assertThat(new PremiumEngineRouter(javaEngine, mainframe, "java").select()).isSameAs(javaEngine);
    }

    @Test
    void mainframeFlagSelectsCtgAdapter() {
        assertThat(new PremiumEngineRouter(javaEngine, mainframe, "mainframe").select()).isSameAs(mainframe);
    }

    @Test
    void unknownFlagFailsFast() {
        assertThatThrownBy(() -> new PremiumEngineRouter(javaEngine, mainframe, "cobol").select())
                .isInstanceOf(IllegalStateException.class);
    }
}
''')

w(T + "service/PolicyServiceTest.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.*;
import com.corvane.policy.events.PolicyEventPublisher;
import com.corvane.policy.ledger.LedgerClient;
import com.corvane.policy.repository.PolicyRepository;
import com.corvane.policy.repository.QuoteRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.*;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

class PolicyServiceTest {

    private final Clock clock = Clock.fixed(Instant.parse("2026-11-16T09:00:00Z"), ZoneOffset.UTC);
    private PolicyRepository policies;
    private QuoteRepository quotes;
    private LedgerClient ledger;
    private PolicyEventPublisher events;
    private PolicyService service;

    @BeforeEach
    void setUp() {
        policies = mock(PolicyRepository.class);
        quotes = mock(QuoteRepository.class);
        ledger = mock(LedgerClient.class);
        events = mock(PolicyEventPublisher.class);
        service = new PolicyService(policies, quotes, ledger, events, clock);
        when(policies.nextPolicySequence()).thenReturn(123456L);
    }

    private Quote quote(String referral, Instant validUntil) {
        PolicyHolder h = new PolicyHolder("PTY000000000001", "Ada Example", LocalDate.of(1985, 3, 2), "LS1 4AP");
        RatingResult r = new RatingResult(new BigDecimal("500.00"), new BigDecimal("60.00"), new BigDecimal("560.00"),
                new BigDecimal("250"), referral, "java");
        return new Quote(ProductLine.MTR, h, r, validUntil);
    }

    @Test
    void bindPostsToLedgerAndPublishes() {
        Quote q = quote(null, clock.instant().plusSeconds(3600));
        when(quotes.findById(q.getId())).thenReturn(Optional.of(q));
        Policy p = service.bind(q.getId(), LocalDate.of(2026, 12, 1), "BRK042");
        assertThat(p.getPolicyNumber()).isEqualTo("MTR000123456");
        assertThat(p.getExpiryDate()).isEqualTo(LocalDate.of(2027, 11, 30));
        verify(ledger).postPremium(p);
        verify(events).policyBound(p, "BRK042");
    }

    @Test
    void referredQuoteCannotBeBound() {
        Quote q = quote("Prior claims above 3", clock.instant().plusSeconds(3600));
        when(quotes.findById(q.getId())).thenReturn(Optional.of(q));
        assertThatThrownBy(() -> service.bind(q.getId(), null, null)).isInstanceOf(QuoteNotBindableException.class);
        verifyNoInteractions(ledger, events);
    }

    @Test
    void expiredQuoteCannotBeBound() {
        Quote q = quote(null, clock.instant().minusSeconds(1));
        when(quotes.findById(q.getId())).thenReturn(Optional.of(q));
        assertThatThrownBy(() -> service.bind(q.getId(), null, null)).hasMessageContaining("expired");
    }
}
''')

w(T + "service/PolicyNumbersTest.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.*;

class PolicyNumbersTest {
    @Test
    void twelveCharacters() {
        assertThat(PolicyNumbers.format(ProductLine.CYB, 42)).isEqualTo("CYB000000042").hasSize(12);
    }

    @Test
    void rejectsOverflow() {
        assertThatThrownBy(() -> PolicyNumbers.format(ProductLine.MTR, 1_000_000_000L)).isInstanceOf(IllegalArgumentException.class);
    }
}
''')

w(T + "service/MainframePremiumAdapterTest.java", r'''
package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.nio.charset.Charset;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class MainframePremiumAdapterTest {

    private final MainframePremiumAdapter adapter = new MainframePremiumAdapter("localhost", 2006, "CORVCTG1", "PRMCALC0", 4000);

    @Test
    void commareaIsEbcdicPrmcommLayout() {
        byte[] area = adapter.toCommarea(new RatingInput(ProductLine.HOM, "LS1 4AP", 52, new BigDecimal("350000.00"),
                new BigDecimal("100.00"), 1, Map.of()));
        assertThat(area).hasSize(MainframePremiumAdapter.COMMAREA_LENGTH);
        assertThat(new String(area, 0, 3, Charset.forName("Cp037"))).isEqualTo("HOM");
    }

    @Test
    void parsesPremiumAndReferral() {
        StringBuilder s = new StringBuilder(" ".repeat(200));
        s.replace(100, 111, "00000045678");
        s.replace(111, 112, "Y");
        s.replace(112, 130, "FLOOD ZONE 3      ");
        PremiumEngine.Priced p = adapter.fromCommarea(s.toString().getBytes(Charset.forName("Cp037")));
        assertThat(p.basePremium()).isEqualByComparingTo("456.78");
        assertThat(p.referralReason()).isEqualTo("FLOOD ZONE 3");
    }
}
''')
print("a_core1 done")
