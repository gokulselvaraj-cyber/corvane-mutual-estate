package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Home contents (CNT) rating rules: Java port of mainframe program RATCNT01.
 * Base rate 4.258 per 1,000 sum insured, minimum premium 60 GBP, maximum sum insured 150,000.
 * Generated from the rating workbook RW-CNT-2026Q3; edit the workbook, not this file.
 */
@Component
public class CntRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("4.258");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("60");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("150000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.17");
    static final int REFER_PRIOR_CLAIMS = 4;

    static final Map<String, BigDecimal> LOCKS = Map.of("BS3621", new BigDecimal("1.0"), "other", new BigDecimal("1.03"));
    static final Map<String, BigDecimal> ALARM = Map.of("monitored", new BigDecimal("1.0"), "bells-only", new BigDecimal("1.5"), "none", new BigDecimal("1.43"));
    static final Map<String, BigDecimal> OCCUPANCY = Map.of("owner", new BigDecimal("1.0"), "tenant", new BigDecimal("1.52"), "student", new BigDecimal("1.44"));
    static final Map<String, BigDecimal> AREA = Map.of("B", new BigDecimal("0.96"), "BS", new BigDecimal("1.21"), "E", new BigDecimal("0.99"), "L", new BigDecimal("1.04"), "SE", new BigDecimal("1.41"));

    @Override
    public ProductLine line() { return ProductLine.CNT; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(LOCKS.getOrDefault(in.factors().getOrDefault("locks", "BS3621"), BigDecimal.ONE));
        p = p.multiply(ALARM.getOrDefault(in.factors().getOrDefault("alarm", "monitored"), BigDecimal.ONE));
        p = p.multiply(OCCUPANCY.getOrDefault(in.factors().getOrDefault("occupancy", "owner"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 35) return new BigDecimal("1.56");
        if (age < 52) return new BigDecimal("1.0");
        if (age < 54) return new BigDecimal("0.98");
        return new BigDecimal("1.04");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Home contents limit of 150,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
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
        return "student".equals(in.factors().get("occupancy"));
    }
}
