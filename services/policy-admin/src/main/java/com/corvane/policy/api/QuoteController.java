package com.corvane.policy.api;

import com.corvane.policy.api.dto.QuoteRequest;
import com.corvane.policy.api.dto.QuoteResponse;
import com.corvane.policy.service.QuoteService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

/** J4 entry point: the customer portal's QuotePage posts here. */
@RestController
@RequestMapping("/v1/quotes")
public class QuoteController {

    private final QuoteService quoteService;

    public QuoteController(QuoteService quoteService) {
        this.quoteService = quoteService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    @PreAuthorize("hasAnyRole('CUSTOMER','BROKER')")
    public QuoteResponse quote(@Valid @RequestBody QuoteRequest request) {
        return QuoteResponse.from(quoteService.quote(request));
    }
}
