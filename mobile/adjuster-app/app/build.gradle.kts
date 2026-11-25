plugins {
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
        buildConfigField("String", "CLAIMS_API", "\"https://api.corvane.internal/claims/\"")
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
