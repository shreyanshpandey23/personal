# CFO's note: Eventify

> **Most inputs are estimates, not quotes.** The founder gave the commission (10–20%) and the same-day fee (₹50–₹100). The worker day rate, costs, volume and ramp are the CFO's estimates; see `cfo-sources.md`. Replace them with real numbers before relying on this. Not financial, tax or legal advice: have an accountant check the structure, GST and payment handling before money moves.

**The margin.** Each shift booked earns Eventify **₹112.50**. That is a 15% commission on an estimated ₹600 day rate, plus a ₹75 same-day fee taken on 30% of shifts. After payment fees and a no-show reserve, each shift leaves **₹80.50** (72%). At 40 shifts a day, the profit margin is **49%**. Break-even is **13 shifts a day**, about 390 a month.

**The lines to watch.** These are the founder's pay and the volume, not the price.
- **Founder pay.** The base plan pays the founder nothing. Adding a ₹25,000 founder salary moves break-even to **23 shifts a day**, and year 1 profit falls from ₹3.07 lakh to **₹6,540**.
- **Volume.** At half the planned volume (20 a day), year 1 *loses* **₹26,730** and the startup money isn't earned back.
- **The plan itself.** 40 shifts a day is 1,200 worker-shifts a month, which is a lot for one city in year 1. Wedding and festival season will make some months much busier than others; the ramp below ignores that.

**Cash.** The manual pilot (WhatsApp plus a spreadsheet, no app) needs about **₹94,000** before it pays for itself, with payback in month 8. **Building a ₹3 lakh app up front** raises the cash needed to **₹4.3 lakh**, and the startup money is *not* earned back in year 1. Build the app only after the pilot proves organisers come back.

**Three ways to improve the margin (what-ifs run, not guessed).**
1. **Charge 20% instead of 15%** (revenue about ₹135 a shift). Break-even falls from 13 to **10 shifts a day**, year 1 profit rises from ₹3.07 lakh to **₹4.93 lakh**, and cash needed falls to ₹82,000. Charge it to the organiser and sell it as the no-show guarantee.
2. **Don't drop to 10%.** At about ₹90 a shift, break-even rises to **18 a day** and year 1 profit falls to ₹1.20 lakh. The commission is the business; don't start a price war on it.
3. **Cut the unit costs.** Unit costs 15% higher cost only about ₹40,000 of year 1 profit, so the fixed costs and volume matter far more. Every 1 shift a day above break-even adds about ₹2,400 a month.

**The board's money conditions.**
- [x] Who pays the 10–20%? Modelled as paid by the organiser on top of the worker's rate. **The founder still has to decide this.**
- [x] Does the commission cover costs? Yes. It leaves ₹80 a shift after payment and no-show costs, *at these estimates*.
- [x] Is the no-show guarantee affordable? A ₹10-a-shift reserve covers 5% no-shows at ₹200 extra each. **If no-shows exceed 5%, re-run.**
- [ ] Budget, team and tech plan. **Not given.** The founder's salary and the app decision change everything (see above).
- [ ] The worker subscription is not modelled, as the board asked. Add it only once there are more jobs than workers.

---

# Unit economics: Eventify (manual pilot stage, Lucknow)

Every number below comes from the input file. Nothing is looked up or guessed.

## One shift

| line | per shift |
| --- | ---: |
| Price | ₹112.50 |
| Payment gateway fee (~2% of ₹690 organiser payment) | -₹14.00 |
| Payout transfer to worker (bank/UPI payout fee) | -₹5.00 |
| No-show guarantee reserve (5% of shifts x ₹200 replacement premium) | -₹10.00 |
| Calls, SMS, WhatsApp per shift | -₹3.00 |
| **Contribution** (what each shift leaves to pay the fixed costs) | **₹80.50** (72%) |

## The margin that matters

Fixed costs: ₹30,000 a month (Ops coordinator (1 person, part/full time) ₹15,000, Marketing to organisers and workers ₹10,000, Phone, WhatsApp Business, tools ₹2,000, Travel and misc ₹3,000).

- **Break-even: 13 shifts a day.** Below that you lose money every month.
- **Profit margin at your plan** (40 a day): **49%** of every sale, after every cost.

## Year 1, month by month

| month | shifts a day | revenue | profit | cumulative (after ₹50,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | ₹10,125 | -₹22,755 | -₹72,755 |
| 2 | 6 | ₹20,250 | -₹15,510 | -₹88,265 |
| 3 | 10 | ₹33,750 | -₹5,850 | -₹94,115 |
| 4 | 14 | ₹47,250 | ₹3,810 | -₹90,305 |
| 5 | 18 | ₹60,750 | ₹13,470 | -₹76,835 |
| 6 | 22 | ₹74,250 | ₹23,130 | -₹53,705 |
| 7 | 26 | ₹87,750 | ₹32,790 | -₹20,915 |
| 8 | 30 | ₹101,250 | ₹42,450 | ₹21,535 |
| 9 | 33 | ₹111,375 | ₹49,695 | ₹71,230 |
| 10 | 36 | ₹121,500 | ₹56,940 | ₹128,170 |
| 11 | 38 | ₹128,250 | ₹61,770 | ₹189,940 |
| 12 | 40 | ₹135,000 | ₹66,600 | ₹256,540 |

- **Year 1 operating profit: ₹306,540** on ₹931,500 of revenue.
- After the ₹50,000 startup spend: ₹256,540.
- Startup money earned back: month 8.
- Cash you need before it pays for itself: **₹94,115**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 49% | 13 | ₹306,540 |
| Price -10% | 44% | 15 | ₹213,390 |
| Volume -20% | 44% | 13 | ₹173,232 |
| Unit costs +15% | 45% | 14 | ₹266,796 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.
