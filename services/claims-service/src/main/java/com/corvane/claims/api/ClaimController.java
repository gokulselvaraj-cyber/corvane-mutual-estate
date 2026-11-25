package com.corvane.claims.api;

import com.corvane.claims.api.ClaimDtos.*;
import com.corvane.claims.service.ClaimApprovalService;
import com.corvane.claims.service.ClaimService;
import com.corvane.claims.service.ClaimSummaryService;
import com.corvane.claims.service.DraftClaimService;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.net.URI;
import java.util.List;
import java.util.UUID;

/** REST entry point for claims. Journey J1 (FNOL) starts at {@link #register}, J2 (payout) at {@link #approve}. */
@RestController
@RequestMapping("/v1/claims")
public class ClaimController {

    private final ClaimService claimService;
    private final DraftClaimService draftService;
    private final ClaimApprovalService approvalService;
    private final ClaimSummaryService summaryService;

    public ClaimController(ClaimService claimService, DraftClaimService draftService,
                           ClaimApprovalService approvalService, ClaimSummaryService summaryService) {
        this.claimService = claimService;
        this.draftService = draftService;
        this.approvalService = approvalService;
        this.summaryService = summaryService;
    }

    /** FNOL submit from the portal wizard (step "Submit") or an adjuster keying a phone claim. */
    @PostMapping
    @PreAuthorize("hasAnyRole('CUSTOMER','ADJUSTER')")
    public ResponseEntity<ClaimResponse> register(@Valid @RequestBody FnolRequest request,
                                                  @AuthenticationPrincipal Jwt jwt) {
        ClaimResponse created = claimService.register(request, jwt.getSubject());
        return ResponseEntity.created(URI.create("/v1/claims/" + created.claimId())).body(created);
    }

    @PostMapping("/drafts")
    @PreAuthorize("hasRole('CUSTOMER')")
    public DraftResponse startDraft(@RequestBody DraftRequest request, @AuthenticationPrincipal Jwt jwt) {
        return draftService.start(request, jwt.getSubject());
    }

    @PostMapping(path = "/drafts/{id}/photos", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @PreAuthorize("hasRole('CUSTOMER')")
    public PhotoResponse addPhoto(@PathVariable UUID id, @RequestPart("file") MultipartFile file) {
        return draftService.attachPhoto(id, file);
    }

    @PutMapping("/{id}/approve")
    @PreAuthorize("hasAnyRole('ADJUSTER','CLAIMS_MANAGER')")
    public ClaimResponse approve(@PathVariable UUID id, @RequestBody ApprovalRequest request,
                                 @AuthenticationPrincipal Jwt jwt) {
        return approvalService.approve(id, request, jwt.getSubject());
    }

    /** Strangler replacement for CICS transaction CLMI (program CLMINQ0, map CLMINQM). */
    @GetMapping("/{id}/summary")
    @PreAuthorize("hasAnyRole('ADJUSTER','CLAIMS_MANAGER','CUSTOMER')")
    public ClaimSummaryDto summary(@PathVariable UUID id) {
        return summaryService.summarise(id);
    }

    /** MI export. NOTE: opened in SecurityConfig for the reporting box; see ticket SEC-418. */
    @GetMapping(path = "/export", produces = "text/csv")
    public String export(@RequestParam(defaultValue = "30") int days) {
        List<ClaimSummaryDto> rows = summaryService.recent(days);
        StringBuilder csv = new StringBuilder("claim_id,policy_number,line,status,claimant_name,date_of_birth,amount\n");
        rows.forEach(r -> csv.append(r.toCsvRow()).append('\n'));
        return csv.toString();
    }
}
