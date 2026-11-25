package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Motor (MTR) rating rules: Java port of mainframe program RATMTR01.
 * Base rate 20.945 per 1,000 sum insured, minimum premium 240 GBP, maximum sum insured 120,000.
 * Generated from the rating workbook RW-MTR-2026Q3; edit the workbook, not this file.
 */
@Component
public class MtrRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("20.945");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("240");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("120000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.13");
    static final int REFER_PRIOR_CLAIMS = 3;

    static final Map<String, BigDecimal> VEHICLE_GROUP = Map.of("1-10", new BigDecimal("1.0"), "11-20", new BigDecimal("1.41"), "21-30", new BigDecimal("1.72"), "31-40", new BigDecimal("1.58"), "41-50", new BigDecimal("1.05"));
    static final Map<String, BigDecimal> ANNUAL_MILEAGE = Map.of("<5k", new BigDecimal("1.0"), "5-10k", new BigDecimal("1.28"), "10-15k", new BigDecimal("1.3"), ">15k", new BigDecimal("0.93"));
    static final Map<String, BigDecimal> OVERNIGHT = Map.of("garage", new BigDecimal("1.0"), "driveway", new BigDecimal("1.31"), "street", new BigDecimal("1.03"));
    static final Map<String, BigDecimal> USE = Map.of("social", new BigDecimal("1.0"), "commuting", new BigDecimal("1.05"), "business", new BigDecimal("1.44"));
    static final Map<String, BigDecimal> AREA = Map.of("B", new BigDecimal("1.44"), "M", new BigDecimal("1.15"), "N", new BigDecimal("1.0"), "SE", new BigDecimal("1.16"), "W", new BigDecimal("1.19"));

    @Override
    public ProductLine line() { return ProductLine.MTR; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(VEHICLE_GROUP.getOrDefault(in.factors().getOrDefault("vehicleGroup", "1-10"), BigDecimal.ONE));
        p = p.multiply(ANNUAL_MILEAGE.getOrDefault(in.factors().getOrDefault("annualMileage", "<5k"), BigDecimal.ONE));
        p = p.multiply(OVERNIGHT.getOrDefault(in.factors().getOrDefault("overnight", "garage"), BigDecimal.ONE));
        p = p.multiply(USE.getOrDefault(in.factors().getOrDefault("use", "social"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 42) return new BigDecimal("1.41");
        if (age < 53) return new BigDecimal("1.0");
        if (age < 75) return new BigDecimal("0.92");
        return new BigDecimal("1.19");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Motor limit of 120,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if ("41-50".equals(in.factors().get("vehicleGroup"))) {
            return Optional.of("Vehicle group 41-50 needs underwriter review");
        }
        return Optional.empty();
    }

    static String area(String postcode) {
        String outward = postcode == null ? "" : postcode.trim().split(" ")[0];
        String letters = outward.replaceAll("[0-9].*$", "");
        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? "" : letters.substring(0, 1);
    }

    /** Risks priced but flagged for the next workbook review (no referral today). */
    static boolean onWatchList(RatingInput in) {
        return "business".equals(in.factors().get("use"));
    }
}
