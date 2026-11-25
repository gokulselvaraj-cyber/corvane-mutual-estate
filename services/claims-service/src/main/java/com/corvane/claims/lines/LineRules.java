package com.corvane.claims.lines;

import com.corvane.claims.api.ClaimDtos.FnolRequest;
import com.corvane.claims.domain.Reserve;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

/** Routes to the per-line validator and reserve calculator (generated per product line under lines/<code>). */
@Component
public class LineRules {

    private final Map<String, LineValidator> validators;
    private final Map<String, LineReserveCalculator> reserves;

    public LineRules(List<LineValidator> validators, List<LineReserveCalculator> reserves) {
        this.validators = validators.stream().collect(Collectors.toMap(LineValidator::lineCode, Function.identity()));
        this.reserves = reserves.stream().collect(Collectors.toMap(LineReserveCalculator::lineCode, Function.identity()));
    }

    public void validate(String lineCode, FnolRequest request) {
        LineValidator v = validators.get(lineCode);
        if (v == null) {
            throw new IllegalArgumentException("Unknown line " + lineCode);
        }
        v.validate(request);
    }

    public Reserve initialReserve(String lineCode, FnolRequest request) {
        return reserves.get(lineCode).initialReserve(request);
    }

    public interface LineValidator {
        String lineCode();
        void validate(FnolRequest request);
    }

    public interface LineReserveCalculator {
        String lineCode();
        Reserve initialReserve(FnolRequest request);
    }
}
