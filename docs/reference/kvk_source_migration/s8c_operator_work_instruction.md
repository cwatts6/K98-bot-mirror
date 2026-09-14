# Work instruction: check the S8C local intake

> Retained S8B/S8C reference, 2026-09-14: S9A repository delivery is now complete.
> See [S9A closeout / S9B scope and pending documentation delivery](s9a_closeout_and_s9b_handoff.md).
> Historical execution/operator evidence and limits below remain intact; this update does not
> request a rerun or claim live Discord acceptance, bot-machine deployment or activation.


**Completed and accepted on 2026-09-14: Chris reported PASS on all seven checks.**
No repeat is required. This instruction is retained for reference; see the
[operator acceptance record](s8c_folder_intake_smoke_evidence.md#operator-walkthrough-accepted--2026-09-14).

**Who:** Chris, on the local development PC.

**Allow:** approximately 15–20 minutes.

**What you are checking:** you can submit the prepared test files, review their details, explicitly
confirm acceptance, inspect a saved pair and cancel a pending upload.

The automated SQL and intake tests have already been completed. You do not need to run those
tests, create a database, write SQL or prepare any spreadsheets. Use the existing synthetic season
**900002** and the files below. Nothing in this instruction connects to Discord or the bot machine.

This is a console walkthrough. Its prompts do not look like Discord. It uses the actual intake
services and the isolated test database. These files have already been accepted, so accepting them
again should return **duplicate**: that is the expected successful result, not an error.

**At the end, tell Codex which steps passed and which messages were confusing.** This does not ask
you to approve deployment or certify a live Discord test. The saved pair is inspected, not recreated;
you are not being asked to make a fresh counterpart attestation.

## Before starting

- Work on the development PC containing `C:\discord_file_downloader`.
- Leave the bot machine alone. No pull, restart or configuration change is needed.
- Use only the supplied synthetic files. Do not put real KVK files in this exercise.
- Do not run `setup.py` or the `journey-phase*.py` files in the evidence folder. Those are records
  of tests already performed, not instructions for you to repeat.
- If a step gives an unexpected error, stop and copy the error back to Codex. Keep all files.

## Step 1 — Open PowerShell in the right folder

Open **Windows Terminal** and select **PowerShell**, or open PowerShell from the Start menu.

Copy this line, paste it into PowerShell and press **Enter**:

```powershell
Set-Location C:\discord_file_downloader
```

**Expected:** the prompt now ends with `C:\discord_file_downloader>`.

## Step 2 — Check that the test files are available

In File Explorer, paste this into the address bar and press **Enter**:

```text
C:\K98-S8C-Smoke\20260913\inbox
```

Find these two files. You do not need to open or move them:

```text
900002-players-14.xlsx
900002-aggregate-14.xlsx
```

**Expected:** both files exist. If either is missing, stop and tell Codex its name.

## Step 3 — Start the local intake console

Return to PowerShell. Copy the whole line below, paste it and press **Enter**:

```powershell
.venv/Scripts/python.exe -m scripts.smoke_kvk_source_intake --approved-target '9SX2VF4\K98DEV|K98_S8C_Disposable_20260913_intake'
```

**Expected:** the first line starts with `SYNTHETIC LOCAL SMOKE ONLY`. It names
`K98_S8C_Disposable_20260913_intake`. You then see an `S8C>` prompt.

From now until Step 12, paste commands at **`S8C>`**, not at the ordinary PowerShell prompt.
The console prints a generic example containing season 900001. Ignore that example and use the
exact commands in this instruction, which use season **900002**.

The lines in braces below are simply the console's command format. You do not need to learn JSON.
Paste each block as a single line and press **Enter**. Do not paste the surrounding backticks.

## Step 4 — Submit both test files together

Paste this at `S8C>`:

```json
{"operation":"upload","arguments":{"season":900002,"files":["900002-players-14.xlsx","900002-aggregate-14.xlsx"]}}
```

**Expected:** two receipts are printed. This simulates submitting two attachments in one message.
It has not confirmed or paired either file merely because they arrived together.

The output contains a short summary followed by a longer technical block. In that block, find each
`OriginalFilename` and its `AttemptID`. An AttemptID is the receipt number; it looks like
`12345678-1234-1234-1234-123456789abc`.

Copy the two receipt numbers into Notepad:

| Write this label in Notepad | Copy the AttemptID belonging to |
|---|---|
| PLAYER_ID | `900002-players-14.xlsx` |
| AGGREGATE_ID | `900002-aggregate-14.xlsx` |

Both new receipts should show **version 1**. Keep these IDs until you finish.

**How to use the next commands:** first paste a command into Notepad, replace `PLAYER_ID` or
`AGGREGATE_ID` with the corresponding number you saved, keeping the quotation marks, then paste
the edited line into `S8C>`. Do not type the literal words `PLAYER_ID` or `AGGREGATE_ID` into the console.

## Step 5 — Review the player file's season and UTC capture time

Replace `PLAYER_ID`, then paste:

```json
{"operation":"metadata","arguments":{"receipt_id":"PLAYER_ID","version":1,"fields":{"kind":"players","period":"","scan_start":"2000-01-14T00:00:00Z","precision":"minute","kingdoms":"101,102"},"reason":"Synthetic operator walkthrough: review player scan 14"}}
```

**Expected:** the receipt now shows **version 2**, with these details:

| Detail | Expected value | Meaning |
|---|---|---|
| KVK | 900002 | The test season selected when submitting the files |
| Kind | players | Individual player snapshot |
| Scan start | 2000-01-14 at 00:00 UTC | When the synthetic source scan was captured |
| Kingdoms | 101 and 102 | The prepared test season's kingdom scope |
| Period | Empty | Accepting a player scan does not assign it to a fight |

The year 2000 is intentional synthetic data. **Do not replace it with today's date.** The `Z` means
UTC. In real use this field must contain the actual capture start, not the time the file was uploaded.

Read these details before continuing. This step prepares a review; it has not accepted the file yet.

## Step 6 — Explicitly accept the player file

Replace `PLAYER_ID`, then paste:

```json
{"operation":"confirm","arguments":{"kind":"receipt","identifier":"PLAYER_ID","version":2}}
```

The console will ask you to type a phrase beginning with `CONFIRM SYNTHETIC receipt`, followed by
your receipt number and `2`. Copy **the phrase it displays after “Type”**, excluding the final colon,
paste it at that prompt and press **Enter**. Typing only `yes` does not confirm anything.

**Expected:** the output contains:

```text
state: duplicate
scan_id: 14
```

These values appear inside the output's `outcome` block, with quotation marks and braces.
`duplicate` means the service recognised the already accepted scan and did not create another one.

Complete Steps 5 and 6 within five minutes. If you see **Confirmation expired**, repeat Step 5 using
the receipt's current version in place of `1`. The new review increments that version; use the new
displayed version in Step 6. Do not guess a version. If unsure, stop and send Codex the output.

## Step 7 — Review the aggregate file

Replace `AGGREGATE_ID`, then paste:

```json
{"operation":"metadata","arguments":{"receipt_id":"AGGREGATE_ID","version":1,"fields":{"kind":"aggregate","period":"fight:one","scan_start":"2000-01-14T00:00:00Z","precision":"minute","kingdoms":"101,102","coverage_start":"2000-01-10T00:00:00Z","coverage_end":"2000-01-14T00:00:00Z","as_of":"2000-01-14T00:00:00Z","state":"live"},"reason":"Synthetic operator walkthrough: review Fight One aggregate"}}
```

**Expected:** aggregate receipt **version 2**, with these details:

| Detail | Expected value |
|---|---|
| Season | 900002 |
| Kind | aggregate |
| Fight | `fight:one` |
| Coverage start | 2000-01-10 at 00:00 UTC |
| Coverage end | 2000-01-14 at 00:00 UTC |
| As-of time | 2000-01-14 at 00:00 UTC |
| Report state | live |

Coverage describes the interval covered by the supplied totals. As-of describes the report's
effective time. These are reviewed explicitly; the console does not infer them from arrival order.
The report state `live` describes this synthetic report, not a connection to the live bot.

## Step 8 — Explicitly accept the aggregate file

Replace `AGGREGATE_ID`, then paste:

```json
{"operation":"confirm","arguments":{"kind":"receipt","identifier":"AGGREGATE_ID","version":2}}
```

Type the exact confirmation phrase displayed, as in Step 6.

**Expected:** `state` is **duplicate** and `aggregate_revision_id` is populated. `scan_id` is
`null` for an aggregate; that is correct. The player file supplies the logical scan number.

As with the player file, confirm within five minutes of preparing the review.

## Step 9 — Inspect the existing confirmed pair

Both files have now been checked through intake. The automated test previously created the pair.
This step only reads that saved pairing review; **do not confirm it again**.

Paste this unchanged:

```json
{"operation":"review","arguments":{"review_id":"625fdbbe-ae77-45b7-8b6a-4b1253d5dbed"}}
```

**Expected:** the review is **completed**, identifies season **900002**, period **fight:one**,
player scans **10 to 14**, an aggregate revision and an explicit counterpart attestation.
That attestation belongs to the earlier labelled synthetic test; you are only inspecting it.

Now paste this unchanged:

```json
{"operation":"update_status","arguments":{"update_id":"1c450338-05c2-4248-9d25-5885cc3c008d"}}
```

**Expected:** KVK **900002**, **fight:one**, and **State: selected**.
This UpdateID is the durable identity of the complete matched result. You are not being asked to
calculate values manually or inspect SQL tables.

## Step 10 — Submit one file so you can practise cancellation

Paste this unchanged:

```json
{"operation":"upload","arguments":{"season":900002,"files":["900002-players-14.xlsx"]}}
```

**Expected:** a new receipt, **version 1**. Copy its AttemptID into Notepad under a new label:
**CANCEL_ID**. Use this new receipt, not the player receipt already accepted in Step 6.

Replace `CANCEL_ID` below, then paste:

```json
{"operation":"cancel_receipt","arguments":{"receipt_id":"CANCEL_ID","version":1}}
```

**Expected:** a message saying pending work was cancelled and accepted revisions/original files
remain retained. The payload contains `cancelled: true`. Cancellation does not delete scan 14,
the existing pair or the original workbook.

## Step 11 — Check the pair still exists after cancellation

Paste the same status command again:

```json
{"operation":"update_status","arguments":{"update_id":"1c450338-05c2-4248-9d25-5885cc3c008d"}}
```

**Expected:** it still shows **State: selected**.

## Step 12 — Exit and send your result

At `S8C>`, type this and press **Enter**:

```text
quit
```

**Expected:** you return to the normal PowerShell prompt. Leave the database, inbox and evidence
folder in place. No cleanup or production action is needed.

Copy the following checklist into your reply to Codex and fill in **Pass**, **Fail** or **Not run**:

```text
Console started:
Two test files submitted:
Player details reviewed and duplicate scan 14 confirmed:
Aggregate details reviewed and duplicate confirmed:
Existing 10–14 pair showed selected:
New pending upload cancelled:
Existing pair still selected after cancellation:

Steps/messages I found confusing:
Any error text:
```

The console automatically saves a transcript in `C:\K98-S8C-Smoke\20260913\evidence`.
Its exact filename is printed when you start. If something fails, include that filename if you can;
you do not need to read the technical evidence files yourself.

## What completing this instruction means

It records your hands-on check of the local review/accept/cancel controls and inspection of a saved
pair. It is not a fresh baseline test, a fresh pair-publication test, or live Discord UX acceptance.
The automated baseline/pairing/configuration results and remaining limits are recorded separately
in [the technical evidence](s8c_folder_intake_smoke_evidence.md).
