package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.Optional;

/**
 * Pet (PET) rating rules: Java port of mainframe program RATPET01.
 * Base rate 29.175 per 1,000 sum insured, minimum premium 72 GBP, maximum sum insured 15,000.
 * Generated from the rating workbook RW-PET-2026Q3; edit the workbook, not this file.
 */
@Component
public class PetRatingRules implements LineRatingRules {

    static final BigDecimal RATE_PER_1000 = new BigDecimal("29.175");
    static final BigDecimal MINIMUM_PREMIUM = new BigDecimal("72");
    static final BigDecimal MAX_SUM_INSURED = new BigDecimal("15000");
    static final BigDecimal PRIOR_CLAIM_LOADING = new BigDecimal("0.22");
    static final int REFER_PRIOR_CLAIMS = 3;

    static final Map<String, BigDecimal> SPECIES = Map.of("dog", new BigDecimal("1.0"), "cat", new BigDecimal("1.59"), "rabbit", new BigDecimal("1.42"));
    static final Map<String, BigDecimal> BREED_GROUP = Map.of("crossbreed", new BigDecimal("1.0"), "pedigree", new BigDecimal("1.56"), "dangerous-dogs-act", new BigDecimal("1.25"));
    static final Map<String, BigDecimal> COVER = Map.of("accident", new BigDecimal("1.0"), "time-limited", new BigDecimal("1.79"), "lifetime", new BigDecimal("1.52"));
    static final Map<String, BigDecimal> NEUTERED = Map.of("yes", new BigDecimal("1.0"), "no", new BigDecimal("1.29"));
    static final Map<String, BigDecimal> AREA = Map.of("E", new BigDecimal("1.4"), "G", new BigDecimal("0.88"), "LS", new BigDecimal("1.15"), "NE", new BigDecimal("1.14"), "SE", new BigDecimal("1.26"));

    @Override
    public ProductLine line() { return ProductLine.PET; }

    @Override
    public BigDecimal basePremium(RatingInput in) {
        BigDecimal p = in.sumInsured().divide(BigDecimal.valueOf(1000)).multiply(RATE_PER_1000);
        p = p.multiply(SPECIES.getOrDefault(in.factors().getOrDefault("species", "dog"), BigDecimal.ONE));
        p = p.multiply(BREED_GROUP.getOrDefault(in.factors().getOrDefault("breedGroup", "crossbreed"), BigDecimal.ONE));
        p = p.multiply(COVER.getOrDefault(in.factors().getOrDefault("cover", "accident"), BigDecimal.ONE));
        p = p.multiply(NEUTERED.getOrDefault(in.factors().getOrDefault("neutered", "yes"), BigDecimal.ONE));
        p = p.multiply(AREA.getOrDefault(area(in.postcode()), BigDecimal.ONE));
        p = p.multiply(ageLoading(in.holderAge()));
        p = p.multiply(BigDecimal.ONE.add(PRIOR_CLAIM_LOADING.multiply(BigDecimal.valueOf(in.priorClaims()))));
        return p.max(MINIMUM_PREMIUM).setScale(2, RoundingMode.HALF_UP);
    }

    BigDecimal ageLoading(int age) {
        if (age < 38) return new BigDecimal("1.07");
        if (age < 60) return new BigDecimal("1.0");
        if (age < 68) return new BigDecimal("0.98");
        return new BigDecimal("1.3");
    }

    @Override
    public Optional<String> referralReason(RatingInput in) {
        if (in.sumInsured().compareTo(MAX_SUM_INSURED) > 0) {
            return Optional.of("Sum insured above the Pet limit of 15,000");
        }
        if (in.priorClaims() >= REFER_PRIOR_CLAIMS) {
            return Optional.of(in.priorClaims() + " prior claims (refer at " + REFER_PRIOR_CLAIMS + ")");
        }
        if ("dangerous-dogs-act".equals(in.factors().get("breedGroup"))) {
            return Optional.of("Breed listed under the Dangerous Dogs Act");
        }
        return Optional.empty();
    }

    static String area(String postcode) {
        String outward = postcode == null ? "" : postcode.trim().split(" ")[0];
        String letters = outward.replaceAll("[0-9].*$", "");
        return AREA.containsKey(letters) ? letters : letters.isEmpty() ? "" : letters.substring(0, 1);
    }
}
