package com.corvane.adjuster

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
