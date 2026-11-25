package com.corvane.policy.ledger;

import com.corvane.policy.domain.Policy;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.jdbc.core.simple.SimpleJdbcCall;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Date;
import java.util.Map;

/** Posts a bound premium to the Oracle ledger: LEDGER.PKG_POLICY_LEDGER.post_premium (data/oracle). */
@Component
public class LedgerClient {

    private final SimpleJdbcCall postPremium;

    public LedgerClient(@Qualifier("ledgerDataSource") DataSource ledger) {
        this.postPremium = new SimpleJdbcCall(ledger)
                .withSchemaName("LEDGER")
                .withCatalogName("PKG_POLICY_LEDGER")
                .withProcedureName("POST_PREMIUM");
    }

    public long postPremium(Policy p) {
        Map<String, Object> out = postPremium.execute(Map.of(
                "P_POLICY_NO", p.getPolicyNumber(),
                "P_PARTY_REF", p.getHolder().getPartyRef(),
                "P_LINE_CODE", p.getLine().name(),
                "P_PREMIUM", p.getAnnualPremium(),
                "P_IPT", p.getIptAmount(),
                "P_CURRENCY", p.getCurrency(),
                "P_EFFECTIVE", Date.valueOf(p.getInceptionDate())));
        return ((Number) out.get("P_POSTING_ID")).longValue();
    }
}
