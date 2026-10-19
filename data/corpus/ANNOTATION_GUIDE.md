# Annotation guide — customer messages

File to fill in: `annotation_template.csv` (columns `id, message, window_start, window_end, band`).
The reviewed labels are saved as `reference.csv`. The review is done message by message, against
this guide only, without consulting the lexicon or the extractor; a disagreement with the label a
message was written under is resolved in favour of the reading of the text.

Judge **only from the text**. Do not infer anything that is not written. Deliveries take place
between 08:00 and 17:00.

## window_start / window_end

The earliest and the latest hour at which the customer accepts the delivery, as `HH:MM`.
Leave both empty when the message states no interval (also when it only says "any time").

| The message says | window_start | window_end |
|---|---|---|
| "between 10 and 12", "10-12", "from 10 to 12" | 10:00 | 12:00 |
| "after 3", "not before 3 pm", "from 15:00 onwards" | 15:00 | 17:00 |
| "before 11", "until 11", "by 11 at the latest" | 08:00 | 11:00 |
| "in the morning" | 08:00 | 12:00 |
| "around noon", "at lunchtime", "midday" | 11:00 | 14:00 |
| "in the afternoon", "after lunch" | 13:00 | 17:00 |
| "late afternoon", "towards the end of the day" | 15:00 | 17:00 |
| "around 2" | 13:00 | 15:00 |

A bare hour from 1 to 7 is an afternoon hour ("after 3" = 15:00). When two statements conflict,
take the one that reads as the customer's actual request.

## band

How strongly the customer constrains the delivery time:

| band | meaning | typical wording |
|---|---|---|
| `none` | no temporal information at all | access, parking, phone, product remarks |
| `flexible` | explicitly any time is fine | "any time", "whenever", "no rush", "home all day" |
| `mild` | a wish, politely hedged, with an explicit or implicit fallback | "if possible", "ideally", "would be nice", "not a must" |
| `strong` | a clear preference, with a reason, but not stated as non-negotiable | "I'd prefer", "I need", "I'm at work until", "suits me best" |
| `binding` | stated as non-negotiable: outside the interval the delivery cannot be received | "only", "must", "no other option", "otherwise nobody can receive it" |

`none` and `flexible` never have a window; `mild`, `strong` and `binding` should have one. If a
message has an urgency wording but no interval you can pin down, leave the window empty and
still give the band you read.

## Ten resolved examples

| message | window_start | window_end | band |
|---|---|---|---|
| I'm only home between 10 and 12, otherwise nobody can receive the order. | 10:00 | 12:00 | binding |
| Must be after 3 pm. Before that the house is empty, don't come earlier. | 15:00 | 17:00 | binding |
| I would prefer the afternoon, I'm at work in the morning. | 13:00 | 17:00 | strong |
| I need it before 11, the builders are waiting for the cement. | 08:00 | 11:00 | strong |
| If possible between 9 and 11, but it's not a big deal. | 09:00 | 11:00 | mild |
| Ideally the morning, if it works for you. | 08:00 | 12:00 | mild |
| Any time works, I'm home all day. | | | flexible |
| Whatever is easier for you, we're retired and always home. | | | flexible |
| Second floor, no elevator, thanks. | | | none |
| Please call before, the intercom is broken. | | | none |
