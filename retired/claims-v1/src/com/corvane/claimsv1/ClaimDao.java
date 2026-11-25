package com.corvane.claimsv1;

import javax.naming.InitialContext;
import javax.sql.DataSource;
import java.math.BigDecimal;
import java.sql.*;

/** JDBC access to the old CLAIMS_V1 table (dropped 2024). Note the string-built SQL in findByPolicy. */
public class ClaimDao {

    private DataSource ds() {
        try {
            return (DataSource) new InitialContext().lookup("java:comp/env/jdbc/ClaimsDS");
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    public long insert(String policy, String cause, String details, BigDecimal amount, String status) {
        String sql = "INSERT INTO CLAIMS_V1 (POLICY_NO, CAUSE, DETAILS, AMOUNT, STATUS) VALUES (?,?,?,?,?)";
        try (Connection c = ds().getConnection(); PreparedStatement ps = c.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            ps.setString(1, policy); ps.setString(2, cause); ps.setString(3, details);
            ps.setBigDecimal(4, amount); ps.setString(5, status);
            ps.executeUpdate();
            ResultSet keys = ps.getGeneratedKeys();
            keys.next();
            return keys.getLong(1);
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    public void approve(long id, BigDecimal payable) {
        try (Connection c = ds().getConnection();
             PreparedStatement ps = c.prepareStatement("UPDATE CLAIMS_V1 SET STATUS='A', PAYABLE=? WHERE ID=?")) {
            ps.setBigDecimal(1, payable); ps.setLong(2, id);
            ps.executeUpdate();
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    public ResultSet findByPolicy(Connection c, String policy) throws SQLException {
        return c.createStatement().executeQuery("SELECT * FROM CLAIMS_V1 WHERE POLICY_NO = '" + policy + "'");
    }
}
