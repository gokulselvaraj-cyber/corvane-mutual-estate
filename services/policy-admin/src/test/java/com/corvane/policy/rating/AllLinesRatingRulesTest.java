package com.corvane.policy.rating;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/** Rating rules for all twelve product lines: minimum premium, prior-claims loading and referral triggers. */
class AllLinesRatingRulesTest {

    @Nested
    class Mtr {

        private final MtrRatingRules rules = new MtrRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.MTR, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return MtrRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("30000"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("30000"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("120001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("30000"), 3, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("30000"), 2, Map.of()))).isEmpty();
        }

        @Test
        void refers_vehicleGroup_41_50() {
            assertThat(rules.referralReason(input(new BigDecimal("30000"), 0, Map.of("vehicleGroup", "41-50")))).contains("Vehicle group 41-50 needs underwriter review");
        }
    }

    @Nested
    class Hom {

        private final HomRatingRules rules = new HomRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.HOM, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return HomRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("250000"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("250000"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("2000001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 3, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 2, Map.of()))).isEmpty();
        }

        @Test
        void refers_floodZone_3() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 0, Map.of("floodZone", "3")))).contains("Flood zone 3");
        }
    }

    @Nested
    class Cnt {

        private final CntRatingRules rules = new CntRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.CNT, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return CntRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("37500"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("37500"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("150001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("37500"), 4, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("37500"), 3, Map.of()))).isEmpty();
        }
    }

    @Nested
    class Trv {

        private final TrvRatingRules rules = new TrvRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.TRV, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return TrvRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("250000"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("250000"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("10000001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 2, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 1, Map.of()))).isEmpty();
        }

        @Test
        void refers_medicalConditions_declared() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 0, Map.of("medicalConditions", "declared")))).contains("Declared medical conditions need screening");
        }
    }

    @Nested
    class Pet {

        private final PetRatingRules rules = new PetRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.PET, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return PetRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("3750"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("3750"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("15001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("3750"), 3, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("3750"), 2, Map.of()))).isEmpty();
        }

        @Test
        void refers_breedGroup_dangerous_dogs_act() {
            assertThat(rules.referralReason(input(new BigDecimal("3750"), 0, Map.of("breedGroup", "dangerous-dogs-act")))).contains("Breed listed under the Dangerous Dogs Act");
        }
    }

    @Nested
    class Lld {

        private final LldRatingRules rules = new LldRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.LLD, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return LldRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("250000"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("250000"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("3000001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 2, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 1, Map.of()))).isEmpty();
        }

        @Test
        void refers_unoccupiedDays_60_() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 0, Map.of("unoccupiedDays", "60+")))).contains("Unoccupied over 60 days");
        }
    }

    @Nested
    class Mar {

        private final MarRatingRules rules = new MarRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.MAR, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return MarRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("250000"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("250000"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("25000001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 4, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 3, Map.of()))).isEmpty();
        }

        @Test
        void refers_route_high_risk_waters() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 0, Map.of("route", "high-risk-waters")))).contains("Route through listed high-risk waters");
        }
    }

    @Nested
    class Cpr {

        private final CprRatingRules rules = new CprRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.CPR, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return CprRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("250000"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("250000"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("50000001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 4, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 3, Map.of()))).isEmpty();
        }

        @Test
        void refers_construction_composite_panel() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 0, Map.of("construction", "composite-panel")))).contains("Composite panel construction");
        }
    }

    @Nested
    class Plb {

        private final PlbRatingRules rules = new PlbRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.PLB, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return PlbRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("250000"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("250000"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("10000001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 3, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 2, Map.of()))).isEmpty();
        }

        @Test
        void refers_workAtHeight_over_10m() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 0, Map.of("workAtHeight", "over-10m")))).contains("Work at height above 10m");
        }
    }

    @Nested
    class Pin {

        private final PinRatingRules rules = new PinRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.PIN, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return PinRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("250000"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("250000"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("5000001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 3, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 2, Map.of()))).isEmpty();
        }

        @Test
        void refers_usWork__10_() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 0, Map.of("usWork", ">10%")))).contains("More than 10% US work");
        }
    }

    @Nested
    class Cyb {

        private final CybRatingRules rules = new CybRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.CYB, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return CybRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("250000"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("250000"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("5000001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 2, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 1, Map.of()))).isEmpty();
        }

        @Test
        void refers_mfa_none() {
            assertThat(rules.referralReason(input(new BigDecimal("250000"), 0, Map.of("mfa", "none")))).contains("No multi-factor authentication");
        }
    }

    @Nested
    class Gdg {

        private final GdgRatingRules rules = new GdgRatingRules();

        private RatingInput input(BigDecimal sumInsured, int priorClaims, Map<String, String> factors) {
            return new RatingInput(ProductLine.GDG, "ZZ1 1AA", 45, sumInsured, BigDecimal.ZERO, priorClaims, factors);
        }

        @Test
        void neverBelowMinimumPremium() {
            assertThat(rules.basePremium(input(BigDecimal.ONE, 0, Map.of()))).isEqualByComparingTo(MINIMUM());
        }

        private static BigDecimal MINIMUM() { return GdgRatingRules.MINIMUM_PREMIUM; }

        @Test
        void priorClaimsLoadThePremium() {
            BigDecimal clean = rules.basePremium(input(new BigDecimal("1500"), 0, Map.of()));
            BigDecimal one = rules.basePremium(input(new BigDecimal("1500"), 1, Map.of()));
            assertThat(one).isGreaterThanOrEqualTo(clean);
        }

        @Test
        void refersAboveLineLimit() {
            assertThat(rules.referralReason(input(new BigDecimal("6001"), 0, Map.of()))).isPresent();
        }

        @Test
        void refersOnPriorClaims() {
            assertThat(rules.referralReason(input(new BigDecimal("1500"), 2, Map.of()))).isPresent();
            assertThat(rules.referralReason(input(new BigDecimal("1500"), 1, Map.of()))).isEmpty();
        }
    }
}
