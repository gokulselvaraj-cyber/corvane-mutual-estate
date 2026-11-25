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
