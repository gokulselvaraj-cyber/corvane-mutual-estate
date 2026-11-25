package com.corvane.policy.service;

import com.corvane.policy.domain.RatingInput;
import java.math.BigDecimal;

/** A base-premium engine. Two implementations: the Java port and the mainframe adapter (ADR-0009). */
public interface PremiumEngine {

    record Priced(BigDecimal basePremium, String referralReason) { }

    String name();

    Priced price(RatingInput input);
}
