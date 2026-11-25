package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import com.corvane.policy.domain.RatingResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;

class RatingServiceTest {

    private PremiumEngine engine;
    private RatingService rating;

    @BeforeEach
    void setUp() {
        engine = mock(PremiumEngine.class);
        PremiumEngineRouter router = mock(PremiumEngineRouter.class);
        when(router.select()).thenReturn(engine);
        when(engine.name()).thenReturn("java");
        rating = new RatingService(router, new BigDecimal("0.12"), new BigDecimal("0.20"), List.of("TRV", "GDG"));
    }

    private RatingInput input(ProductLine line, String voluntary) {
        return new RatingInput(line, "LS1 4AP", 40, new BigDecimal("20000"), new BigDecimal(voluntary), 0, Map.of());
    }

    @Test
    void excessIsCompulsory250PlusVoluntary() {
        assertThat(rating.applyExcess(new BigDecimal("100"))).isEqualByComparingTo("350");
    }

    @Test
    void excessRoundsHalfUp() {
        assertThat(rating.applyExcess(new BigDecimal("99.50"))).isEqualByComparingTo("350");
        assertThat(rating.applyExcess(new BigDecimal("99.49"))).isEqualByComparingTo("349");
    }

    @Test
    void negativeVoluntaryExcessIsIgnored() {
        assertThat(rating.applyExcess(new BigDecimal("-50"))).isEqualByComparingTo("250");
    }

    @Test
    void standardIptForMotor() {
        when(engine.price(any())).thenReturn(new PremiumEngine.Priced(new BigDecimal("500.00"), null));
        RatingResult r = rating.rate(input(ProductLine.MTR, "0"));
        assertThat(r.ipt()).isEqualByComparingTo("60.00");
        assertThat(r.totalPremium()).isEqualByComparingTo("560.00");
        assertThat(r.engine()).isEqualTo("java");
    }

    @Test
    void higherIptForTravelAndGadget() {
        when(engine.price(any())).thenReturn(new PremiumEngine.Priced(new BigDecimal("100.00"), null));
        assertThat(rating.rate(input(ProductLine.TRV, "0")).ipt()).isEqualByComparingTo("20.00");
        assertThat(rating.rate(input(ProductLine.GDG, "0")).ipt()).isEqualByComparingTo("20.00");
    }

    @Test
    void referralReasonIsPassedThrough() {
        when(engine.price(any())).thenReturn(new PremiumEngine.Priced(new BigDecimal("900.00"), "Sum insured above line limit"));
        assertThat(rating.rate(input(ProductLine.HOM, "0")).referralReason()).contains("line limit");
    }
}
