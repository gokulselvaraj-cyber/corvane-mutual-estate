package com.corvane.adjuster

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.*
import java.math.BigDecimal

data class ClaimSummary(val claimId: String, val claimNumber: String, val policyNumber: String,
                        val lineCode: String, val status: String, val reserveAmount: BigDecimal?,
                        val fraudScore: Double?, val claimantName: String?)

data class Payee(val name: String, val sortCode: String, val account: String)
data class ApprovalRequest(val approvedAmount: BigDecimal, val note: String?, val payee: Payee)
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
