package com.corvane.claims.repository;

import com.corvane.claims.domain.ClaimParty;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;
import java.util.UUID;

public interface ClaimPartyRepository extends JpaRepository<ClaimParty, UUID> {
    Optional<ClaimParty> findFirstByClaimIdAndRole(UUID claimId, String role);
}
