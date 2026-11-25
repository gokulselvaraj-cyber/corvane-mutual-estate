package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Marine cargo (MAR) rating rules: Java port of mainframe program RATMAR01.
 * Base rate 1.299 per 1,000 sum insured, minimum premium 450 GBP, maximum sum insured 25,000,000.
 * Generated from the rating workbook RW-MAR-2026Q3; edit the workbook, not this file.
 */
@Component
public class MarRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("1.299");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("450");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("25000000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.16");
    static final int REFER_PRIOR_CLAIMS = 4;

    static final Map<String, BigDecimal> CONVEYANCE = Map.of("container-ship", new BigDecimal("1.0"), "bulk", new BigDecimal("1.06"), "air", new BigDecimal("1.39"), "road", new BigDecimal("1.81"));
    static final Map<String, BigDecimal> COMMODITY = Map.of("general", new BigDecimal("1.0"), "perishable", new BigDecimal("1.04"), "hazardous", new BigDecimal("0.81"), "fine-art", new BigDecimal("1.13"));
    static final Map<String, BigDecimal> ROUTE = Map.of("intra-EU", new BigDecimal("1.0"), "transatlantic", new BigDecimal("1.89"), "Asia-Europe", new BigDecimal("1.62"), "high-risk-waters", new BigDecimal("1.1"));
    static final Map<String, BigDecimal> AREA = Map.of("B", new BigDecimal("1.06"), "E", new BigDecimal("1.26"), "G", new BigDecimal("0.99"), "LS", new BigDecimal("1.43"), "SW", new BigDecimal("0.86"));

    @Override
    public ProductLine line() { return ProductLine.MAR; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(CONVEYANCE.getOrDefault(in.factors().getOrDefault("conveyance", "container-ship"), BigDecimal.ONE));
        p = p.multiply(COMMODITY.getOrDefault(in.factors().getOrDefault("commodity", "general"), BigDecimal.ONE));
        p = p.multiply(ROUTE.getOrDefault(in.factors().getOrDefault("route", "intra-EU"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 39) return new BigDecimal("1.55");
        if (age < 46) return new BigDecimal("1.0");
        if (age < 52) return new BigDecimal("0.93");
        return new BigDecimal("1.14");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Marine cargo limit of 25,000,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if ("high-risk-waters".equals(in.factors().get("route"))) {
            return Optional.of("Route through listed high-risk waters");
        }
        if ("fine-art".equals(in.factors().get("commodity"))) {
            return Optional.of("Fine art cargo");
        }
        return Optional.empty();
    }

    static String area(String postcode) {
        String outward = postcode == null ? "" : postcode.trim().split(" ")[0];
        String letters = outward.replaceAll("[0-9].*$", "");
        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? "" : letters.substring(0, 1);
    }
}
