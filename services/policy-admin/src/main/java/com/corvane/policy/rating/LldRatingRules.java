package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Landlord (LLD) rating rules: Java port of mainframe program RATLLD01.
 * Base rate 2.305 per 1,000 sum insured, minimum premium 180 GBP, maximum sum insured 3,000,000.
 * Generated from the rating workbook RW-LLD-2026Q3; edit the workbook, not this file.
 */
@Component
public class LldRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("2.305");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("180");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("3000000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.19");
    static final int REFER_PRIOR_CLAIMS = 2;

    static final Map<String, BigDecimal> TENANT_TYPE = Map.of("professional", new BigDecimal("1.0"), "student", new BigDecimal("1.6"), "DSS", new BigDecimal("1.21"), "holiday-let", new BigDecimal("1.16"));
    static final Map<String, BigDecimal> UNITS = Map.of("1", new BigDecimal("1.0"), "2-4", new BigDecimal("1.05"), "5+", new BigDecimal("0.96"));
    static final Map<String, BigDecimal> UNOCCUPIED_DAYS = Map.of("0-30", new BigDecimal("1.0"), "31-60", new BigDecimal("1.8"), "60+", new BigDecimal("1.44"));
    static final Map<String, BigDecimal> AREA = Map.of("B", new BigDecimal("1.31"), "CF", new BigDecimal("0.88"), "EH", new BigDecimal("1.16"), "SE", new BigDecimal("1.23"), "W", new BigDecimal("0.88"));

    @Override
    public ProductLine line() { return ProductLine.LLD; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(TENANT_TYPE.getOrDefault(in.factors().getOrDefault("tenantType", "professional"), BigDecimal.ONE));
        p = p.multiply(UNITS.getOrDefault(in.factors().getOrDefault("units", "1"), BigDecimal.ONE));
        p = p.multiply(UNOCCUPIED_DAYS.getOrDefault(in.factors().getOrDefault("unoccupiedDays", "0-30"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 21) return new BigDecimal("1.53");
        if (age < 42) return new BigDecimal("1.0");
        if (age < 59) return new BigDecimal("0.93");
        return new BigDecimal("1.23");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Landlord limit of 3,000,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if ("60+".equals(in.factors().get("unoccupiedDays"))) {
            return Optional.of("Unoccupied over 60 days");
        }
        if ("5+".equals(in.factors().get("units"))) {
            return Optional.of("HMO with 5+ units");
        }
        return Optional.empty();
    }

    static String area(String postcode) {
        String outward = postcode == null ? "" : postcode.trim().split(" ")[0];
        String letters = outward.replaceAll("[0-9].*$", "");
        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? "" : letters.substring(0, 1);
    }
}
