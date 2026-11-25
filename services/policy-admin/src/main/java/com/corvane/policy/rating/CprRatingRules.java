package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Commercial property (CPR) rating rules: Java port of mainframe program RATCPR01.
 * Base rate 2.434 per 1,000 sum insured, minimum premium 600 GBP, maximum sum insured 50,000,000.
 * Generated from the rating workbook RW-CPR-2026Q3; edit the workbook, not this file.
 */
@Component
public class CprRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("2.434");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("600");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("50000000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.12");
    static final int REFER_PRIOR_CLAIMS = 4;

    static final Map<String, BigDecimal> CONSTRUCTION = Map.of("standard", new BigDecimal("1.0"), "composite-panel", new BigDecimal("1.82"), "timber-frame", new BigDecimal("1.67"));
    static final Map<String, BigDecimal> SPRINKLERS = Map.of("yes", new BigDecimal("1.0"), "no", new BigDecimal("1.26"));
    static final Map<String, BigDecimal> TRADE = Map.of("office", new BigDecimal("1.0"), "retail", new BigDecimal("1.24"), "warehouse", new BigDecimal("1.18"), "manufacturing", new BigDecimal("1.75"), "food-processing", new BigDecimal("1.69"));
    static final Map<String, BigDecimal> AREA = Map.of("B", new BigDecimal("0.89"), "EH", new BigDecimal("1.4"), "L", new BigDecimal("1.01"), "LS", new BigDecimal("1.2"), "W", new BigDecimal("0.93"));

    @Override
    public ProductLine line() { return ProductLine.CPR; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(CONSTRUCTION.getOrDefault(in.factors().getOrDefault("construction", "standard"), BigDecimal.ONE));
        p = p.multiply(SPRINKLERS.getOrDefault(in.factors().getOrDefault("sprinklers", "yes"), BigDecimal.ONE));
        p = p.multiply(TRADE.getOrDefault(in.factors().getOrDefault("trade", "office"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 28) return new BigDecimal("1.47");
        if (age < 29) return new BigDecimal("1.0");
        if (age < 40) return new BigDecimal("0.98");
        return new BigDecimal("1.07");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Commercial property limit of 50,000,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if ("composite-panel".equals(in.factors().get("construction"))) {
            return Optional.of("Composite panel construction");
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
        return "food-processing".equals(in.factors().get("trade"));
    }
}
