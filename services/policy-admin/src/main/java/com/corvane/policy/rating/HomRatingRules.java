package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Home buildings (HOM) rating rules: Java port of mainframe program RATHOM01.
 * Base rate 0.905 per 1,000 sum insured, minimum premium 140 GBP, maximum sum insured 2,000,000.
 * Generated from the rating workbook RW-HOM-2026Q3; edit the workbook, not this file.
 */
@Component
public class HomRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("0.905");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("140");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("2000000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.13");
    static final int REFER_PRIOR_CLAIMS = 3;

    static final Map<String, BigDecimal> BUILD_YEAR = Map.of("pre-1900", new BigDecimal("1.0"), "1900-1945", new BigDecimal("0.93"), "1946-1990", new BigDecimal("1.01"), "post-1990", new BigDecimal("1.49"));
    static final Map<String, BigDecimal> FLOOD_ZONE = Map.of("1", new BigDecimal("1.0"), "2", new BigDecimal("1.12"), "3", new BigDecimal("1.27"));
    static final Map<String, BigDecimal> ROOF = Map.of("tile", new BigDecimal("1.0"), "slate", new BigDecimal("1.07"), "flat", new BigDecimal("1.23"), "thatch", new BigDecimal("0.93"));
    static final Map<String, BigDecimal> LISTED = Map.of("no", new BigDecimal("1.0"), "grade II", new BigDecimal("1.41"), "grade I", new BigDecimal("1.5"));
    static final Map<String, BigDecimal> AREA = Map.of("BS", new BigDecimal("1.2"), "CF", new BigDecimal("0.97"), "E", new BigDecimal("0.98"), "L", new BigDecimal("1.23"), "SW", new BigDecimal("1.1"));

    @Override
    public ProductLine line() { return ProductLine.HOM; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(BUILD_YEAR.getOrDefault(in.factors().getOrDefault("buildYear", "pre-1900"), BigDecimal.ONE));
        p = p.multiply(FLOOD_ZONE.getOrDefault(in.factors().getOrDefault("floodZone", "1"), BigDecimal.ONE));
        p = p.multiply(ROOF.getOrDefault(in.factors().getOrDefault("roof", "tile"), BigDecimal.ONE));
        p = p.multiply(LISTED.getOrDefault(in.factors().getOrDefault("listed", "no"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 31) return new BigDecimal("1.45");
        if (age < 33) return new BigDecimal("1.0");
        if (age < 66) return new BigDecimal("0.88");
        return new BigDecimal("1.2");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Home buildings limit of 2,000,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if ("3".equals(in.factors().get("floodZone"))) {
            return Optional.of("Flood zone 3");
        }
        if ("thatch".equals(in.factors().get("roof"))) {
            return Optional.of("Thatched roof");
        }
        if ("grade I".equals(in.factors().get("listed"))) {
            return Optional.of("Grade I listed");
        }
        return Optional.empty();
    }

    static String area(String postcode) {
        String outward = postcode == null ? "" : postcode.trim().split(" ")[0];
        String letters = outward.replaceAll("[0-9].*$", "");
        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? "" : letters.substring(0, 1);
    }
}
