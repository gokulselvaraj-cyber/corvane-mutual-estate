package com.corvane.policy.service;

import com.corvane.policy.domain.ProductLine;
import com.corvane.policy.domain.RatingInput;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.nio.charset.Charset;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class MainframePremiumAdapterTest {

    private final MainframePremiumAdapter adapter = new MainframePremiumAdapter("localhost", 2006, "CORVCTG1", "PRMCALC0", 4000);

    @Test
    void commareaIsEbcdicPrmcommLayout() {
        byte[] area = adapter.toCommarea(new RatingInput(ProductLine.HOM, "LS1 4AP", 52, new BigDecimal("350000.00"),
                new BigDecimal("100.00"), 1, Map.of()));
        assertThat(area).hasSize(MainframePremiumAdapter.COMMAREA_LENGTH);
        assertThat(new String(area, 0, 3, Charset.forName("Cp037"))).isEqualTo("HOM");
    }

    @Test
    void parsesPremiumAndReferral() {
        StringBuilder s = new StringBuilder(" ".repeat(200));
        s.replace(100, 111, "00000045678");
        s.replace(111, 112, "Y");
        s.replace(112, 130, "FLOOD ZONE 3      ");
        PremiumEngine.Priced p = adapter.fromCommarea(s.toString().getBytes(Charset.forName("Cp037")));
        assertThat(p.basePremium()).isEqualByComparingTo("456.78");
        assertThat(p.referralReason()).isEqualTo("FLOOD ZONE 3");
    }
}
