"""Builder B, part 2: retired/claims-v1, mobile/adjuster-app, claims contracts. Run: python3 -I b_core2.py <estate_root>"""
import json
import os
import sys

ROOT = sys.argv[1]
F = {}

# ---------------- retired/claims-v1 ----------------
RV = "retired/claims-v1"
RJ = RV + "/src/com/corvane/claimsv1"
F[RV + "/README.md"] = """# claims-v1 (RETIRED)

The original servlet-based claims application, 2011–2023. **Retired 2023-06-30** when claims-service went live.
Kept for audit reference only. Not built, not deployed, not tested.

Rules as they were in claims-v1 (do not use, superseded):
- Auto-approve claims up to 1,000 GBP.
- Flat excess of 150 GBP on every claim.
- Fraud check was a manual adjuster tick-box.
"""
F[RV + "/WEB-INF/web.xml"] = """<?xml version="1.0" encoding="UTF-8"?>
<web-app xmlns="http://java.sun.com/xml/ns/javaee" version="2.5">
  <display-name>Corvane Claims v1</display-name>
  <servlet><servlet-name>fnol</servlet-name><servlet-class>com.corvane.claimsv1.FnolServlet</servlet-class></servlet>
  <servlet><servlet-name>approve</servlet-name><servlet-class>com.corvane.claimsv1.ApproveServlet</servlet-class></servlet>
  <servlet-mapping><servlet-name>fnol</servlet-name><url-pattern>/claim/new</url-pattern></servlet-mapping>
  <servlet-mapping><servlet-name>approve</servlet-name><url-pattern>/claim/approve</url-pattern></servlet-mapping>
  <resource-ref><res-ref-name>jdbc/ClaimsDS</res-ref-name><res-type>javax.sql.DataSource</res-type></resource-ref>
</web-app>
"""
F[RJ + "/FnolServlet.java"] = """package com.corvane.claimsv1;

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
"""
F[RJ + "/ApproveServlet.java"] = """package com.corvane.claimsv1;

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
"""
F[RJ + "/ClaimDao.java"] = """package com.corvane.claimsv1;

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
"""
F[RV + "/web/claim.jsp"] = """<%@ page contentType="text/html;charset=UTF-8" %>
<html><head><title>Claim</title></head>
<body>
<h1>Claim <%= request.getParameter("id") %></h1>
<p>Status codes: A = approved, F = referred to adjuster.</p>
<form method="post" action="claim/approve">
  <input type="hidden" name="id" value="<%= request.getParameter("id") %>"/>
  Approved amount: <input name="approved"/> <button>Approve</button>
</form>
</body></html>
"""

# ---------------- mobile/adjuster-app ----------------
M = "mobile/adjuster-app"
MK = M + "/app/src/main/java/com/corvane/adjuster"
F[M + "/README.md"] = """# Corvane Adjuster (Android)

Field adjuster app: list referred claims, view a claim, approve it, and book an inspection slot.
Kotlin, Jetpack Compose, minSdk 28. Calls claims-service with the adjuster's JWT.

No automated tests yet (backlog item MOB-12).
"""
F[M + "/settings.gradle.kts"] = """rootProject.name = "corvane-adjuster"
include(":app")
"""
F[M + "/app/build.gradle.kts"] = """plugins {
    id("com.android.application") version "8.4.1"
    id("org.jetbrains.kotlin.android") version "1.9.24"
}

android {
    namespace = "com.corvane.adjuster"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.corvane.adjuster"
        minSdk = 28
        targetSdk = 34
        versionCode = 41
        versionName = "1.8.0"
        buildConfigField("String", "CLAIMS_API", "\\"https://api.corvane.internal/claims/\\"")
    }
    buildFeatures { compose = true; buildConfig = true }
    composeOptions { kotlinCompilerExtensionVersion = "1.5.14" }
}

dependencies {
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation("androidx.compose.material3:material3:1.2.1")
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-moshi:2.11.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.8.1")
}
"""
F[M + "/app/src/main/AndroidManifest.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.CAMERA" />
    <application android:label="Corvane Adjuster" android:allowBackup="true">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""
F[M + "/app/src/main/res/layout/activity_main.xml"] = """<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/compose_host"
    android:layout_width="match_parent"
    android:layout_height="match_parent" />
"""
F[MK + "/MainActivity.kt"] = """package com.corvane.adjuster

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val tokens = TokenStore(this)
        val api = ClaimsApi.create(BuildConfig.CLAIMS_API, tokens)
        setContent {
            var selected by remember { mutableStateOf<String?>(null) }
            if (selected == null) {
                ClaimListScreen(api) { selected = it }
            } else {
                ApproveClaimScreen(api, selected!!) { selected = null }
            }
        }
    }
}
"""
F[MK + "/ClaimsApi.kt"] = """package com.corvane.adjuster

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.*
import java.math.BigDecimal

data class ClaimSummary(val claimId: String, val claimNumber: String, val policyNumber: String,
                        val lineCode: String, val status: String, val reserveAmount: BigDecimal?,
                        val fraudScore: Double?)

data class ApprovalRequest(val approvedAmount: BigDecimal, val note: String?)
data class ClaimResponse(val claimId: String, val claimNumber: String, val status: String)

/** claims-service endpoints used by the adjuster app. */
interface ClaimsApi {
    @GET("v1/claims/{id}/summary")
    suspend fun summary(@Path("id") id: String): ClaimSummary

    @GET("v1/claims/export")
    suspend fun referredCsv(@Query("days") days: Int = 14): String

    @PUT("v1/claims/{id}/approve")
    suspend fun approve(@Path("id") id: String, @Body body: ApprovalRequest): ClaimResponse

    companion object {
        fun create(baseUrl: String, tokens: TokenStore): ClaimsApi {
            val client = OkHttpClient.Builder().addInterceptor { chain ->
                val req = chain.request().newBuilder()
                    .header("Authorization", "Bearer " + (tokens.accessToken() ?: ""))
                    .build()
                chain.proceed(req)
            }.build()
            return Retrofit.Builder().baseUrl(baseUrl).client(client)
                .addConverterFactory(MoshiConverterFactory.create()).build().create(ClaimsApi::class.java)
        }
    }
}
"""
F[MK + "/TokenStore.kt"] = """package com.corvane.adjuster

import android.content.Context

/**
 * Keeps the adjuster's access and refresh tokens between launches.
 * Plain SharedPreferences (not EncryptedSharedPreferences): flagged in pen test PT-2026-04, not yet fixed.
 */
class TokenStore(context: Context) {
    private val prefs = context.getSharedPreferences("corvane_auth", Context.MODE_PRIVATE)

    fun save(access: String, refresh: String) {
        prefs.edit().putString("access_token", access).putString("refresh_token", refresh).apply()
    }

    fun accessToken(): String? = prefs.getString("access_token", null)
    fun refreshToken(): String? = prefs.getString("refresh_token", null)
    fun clear() = prefs.edit().clear().apply()
}
"""
F[MK + "/ClaimListScreen.kt"] = """package com.corvane.adjuster

import androidx.compose.foundation.clickable
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier

/** Referred claims for this adjuster. Uses the CSV export endpoint because there is no list endpoint yet. */
@Composable
fun ClaimListScreen(api: ClaimsApi, onOpen: (String) -> Unit) {
    var rows by remember { mutableStateOf(listOf<List<String>>()) }
    LaunchedEffect(Unit) {
        rows = api.referredCsv().lines().drop(1).filter { it.isNotBlank() }.map { it.split(",") }
            .filter { it.getOrNull(3) == "REFERRED" }
    }
    LazyColumn {
        items(rows) { r ->
            ListItem(
                headlineContent = { Text("${r[1]}  ${r[2]}") },
                supportingContent = { Text("Reserve ${r.getOrNull(6) ?: "-"}") },
                modifier = Modifier.clickable { onOpen(r[0]) })
        }
    }
}
"""
F[MK + "/ApproveClaimScreen.kt"] = """package com.corvane.adjuster

import androidx.compose.foundation.layout.Column
import androidx.compose.material3.*
import androidx.compose.runtime.*
import kotlinx.coroutines.launch
import java.math.BigDecimal

/** Journey J2 from the field: approve a referred claim -> claims-service PUT /v1/claims/{id}/approve. */
@Composable
fun ApproveClaimScreen(api: ClaimsApi, claimId: String, onDone: () -> Unit) {
    val scope = rememberCoroutineScope()
    var summary by remember { mutableStateOf<ClaimSummary?>(null) }
    var amount by remember { mutableStateOf("") }
    var slot by remember { mutableStateOf<ReserveSlot?>(null) }
    LaunchedEffect(claimId) { summary = api.summary(claimId) }
    Column {
        Text(summary?.claimNumber ?: "Loading")
        Text("Fraud score: ${summary?.fraudScore ?: "-"}")
        OutlinedTextField(value = amount, onValueChange = { amount = it }, label = { Text("Approved amount (GBP)") })
        Button(onClick = { slot = ReserveSlot.nextFree(claimId) }) { Text("Book inspection") }
        slot?.let { Text("Inspection ${it.label()}") }
        Button(onClick = {
            scope.launch {
                api.approve(claimId, ApprovalRequest(BigDecimal(amount), "approved in field"))
                onDone()
            }
        }) { Text("Approve") }
    }
}
"""
F[MK + "/ReserveSlot.kt"] = """package com.corvane.adjuster

import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/**
 * An inspection appointment slot the adjuster reserves with the claimant. Nothing to do with a claim reserve
 * (money set aside, com.corvane.claims.domain.Reserve in claims-service).
 */
data class ReserveSlot(val claimId: String, val start: LocalDateTime, val minutes: Int) {
    fun label(): String = start.format(DateTimeFormatter.ofPattern("EEE d MMM HH:mm")) + " ($minutes min)"

    companion object {
        fun nextFree(claimId: String): ReserveSlot {
            val now = LocalDateTime.now().plusDays(1).withHour(9).withMinute(0)
            return ReserveSlot(claimId, now, 45)
        }
    }
}
"""

# ---------------- contracts ----------------
F["contracts/claims.openapi.yaml"] = """openapi: 3.0.3
info:
  title: Corvane Claims API
  version: 2.3.0
  description: claims-service public API. Owner team-fnol.
servers:
  - url: https://api.corvane.internal/claims
security:
  - bearerAuth: []
paths:
  /v1/claims:
    post:
      operationId: registerClaim
      summary: First notice of loss
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/FnolRequest' }
      responses:
        '201': { description: Registered, content: { application/json: { schema: { $ref: '#/components/schemas/ClaimResponse' } } } }
        '422': { description: Not covered }
  /v1/claims/drafts:
    post:
      operationId: startDraft
      requestBody:
        content:
          application/json:
            schema: { type: object, properties: { policyNumber: { type: string } } }
      responses:
        '200': { description: Draft started }
  /v1/claims/drafts/{id}/photos:
    post:
      operationId: addDraftPhoto
      parameters: [ { name: id, in: path, required: true, schema: { type: string, format: uuid } } ]
      requestBody:
        content:
          multipart/form-data:
            schema: { type: object, properties: { file: { type: string, format: binary } } }
      responses:
        '200': { description: Stored }
  /v1/claims/{id}/approve:
    put:
      operationId: approveClaim
      parameters: [ { name: id, in: path, required: true, schema: { type: string, format: uuid } } ]
      requestBody:
        content:
          application/json:
            schema: { $ref: '#/components/schemas/ApprovalRequest' }
      responses:
        '200': { description: Approved }
        '409': { description: Claim not in REFERRED state }
  /v1/claims/{id}/summary:
    get:
      operationId: getClaimSummary
      parameters: [ { name: id, in: path, required: true, schema: { type: string, format: uuid } } ]
      responses:
        '200': { description: Summary, content: { application/json: { schema: { $ref: '#/components/schemas/ClaimSummary' } } } }
  /v1/claims/{id}/subrogate:
    post:
      operationId: subrogateClaim
      summary: Open a recovery against a liable third party
      parameters: [ { name: id, in: path, required: true, schema: { type: string, format: uuid } } ]
      requestBody:
        content:
          application/json:
            schema: { type: object, properties: { thirdPartyInsurer: { type: string } } }
      responses:
        '202': { description: Recovery opened }
  /v1/claims/export:
    get:
      operationId: exportClaims
      security: []
      parameters: [ { name: days, in: query, schema: { type: integer, default: 30 } } ]
      responses:
        '200': { description: CSV, content: { text/csv: { schema: { type: string } } } }
components:
  securitySchemes:
    bearerAuth: { type: http, scheme: bearer, bearerFormat: JWT }
  schemas:
    FnolRequest:
      type: object
      required: [policyNumber, incidentDate, lossCause, estimatedAmount]
      properties:
        policyNumber: { type: string, pattern: '^[A-Z]{3}-\\d{8}$' }
        incidentDate: { type: string, format: date }
        lossCause: { type: string }
        description: { type: string, maxLength: 4000 }
        injuryNotes: { type: string, maxLength: 4000 }
        estimatedAmount: { type: number }
        incidentPostcode: { type: string }
        draftId: { type: string, format: uuid }
    ClaimResponse:
      type: object
      properties:
        claimId: { type: string, format: uuid }
        claimNumber: { type: string }
        status: { type: string, enum: [REGISTERED, REFERRED, APPROVED, PAID, CLOSED, DECLINED] }
        triageOutcome: { type: string, enum: [AUTO_APPROVE, REFER_ADJUSTER, REFER_FRAUD] }
        reserveAmount: { type: number }
        registeredAt: { type: string, format: date-time }
    ApprovalRequest:
      type: object
      required: [approvedAmount]
      properties:
        approvedAmount: { type: number }
        note: { type: string }
    ClaimSummary:
      type: object
      properties:
        claimId: { type: string, format: uuid }
        claimNumber: { type: string }
        policyNumber: { type: string }
        lineCode: { type: string }
        status: { type: string }
        claimantName: { type: string }
        reserveAmount: { type: number }
        paidAmount: { type: number }
        fraudScore: { type: number }
"""

F["contracts/claims-events.asyncapi.yaml"] = """asyncapi: 2.6.0
info:
  title: Corvane claims and payments events
  version: 1.4.0
servers:
  confluent:
    url: pkc-corvane.europe-west2.gcp.confluent.cloud:9092
    protocol: kafka-secure
channels:
  policies.bound.v1:
    description: A policy was bound. Producer policy-admin; consumers broker-commissions, notifications.
    subscribe: { message: { $ref: '#/components/messages/PolicyBound' } }
  claims.registered.v1:
    description: A claim was registered (FNOL). Producer claims-service; consumers notifications, fraud-scoring.
    subscribe: { message: { $ref: '#/components/messages/ClaimRegistered' } }
  claims.approved.v1:
    description: A claim was approved for payment. Producer claims-service; consumer payments-gateway.
    subscribe: { message: { $ref: '#/components/messages/ClaimApproved' } }
  payments.settled.v1:
    description: The bank settled a payout. Producer payments-gateway; consumer claims-service.
    subscribe: { message: { $ref: '#/components/messages/PaymentSettled' } }
  claims.closed.v1:
    description: A claim was closed. Producer claims-service; consumer warehouse-loader.
    subscribe: { message: { $ref: '#/components/messages/ClaimClosed' } }
  claims.reopened.v1:
    description: A closed claim was reopened. Reserved for the reopen feature (CLM-REOPEN); no producer yet.
    subscribe: { message: { $ref: '#/components/messages/ClaimReopened' } }
components:
  messages:
    PolicyBound: { payload: { $ref: 'avro/policy-bound.avsc' }, schemaFormat: application/vnd.apache.avro;version=1.9.0 }
    ClaimRegistered: { payload: { $ref: 'avro/claim-registered.avsc' }, schemaFormat: application/vnd.apache.avro;version=1.9.0 }
    ClaimApproved: { payload: { $ref: 'avro/claim-approved.avsc' }, schemaFormat: application/vnd.apache.avro;version=1.9.0 }
    PaymentSettled: { payload: { $ref: 'avro/payment-settled.avsc' }, schemaFormat: application/vnd.apache.avro;version=1.9.0 }
    ClaimClosed: { payload: { $ref: 'avro/claim-closed.avsc' }, schemaFormat: application/vnd.apache.avro;version=1.9.0 }
    ClaimReopened: { payload: { $ref: 'avro/claim-reopened.avsc' }, schemaFormat: application/vnd.apache.avro;version=1.9.0 }
"""

def avro(name, doc, fields):
    return json.dumps({"type": "record", "name": name, "namespace": "com.corvane.events", "doc": doc,
                       "fields": [{"name": n, "type": t} for n, t in fields]}, indent=2) + "\n"

F["contracts/avro/policy-bound.avsc"] = avro("PolicyBound", "policies.bound.v1", [
    ("policyNumber", "string"), ("lineCode", "string"), ("brokerId", ["null", "string"]),
    ("annualPremium", "string"), ("currency", "string"), ("boundAt", "string")])
F["contracts/avro/claim-registered.avsc"] = avro("ClaimRegistered", "claims.registered.v1", [
    ("claimId", "string"), ("claimNumber", "string"), ("policyNumber", "string"), ("lineCode", "string"),
    ("status", "string"), ("holderEmail", "string"), ("holderName", "string"), ("occurredAt", "string")])
F["contracts/avro/claim-approved.avsc"] = avro("ClaimApproved", "claims.approved.v1", [
    ("claimId", "string"), ("claimNumber", "string"), ("policyNumber", "string"), ("payableAmount", "string"),
    ("currency", "string"), ("occurredAt", "string")])
F["contracts/avro/payment-settled.avsc"] = avro("PaymentSettled", "payments.settled.v1", [
    ("paymentId", "string"), ("claimId", "string"), ("amount", "string"), ("currency", "string"),
    ("bankReference", "string"), ("settledAt", "string")])
F["contracts/avro/claim-closed.avsc"] = avro("ClaimClosed", "claims.closed.v1", [
    ("claimId", "string"), ("claimNumber", "string"), ("lineCode", "string"), ("paidAmount", "string"),
    ("occurredAt", "string")])
F["contracts/avro/claim-reopened.avsc"] = avro("ClaimReopened", "claims.reopened.v1 (no producer yet)", [
    ("claimId", "string"), ("reason", "string"), ("reopenedBy", "string"), ("occurredAt", "string")])

F["contracts/fraud-scoring.proto"] = """syntax = "proto3";

// Planned gRPC interface for fraud scoring (design review 2024-05). NOT IMPLEMENTED:
// claims-service calls fraud-scoring over HTTP JSON (POST /v1/score).
package corvane.fraud.v1;

option java_package = "com.corvane.fraud.v1";

service FraudScoring {
  rpc Score (ScoreRequest) returns (ScoreReply);
  rpc Explain (ExplainRequest) returns (ExplainReply);
}

message ScoreRequest {
  string claim_number = 1;
  string line_code = 2;
  string loss_cause = 3;
  double estimated_amount = 4;
  string description = 5;
  int32 prior_claims_3y = 6;
}

message ScoreReply {
  double score = 1;
  string band = 2;
  repeated string reasons = 3;
}

message ExplainRequest { string claim_number = 1; }
message ExplainReply { repeated string features = 1; }
"""

F["contracts/notifications.graphql"] = """# Read-only GraphQL view over notifications sent to a customer (portal "My messages").
schema {
  query: Query
}

type Query {
  notifications(policyNumber: String!, limit: Int = 20): [Notification!]!
  notification(id: ID!): Notification
}

enum Channel { EMAIL SMS }

type Notification {
  id: ID!
  policyNumber: String!
  claimNumber: String
  channel: Channel!
  template: String!
  sentAt: String!
  delivered: Boolean!
}
"""

for path, body in F.items():
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
print(f"b_core2: wrote {len(F)} files")
