package com.corvane.claims.subrogation;

import org.springframework.stereotype.Service;

import java.util.UUID;

/**
 * Recovering paid claim costs from a liable third party. Planned Q3 2027 (roadmap item CLM-SUBRO).
 * contracts/claims.openapi.yaml already lists POST /v1/claims/{id}/subrogate, but no controller maps it.
 */
@Service
public class SubrogationService {

    public void openRecovery(UUID claimId, String thirdPartyInsurer) {
        throw new UnsupportedOperationException("Subrogation is planned for Q3 2027");
    }
}
