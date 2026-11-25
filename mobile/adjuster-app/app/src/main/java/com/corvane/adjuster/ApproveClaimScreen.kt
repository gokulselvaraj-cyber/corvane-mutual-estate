package com.corvane.adjuster

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
    var sortCode by remember { mutableStateOf("") }
    var account by remember { mutableStateOf("") }
    var slot by remember { mutableStateOf<ReserveSlot?>(null) }
    LaunchedEffect(claimId) { summary = api.summary(claimId) }
    Column {
        Text(summary?.claimNumber ?: "Loading")
        Text("Fraud score: ${summary?.fraudScore ?: "-"}")
        OutlinedTextField(value = amount, onValueChange = { amount = it }, label = { Text("Approved amount (GBP)") })
        OutlinedTextField(value = sortCode, onValueChange = { sortCode = it }, label = { Text("Payee sort code") })
        OutlinedTextField(value = account, onValueChange = { account = it }, label = { Text("Payee account") })
        Button(onClick = { slot = ReserveSlot.nextFree(claimId) }) { Text("Book inspection") }
        slot?.let { Text("Inspection ${it.label()}") }
        Button(onClick = {
            scope.launch {
                api.approve(claimId, ApprovalRequest(BigDecimal(amount), "approved in field",
                    Payee(summary?.claimantName ?: "", sortCode, account)))
                onDone()
            }
        }) { Text("Approve") }
    }
}
