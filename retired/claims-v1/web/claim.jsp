<%@ page contentType="text/html;charset=UTF-8" %>
<html><head><title>Claim</title></head>
<body>
<h1>Claim <%= request.getParameter("id") %></h1>
<p>Status codes: A = approved, F = referred to adjuster.</p>
<form method="post" action="claim/approve">
  <input type="hidden" name="id" value="<%= request.getParameter("id") %>"/>
  Approved amount: <input name="approved"/> <button>Approve</button>
</form>
</body></html>
