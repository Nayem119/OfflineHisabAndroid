# HISAB

### PolliLabs Offline Ledger · v1.1.0

বাংলা ও English-এ ব্যক্তিগত এবং ব্যবসায়িক হিসাব রাখার offline-first Android app।

| Android | ভাষা | হিসাবের মুদ্রা | নেটওয়ার্ক |
|---|---|---|---|
| 8.0+ · API 26+ | বাংলা · English | BDT · পূর্ণ টাকা | App ব্যবহারে প্রয়োজন নেই |

> [!IMPORTANT]
> HISAB কেবল প্রকৃত principal amount-এর হিসাব রাখে। Interest, profit rate, penalty বা fee-এর কোনো field বা calculation নেই।

## বিষয়সূচি

- [ফিচার](#ফিচার)
- [Build ও পরীক্ষা](#build-ও-পরীক্ষা)
- [হিসাবের নিয়ম](#হিসাবের-নিয়ম)
- [Backup ও নিরাপত্তা](#backup-ও-নিরাপত্তা)
- [সীমাবদ্ধতা](#সীমাবদ্ধতা)

## ফিচার

| বিভাগ | যা আছে |
|---|---|
| **নিরাপত্তা** | ৪–৮ অঙ্কের PIN; salted PBKDF2-HMAC-SHA256 hash; PIN যাচাই/পরিবর্তন; app থেকে বের হলে lock |
| **Navigation** | Home, Balance, Transactions, Reports, Settings; 600dp-এর নিচে bottom navigation, বড় screen-এ sidebar |
| **Dashboard** | Account balance, ধার দেওয়া/ফেরত, বর্তমান পাওনা/জমার summary; নতুন ধার, জমা ও repayment quick action; সাম্প্রতিক লেনদেন |
| **Ledger** | Personal/Business scope-এ ধার দেওয়া, ধার ফেরত, অন্যের জমা গ্রহণ ও জমা ফেরত/উত্তোলন |
| **Accounts** | একাধিক Cash/Bank account, opening balance এবং account-to-account transfer |
| **Transactions** | History search, edit এবং confirmation-সহ delete |
| **Reports** | ৭ দিন/এই মাস/সব সময় summary, সাম্প্রতিক ৭ দিনের activity chart, CSV ও PDF export |
| **Backup** | JSON export/restore, SHA-256 integrity check, strict validation ও 20 MiB size limit |

একই নাম Personal ও Business scope-এ থাকলে তাদের balance আলাদা হিসাব হয়। Account transfer ব্যক্তির পাওনা বা জমার balance পরিবর্তন করে না।

## Build ও পরীক্ষা

**প্রয়োজন:** JDK 17, Android SDK Platform 35। প্রথমবার Gradle ও Android Gradle Plugin download করতে internet লাগতে পারে; app ব্যবহারে লাগে না।

Project root থেকে PowerShell-এ চালান:

```powershell
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug
```

Debug APK তৈরি হবে এখানে:

```text
app/build/outputs/apk/debug/app-debug.apk
```

| যাচাই | অবস্থা |
|---|---|
| Unit tests | সফল |
| Debug APK build | সফল |
| Instrumentation test | চালানো হয়নি; device/emulator প্রয়োজন |
| Device install ও visual verification | চালানো হয়নি |

সংযুক্ত Android device বা emulator-এ instrumentation test চালাতে:

```powershell
.\gradlew.bat :app:connectedDebugAndroidTest
```

## হিসাবের নিয়ম

বর্তমান SQLite schema v2-তে `accounts`, `entries`, `transfers` table আছে। নতুন database-এ Cash account তৈরি হয়। v1 থেকে migration পুরোনো entry রেখে `account_id=1` এবং `scope=PERSONAL` বসায়। অর্থ পূর্ণ BDT হিসেবে SQLite `INTEGER`-এ রাখা হয়; poisha precision নেই।

```text
পাওনা       = GAVE - RECEIVED
আপনার কাছে জমা = DEPOSIT - WITHDRAW
Account balance = opening balance
				+ RECEIVED + DEPOSIT
				- GAVE - WITHDRAW
				+ transfer in - transfer out
```

`GAVE` = ধার দেওয়া · `RECEIVED` = ধার ফেরত পাওয়া · `DEPOSIT` = অন্যের জমা গ্রহণ · `WITHDRAW` = জমা ফেরত। Loan/deposit principal-কে আয় বা লাভ হিসেবে গণনা করা হয় না।

## Backup ও নিরাপত্তা

> [!CAUTION]
> Restore বর্তমান data সম্পূর্ণ replace করে; merge করে না। Restore-এর আগে আলাদা JSON backup export করুন।

- Backup-এ accounts, entries ও transfers থাকে। Restore-এর আগে data validate হয় এবং SQLite transaction-এর মধ্যে প্রতিস্থাপন হয়।
- PIN app lock; এটি database বা exported backup encrypt করে না।
- SHA-256 checksum data integrity যাচাইয়ে সাহায্য করে, কিন্তু encryption নয়। Backup file নিরাপদ স্থানে রাখুন।

## সীমাবদ্ধতা

| ক্ষেত্র | বর্তমান সীমা |
|---|---|
| **People** | Person আলাদা database record নয়; entry-তে নাম ও scope থাকে। Phone, address, archive ও person details নেই। |
| **Loan/Deposit** | Due date বা linked loan/deposit record নেই। Partial repayment/return আলাদা principal record-এর সঙ্গে linked নয়; overpayment আটকানো বা non-negative balance guarantee করা হয় না। |
| **Audit** | Void/reversal ও audit log নেই; delete confirmation-এর পর entry স্থায়ীভাবে মুছে যায়। |
| **Accounting** | Dedicated cashbook, account-wise filter ও mobile financial service account নেই। |
| **Reports** | CSV/PDF export সম্পূর্ণ ledger-এর; নির্বাচিত period filter export-এ প্রয়োগ হয় না। XLSX, receipt, statement ও print নেই। |
| **Security** | Biometric, dark mode ও encrypted backup নেই। |
| **Scale ও accessibility** | History pagination/lazy loading নেই। String-resource localization, screen-reader ও বড় screen/landscape layout device-এ যাচাই করা হয়নি। |
| **অন্যান্য** | Attachment ও notification নেই। |

> **সংস্করণের অবস্থান:** এটি principal-only personal ledger baseline। পূর্ণাঙ্গ loan servicing, cashbook, audit বা production release হিসেবে বিবেচনা করবেন না।
