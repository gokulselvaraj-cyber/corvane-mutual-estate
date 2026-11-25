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
