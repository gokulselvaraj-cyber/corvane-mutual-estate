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
