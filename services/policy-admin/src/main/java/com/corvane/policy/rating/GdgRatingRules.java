package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Gadget (GDG) rating rules: Java port of mainframe program RATGDG01.
 * Base rate 84.468 per 1,000 sum insured, minimum premium 45 GBP, maximum sum insured 6,000.
 * Generated from the rating workbook RW-GDG-2026Q3; edit the workbook, not this file.
 */
@Component
public class GdgRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("84.468");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("45");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("6000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.11");
    static final int REFER_PRIOR_CLAIMS = 2;

    static final Map<String, BigDecimal> DEVICE = Map.of("phone", new BigDecimal("1.0"), "laptop", new BigDecimal("1.3"), "tablet", new BigDecimal("0.93"), "wearable", new BigDecimal("1.88"), "console", new BigDecimal("1.24"));
    static final Map<String, BigDecimal> AGE = Map.of("new", new BigDecimal("1.0"), "<1y", new BigDecimal("0.84"), "1-2y", new BigDecimal("1.19"), ">2y", new BigDecimal("1.54"));
    static final Map<String, BigDecimal> THEFT_COVER = Map.of("yes", new BigDecimal("1.0"), "no", new BigDecimal("1.55"));
    static final Map<String, BigDecimal> AREA = Map.of("B", new BigDecimal("1.13"), "BS", new BigDecimal("1.38"), "G", new BigDecimal("1.23"), "SW", new BigDecimal("1.39"), "W", new BigDecimal("0.91"));

    @Override
    public ProductLine line() { return ProductLine.GDG; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(DEVICE.getOrDefault(in.factors().getOrDefault("device", "phone"), BigDecimal.ONE));
        p = p.multiply(AGE.getOrDefault(in.factors().getOrDefault("age", "new"), BigDecimal.ONE));
        p = p.multiply(THEFT_COVER.getOrDefault(in.factors().getOrDefault("theftCover", "yes"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 23) return new BigDecimal("1.42");
        if (age < 34) return new BigDecimal("1.0");
        if (age < 47) return new BigDecimal("0.9");
        return new BigDecimal("1.29");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Gadget limit of 6,000");
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
        return ">2y".equals(in.factors().get("age"));
    }
}
