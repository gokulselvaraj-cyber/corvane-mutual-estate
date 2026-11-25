package com.corvane.adjuster

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
