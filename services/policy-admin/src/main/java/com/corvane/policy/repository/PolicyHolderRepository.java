package com.corvane.policy.repository;

import com.corvane.policy.domain.PolicyHolder;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface PolicyHolderRepository extends JpaRepository<PolicyHolder, Long> {
    Optional<PolicyHolder> findByPartyRef(String partyRef);
}
