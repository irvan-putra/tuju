plugins {
    id("com.android.application")
}

val appVersionName = "0.2.33"
val appVersionCode = 44

base {
    archivesName.set("tuju-v$appVersionName")
}

android {
    namespace = "com.vanipy.tuju"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.vanipy.tuju"
        minSdk = 26
        targetSdk = 34
        versionCode = appVersionCode
        versionName = appVersionName
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    signingConfigs {
        create("release") {
            val ks = System.getenv("TUJU_KEYSTORE_FILE")
            if (ks != null) {
                storeFile = file(ks)
                storePassword = System.getenv("TUJU_STORE_PASSWORD")
                keyAlias = System.getenv("TUJU_KEY_ALIAS")
                keyPassword = System.getenv("TUJU_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            if (System.getenv("TUJU_KEYSTORE_FILE") != null) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    testOptions {
        unitTests {
            isIncludeAndroidResources = true
            all { it.systemProperty("robolectric.graphicsMode", "NATIVE") }
        }
    }
}

dependencies {
    androidTestImplementation("androidx.test:runner:1.6.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.robolectric:robolectric:4.14.1") // test-only, not in the APK
}
