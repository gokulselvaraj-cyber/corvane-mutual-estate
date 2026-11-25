package com.corvane.claimsv1;

import javax.servlet.http.*;
import java.io.IOException;
import java.math.BigDecimal;

/** v1 adjuster approval. Applied a flat 150 GBP excess. Retired 2023. */
public class ApproveServlet extends HttpServlet {

    static final BigDecimal FLAT_EXCESS = new BigDecimal("150");
    private final ClaimDao dao = new ClaimDao();

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        long id = Long.parseLong(req.getParameter("id"));
        BigDecimal approved = new BigDecimal(req.getParameter("approved"));
        dao.approve(id, approved.subtract(FLAT_EXCESS).max(BigDecimal.ZERO));
        resp.sendRedirect("claim.jsp?id=" + id);
    }
}
