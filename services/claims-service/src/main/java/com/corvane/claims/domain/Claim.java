package com.corvane.claims.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.UUID;

/** An insurance claim. Table claims.claim (data/postgres). Not to be confused with JWT claims (security.TokenClaims). */
@Entity
@Table(name = "claim", schema = "claims")
public class Claim {
    @Id
    private UUID id;
    @Column(name = "claim_number", nullable = false, unique = true)
    private String claimNumber;
    @Column(name = "policy_number", nullable = false)
    private String policyNumber;
    @Column(name = "line_code", length = 3)
    private String lineCode;
    @Enumerated(EnumType.STRING)
    private ClaimStatus status;
    @Column(name = "incident_date")
    private LocalDate incidentDate;
    @Column(name = "loss_cause")
    private String lossCause;
    private String description;
    /** Special-category data (health). Retained 7 years by claims.purge_expired_claims(). */
    @Column(name = "injury_notes")
    private String injuryNotes;
    @Column(name = "estimated_amount")
    private BigDecimal estimatedAmount;
    @Column(name = "reserve_amount")
    private BigDecimal reserveAmount;
    @Column(name = "paid_amount")
    private BigDecimal paidAmount;
    @Column(name = "fraud_score")
    private Double fraudScore;
    @Column(name = "triage_outcome")
    private String triageOutcome;
    @Column(name = "registered_at")
    private OffsetDateTime registeredAt;
    @Column(name = "registered_by")
    private String registeredBy;

    protected Claim() {}

    public static Claim newClaim(String number, String policyNumber, String lineCode) {
        Claim c = new Claim();
        c.id = UUID.randomUUID();
        c.claimNumber = number;
        c.policyNumber = policyNumber;
        c.lineCode = lineCode;
        c.status = ClaimStatus.REGISTERED;
        c.registeredAt = OffsetDateTime.now();
        return c;
    }

    public UUID getId() { return id; }
    public String getClaimNumber() { return claimNumber; }
    public String getPolicyNumber() { return policyNumber; }
    public String getLineCode() { return lineCode; }
    public ClaimStatus getStatus() { return status; }
    public void setStatus(ClaimStatus status) { this.status = status; }
    public LocalDate getIncidentDate() { return incidentDate; }
    public void setIncidentDate(LocalDate d) { this.incidentDate = d; }
    public String getLossCause() { return lossCause; }
    public void setLossCause(String c) { this.lossCause = c; }
    public String getDescription() { return description; }
    public void setDescription(String d) { this.description = d; }
    public String getInjuryNotes() { return injuryNotes; }
    public void setInjuryNotes(String n) { this.injuryNotes = n; }
    public BigDecimal getEstimatedAmount() { return estimatedAmount; }
    public void setEstimatedAmount(BigDecimal a) { this.estimatedAmount = a; }
    public BigDecimal getReserveAmount() { return reserveAmount; }
    public void setReserveAmount(BigDecimal a) { this.reserveAmount = a; }
    public BigDecimal getPaidAmount() { return paidAmount; }
    public void setPaidAmount(BigDecimal a) { this.paidAmount = a; }
    public Double getFraudScore() { return fraudScore; }
    public void setFraudScore(Double s) { this.fraudScore = s; }
    public String getTriageOutcome() { return triageOutcome; }
    public void setTriageOutcome(String t) { this.triageOutcome = t; }
    public OffsetDateTime getRegisteredAt() { return registeredAt; }
    public void setRegisteredBy(String u) { this.registeredBy = u; }
}
