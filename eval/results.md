# Haqdar evaluation results

Abstention threshold: **0.25**  |  questions: 52

## Overall

| Metric | Result |
|---|---|
| Retrieval hit rate@4 | 98% (41/42) |
| Answer accuracy | 98% (41/42) |
| Citation accuracy (answered) | 100% (41/41) |
| Correct abstention (out of scope) | 90% (9/10) |
| False abstention (answerable refused) | 2% (1/42) |

## By language

| Language | Retrieval hit@4 | Answer accuracy | Correct abstention |
|---|---|---|---|
| Urdu | 100% (12/12) | 100% (12/12) | 100% (1/1) |
| Roman Urdu | 94% (17/18) | 94% (17/18) | 100% (5/5) |
| English | 100% (12/12) | 100% (12/12) | 75% (3/4) |

## Threshold sweep

| Threshold | Answer accuracy | Correct abstention | Balanced |
|---|---|---|---|
| 0.15 | 98% (41/42) | 80% (8/10) | 0.89 |
| 0.2 | 98% (41/42) | 80% (8/10) | 0.89 |
| 0.25 | 98% (41/42) | 90% (9/10) | 0.94 |
| 0.3 | 90% (38/42) | 90% (9/10) | 0.90 |
| 0.35 | 86% (36/42) | 100% (10/10) | 0.93 |

## Confidence calibration

- Mean confidence, correctly answered questions: 0.536
- Mean confidence, out-of-scope questions: 0.121

## Every question

| Kind | Lang | Question | Confidence | Abstained | Correct |
|---|---|---|---|---|---|
| answerable | ur | بل جمع کرانے کی آخری تاریخ کیا ہوتی ہے؟ | 0.600 | False | ✅ |
| answerable | ur | میرا میٹر تیز چل رہا ہے، کیا کروں؟ | 0.545 | False | ✅ |
| answerable | ur | میٹر چیک ہونے میں کتنے دن لگتے ہیں؟ | 0.579 | False | ✅ |
| answerable | ur | اگر میٹر تیز نکلا تو کیا اضافی یونٹس واپس ملیں گے؟ | 0.595 | False | ✅ |
| answerable | ur | بجلی کے بل کی شکایت کہاں کروں؟ | 0.681 | False | ✅ |
| answerable | ur | شکایت کے دوران کیا مجھے بل ادا کرنا ہوگا؟ | 0.538 | False | ✅ |
| answerable | roman | bill ki last date kya hoti hai | 0.492 | False | ✅ |
| answerable | roman | meter tez chal raha hai kya karun | 0.280 | False | ✅ |
| answerable | roman | meter check karwane mein kitne din lagte hain | 0.375 | False | ✅ |
| answerable | roman | nepra mein bijli bill ki shikayat kaise karun | 0.360 | False | ✅ |
| answerable | roman | ziada bill aya hai complaint number kahan milega | 0.602 | False | ✅ |
| answerable | roman | bijli ka meter kharab lagta hai kahan shikayat karun | 0.277 | False | ✅ |
| answerable | roman | inspector meter kab tak check karega | 0.590 | False | ✅ |
| answerable | en | What is the due date for my electricity bill? | 0.760 | False | ✅ |
| answerable | en | My electricity meter is running fast, what should I do? | 0.585 | False | ✅ |
| answerable | en | Will I get credit if my meter was faster than allowed? | 0.531 | False | ✅ |
| answerable | en | Can the company remove my meter before the inspector checks it? | 0.735 | False | ✅ |
| answerable | en | Do I have to keep paying bills while my complaint is with NEPRA? | 0.810 | False | ✅ |
| answerable | en | How do I file my income tax return? | 0.607 | False | ✅ |
| answerable | en | I got a notice from FBR, how do I reply to it? | 0.617 | False | ✅ |
| answerable | roman | FBR ka notice aya hai jawab kaise dun | 0.387 | False | ✅ |
| answerable | roman | iris mein notice kahan dekhun | 0.492 | False | ✅ |
| answerable | ur | ایف بی آر کا نوٹس ملا ہے، کیا کروں؟ | 0.548 | False | ✅ |
| answerable | ur | ٹیکس ریٹرن کیسے جمع کرواؤں؟ | 0.444 | False | ✅ |
| answerable | roman | fbr helpline number kya hai | 0.616 | False | ✅ |
| answerable | ur | شناختی کارڈ کی تجدید کیسے کروں؟ | 0.584 | False | ✅ |
| answerable | ur | امی کا شناختی کارڈ کیسے رینیو کروں؟ | 0.448 | False | ✅ |
| answerable | roman | cnic renew kaise karun | 0.565 | False | ✅ |
| answerable | roman | mera shanakhti card expire ho gaya hai kya karun | 0.422 | False | ✅ |
| answerable | roman | naya card nadra office se le sakti hun | 0.314 | False | ✅ |
| answerable | en | How do I renew my CNIC online? | 0.670 | False | ✅ |
| answerable | en | Do I need to give fingerprints to renew my ID card? | 0.651 | False | ✅ |
| answerable | en | When do I pay the fee for CNIC renewal? | 0.543 | False | ✅ |
| answerable | roman | rent agreement kaise banta hai | 0.628 | False | ✅ |
| answerable | roman | malik makan har saal kitna kiraya barha sakta hai | 0.338 | False | ✅ |
| answerable | roman | landlord zabardasti ghar khali karwa raha hai | 0.605 | False | ✅ |
| answerable | ur | مالک مکان کرایہ نہیں لے رہا، کیا کروں؟ | 0.602 | False | ✅ |
| answerable | ur | کیا مالک مکان پگڑی مانگ سکتا ہے؟ | 0.579 | False | ✅ |
| answerable | en | Does my rent agreement in Islamabad need to be in writing? | 0.611 | False | ✅ |
| answerable | en | My landlord won't fix the leaking roof. What can I do? | 0.505 | False | ✅ |
| answerable | roman | kirayedar ko kiraye ki raseed lena zaroori hai kya | 0.270 | False | ✅ |
| answerable | roman | kya malik makan bina wajah nikal sakta hai | 0.225 | True | ❌ |
| out_of_scope | ur | پاسپورٹ کیسے بنواؤں؟ | 0.137 | True | ✅ |
| out_of_scope | roman | passport kaise banwaun | 0.225 | True | ✅ |
| out_of_scope | en | How do I renew my passport on Pak-ID? _near-scope trap: same app, but passports are not in the CNIC pack_ | 0.144 | True | ✅ |
| out_of_scope | roman | gas ka bill zyada aya hai _trap: Sui gas is not covered by the electricity pack_ | 0.000 | True | ✅ |
| out_of_scope | roman | sui gas ka meter tez chal raha hai _held out: gas trap_ | 0.000 | True | ✅ |
| out_of_scope | roman | pani ka bill ghalat aya hai _held out: water bill_ | 0.100 | True | ✅ |
| out_of_scope | en | What is the weather in Lahore? | 0.118 | True | ✅ |
| out_of_scope | en | Write me a poem about cricket | 0.113 | True | ✅ |
| out_of_scope | roman | lahore mein kiraya kitna barh sakta hai _jurisdiction trap: Punjab has a different rent law_ | 0.075 | True | ✅ |
| out_of_scope | en | How much income tax do I have to pay on my salary? _near-scope trap: tax rates are not in the FBR pack_ | 0.302 | False | ❌ |

## Failure cases

- [roman] kya malik makan bina wajah nikal sakta hai (confidence 0.225, abstained=True)
- [en] How much income tax do I have to pay on my salary? (confidence 0.302, abstained=False)
