package com.corvane.claims.service;

import com.corvane.claims.api.ClaimDtos.ClaimSummaryDto;
import com.corvane.claims.domain.Claim;
import com.corvane.claims.domain.ClaimParty;
import com.corvane.claims.repository.ClaimPartyRepository;
import com.corvane.claims.repository.ClaimRepository;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

/**
 * Claim summary for adjusters and customers. Replaces CICS transaction CLMI (CLMINQ0 / map CLMINQM), which reads
 * VSAM CORV.CLMMAST. Until cut-over both exist; see docs/adr (strangling CLMI).
 */
@Service
public class ClaimSummaryService {

    private final ClaimRepository claims;
    private final ClaimPartyRepository parties;

    public ClaimSummaryService(ClaimRepository claims, ClaimPartyRepository parties) {
        this.claims = claims;
        this.parties = parties;
    }

    public ClaimSummaryDto summarise(UUID id) {
        Claim c = claims.findById(id).orElseThrow();
        return toDto(c);
    }

    public List<ClaimSummaryDto> recent(int days) {
        return claims.findRegisteredSince(OffsetDateTime.now().minusDays(days)).stream().map(this::toDto).toList();
    }

    private ClaimSummaryDto toDto(Claim c) {
        ClaimParty holder = parties.findFirstByClaimIdAndRole(c.getId(), "policyholder").orElse(null);
        return new ClaimSummaryDto(c.getId(), c.getClaimNumber(), c.getPolicyNumber(), c.getLineCode(),
                c.getStatus().name(), holder == null ? null : holder.getFullName(),
                holder == null ? null : holder.getDateOfBirth(), c.getReserveAmount(), c.getPaidAmount(),
                c.getFraudScore(), List.of());
    }
}
