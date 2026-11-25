package com.corvane.policy.api;

import com.corvane.policy.api.dto.BindRequest;
import com.corvane.policy.api.dto.PolicyView;
import com.corvane.policy.service.PolicyService;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/v1/policies")
public class PolicyController {

    private final PolicyService policyService;

    public PolicyController(PolicyService policyService) {
        this.policyService = policyService;
    }

    /** Called by claims-service PolicyAdminClient.getPolicy during FNOL (J1) and by the portal's PolicyView. */
    @GetMapping("/{policyNumber}")
    @PreAuthorize("hasAnyRole('CUSTOMER','ADJUSTER','CLAIMS_MANAGER','BROKER')")
    public PolicyView get(@PathVariable String policyNumber) {
        return PolicyView.from(policyService.find(policyNumber));
    }

    /** J4: bind an accepted quote into a live policy. */
    @PostMapping("/{quoteId}/bind")
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('CUSTOMER','BROKER')")
    public PolicyView bind(@PathVariable String quoteId, @RequestBody BindRequest request) {
        return PolicyView.from(policyService.bind(quoteId, request.inceptionDate(), request.brokerCode()));
    }
}
