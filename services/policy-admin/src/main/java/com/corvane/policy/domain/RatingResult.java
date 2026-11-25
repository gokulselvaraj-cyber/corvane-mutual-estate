package com.corvane.policy.domain;

import java.math.BigDecimal;

/** What a premium engine returns. {@code engine} is "java" or "mainframe" so the policy records who priced it. */
public record RatingResult(BigDecimal basePremium, BigDecimal ipt, BigDecimal totalPremium,
                           BigDecimal excessTotal, String referralReason, String engine) {
}
