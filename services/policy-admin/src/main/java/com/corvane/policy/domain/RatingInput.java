package com.corvane.policy.domain;

import java.math.BigDecimal;
import java.util.Map;

/** Risk facts captured by the quote form. {@code factors} holds the line-specific answers (e.g. vehicleAge). */
public record RatingInput(ProductLine line, String postcode, int holderAge, BigDecimal sumInsured,
                          BigDecimal voluntaryExcess, int priorClaims, Map<String, String> factors) {
}
