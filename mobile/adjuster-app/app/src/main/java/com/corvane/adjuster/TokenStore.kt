package com.corvane.adjuster

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
