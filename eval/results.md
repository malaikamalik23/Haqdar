# Haqdar evaluation results

Abstention threshold: **0.25**  |  questions: 35

## Overall

| Metric | Result |
|---|---|
| Retrieval hit rate@4 | 100% (25/25) |
| Answer accuracy | 100% (25/25) |
| Citation accuracy (answered) | 100% (25/25) |
| Correct abstention (out of scope) | 90% (9/10) |
| False abstention (answerable refused) | 0% (0/25) |

## By language

| Language | Retrieval hit@4 | Answer accuracy | Correct abstention |
|---|---|---|---|
| Urdu | 100% (8/8) | 100% (8/8) | 100% (2/2) |
| Roman Urdu | 100% (10/10) | 100% (10/10) | 100% (5/5) |
| English | 100% (7/7) | 100% (7/7) | 67% (2/3) |

## Threshold sweep

| Threshold | Answer accuracy | Correct abstention | Balanced |
|---|---|---|---|
| 0.15 | 100% (25/25) | 60% (6/10) | 0.80 |
| 0.2 | 100% (25/25) | 80% (8/10) | 0.90 |
| 0.25 | 100% (25/25) | 90% (9/10) | 0.95 |
| 0.3 | 92% (23/25) | 90% (9/10) | 0.91 |
| 0.35 | 84% (21/25) | 100% (10/10) | 0.92 |

## Confidence calibration

- Mean confidence, correctly answered questions: 0.539
- Mean confidence, out-of-scope questions: 0.114

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
| answerable | roman | meter check karwane mein kitne din lagte hain | 0.305 | False | ✅ |
| answerable | roman | nepra mein bijli bill ki shikayat kaise karun | 0.315 | False | ✅ |
| answerable | roman | ziada bill aya hai complaint number kahan milega | 0.602 | False | ✅ |
| answerable | roman | bijli ka meter kharab lagta hai kahan shikayat karun | 0.277 | False | ✅ |
| answerable | roman | inspector meter kab tak check karega | 0.590 | False | ✅ |
| answerable | en | What is the due date for my electricity bill? | 0.760 | False | ✅ |
| answerable | en | My electricity meter is running fast, what should I do? | 0.585 | False | ✅ |
| answerable | en | Will I get credit if my meter was faster than allowed? | 0.531 | False | ✅ |
| answerable | en | Can the company remove my meter before the inspector checks it? | 0.685 | False | ✅ |
| answerable | en | Do I have to keep paying bills while my complaint is with NEPRA? | 0.810 | False | ✅ |
| answerable | en | How do I file my income tax return? | 0.607 | False | ✅ |
| answerable | en | I got a notice from FBR, how do I reply to it? | 0.617 | False | ✅ |
| answerable | roman | FBR ka notice aya hai jawab kaise dun | 0.387 | False | ✅ |
| answerable | roman | iris mein notice kahan dekhun | 0.492 | False | ✅ |
| answerable | ur | ایف بی آر کا نوٹس ملا ہے، کیا کروں؟ | 0.548 | False | ✅ |
| answerable | ur | ٹیکس ریٹرن کیسے جمع کرواؤں؟ | 0.444 | False | ✅ |
| answerable | roman | fbr helpline number kya hai | 0.616 | False | ✅ |
| out_of_scope | ur | پاسپورٹ کیسے بنواؤں؟ | 0.121 | True | ✅ |
| out_of_scope | ur | شناختی کارڈ کی تجدید کیسے کروں؟ | 0.214 | True | ✅ |
| out_of_scope | roman | passport kaise banwaun | 0.153 | True | ✅ |
| out_of_scope | roman | gas ka bill zyada aya hai _trap: Sui gas is not covered by the electricity pack_ | 0.000 | True | ✅ |
| out_of_scope | roman | rent agreement kaise banta hai | 0.154 | True | ✅ |
| out_of_scope | roman | sui gas ka meter tez chal raha hai _held out: gas trap_ | 0.000 | True | ✅ |
| out_of_scope | roman | pani ka bill ghalat aya hai _held out: water bill_ | 0.000 | True | ✅ |
| out_of_scope | en | What is the weather in Lahore? | 0.118 | True | ✅ |
| out_of_scope | en | Write me a poem about cricket | 0.075 | True | ✅ |
| out_of_scope | en | How much income tax do I have to pay on my salary? _near-scope trap: tax rates are not in the FBR pack_ | 0.302 | False | ❌ |

## Failure cases

- [en] How much income tax do I have to pay on my salary? (confidence 0.302, abstained=False)
