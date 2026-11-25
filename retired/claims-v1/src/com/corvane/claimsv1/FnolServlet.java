package com.corvane.claimsv1;

import javax.servlet.http.*;
import java.io.IOException;
import java.math.BigDecimal;

/** v1 FNOL form post. Retired 2023. */
public class FnolServlet extends HttpServlet {

    static final BigDecimal AUTO_APPROVE_LIMIT = new BigDecimal("1000");
    private final ClaimDao dao = new ClaimDao();

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String policy = req.getParameter("policyNo");
        BigDecimal amount = new BigDecimal(req.getParameter("amount"));
        String status = amount.compareTo(AUTO_APPROVE_LIMIT) <= 0 ? "A" : "F";
        long id = dao.insert(policy, req.getParameter("cause"), req.getParameter("details"), amount, status);
        resp.sendRedirect("claim.jsp?id=" + id);
    }
}
