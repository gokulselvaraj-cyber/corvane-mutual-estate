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
