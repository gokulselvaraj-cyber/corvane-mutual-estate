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
