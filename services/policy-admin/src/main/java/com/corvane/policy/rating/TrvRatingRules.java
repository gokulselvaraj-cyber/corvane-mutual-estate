package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Travel (TRV) rating rules: Java port of mainframe program RATTRV01.
 * Base rate 11.255 per 1,000 sum insured, minimum premium 18 GBP, maximum sum insured 10,000,000.
 * Generated from the rating workbook RW-TRV-2026Q3; edit the workbook, not this file.
 */
@Component
public class TrvRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("11.255");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("18");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("10000000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.24");
    static final int REFER_PRIOR_CLAIMS = 2;

    static final Map<String, BigDecimal> REGION = Map.of("UK", new BigDecimal("1.0"), "Europe", new BigDecimal("1.26"), "Worldwide-ex-USA", new BigDecimal("1.56"), "Worldwide", new BigDecimal("1.88"));
    static final Map<String, BigDecimal> TRIP_TYPE = Map.of("single", new BigDecimal("1.0"), "annual", new BigDecimal("1.5"));
    static final Map<String, BigDecimal> WINTER_SPORTS = Map.of("no", new BigDecimal("1.0"), "yes", new BigDecimal("1.37"));
    static final Map<String, BigDecimal> MEDICAL_CONDITIONS = Map.of("none", new BigDecimal("1.0"), "declared", new BigDecimal("1.63"), "undeclared", new BigDecimal("1.15"));
    static final Map<String, BigDecimal> AREA = Map.of("B", new BigDecimal("1.08"), "BS", new BigDecimal("1.21"), "M", new BigDecimal("1.1"), "SE", new BigDecimal("0.85"), "SW", new BigDecimal("1.2"));

    @Override
    public ProductLine line() { return ProductLine.TRV; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(REGION.getOrDefault(in.factors().getOrDefault("region", "UK"), BigDecimal.ONE));
        p = p.multiply(TRIP_TYPE.getOrDefault(in.factors().getOrDefault("tripType", "single"), BigDecimal.ONE));
        p = p.multiply(WINTER_SPORTS.getOrDefault(in.factors().getOrDefault("winterSports", "no"), BigDecimal.ONE));
        p = p.multiply(MEDICAL_CONDITIONS.getOrDefault(in.factors().getOrDefault("medicalConditions", "none"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 21) return new BigDecimal("1.22");
        if (age < 59) return new BigDecimal("1.0");
        if (age < 64) return new BigDecimal("0.92");
        return new BigDecimal("1.34");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Travel limit of 10,000,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if ("declared".equals(in.factors().get("medicalConditions"))) {
            return Optional.of("Declared medical conditions need screening");
        }
        return Optional.empty();
    }

    static String area(String postcode) {
        String outward = postcode == null ? "" : postcode.trim().split(" ")[0];
        String letters = outward.replaceAll("[0-9].*$", "");
        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? "" : letters.substring(0, 1);
    }
}
