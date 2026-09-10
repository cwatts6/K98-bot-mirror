# Private Inventory Import and Support Sharing — Programme Pack

> Programme-level delivery plan for replacing the public-message inventory screenshot workflow
> with a private multi-file Discord modal, while retaining an explicit and auditable
> **Share with Support** path for authorised administrators.
>
> Prepared from the canonical K98 programme-pack template and the current repository implementation.
> This pack defines the approved product direction, target architecture, phased delivery model,
> privacy boundary, support-retention model, validation strategy, and final cutover contract.

## 1. Programme Header

- Programme name: `Private Inventory Import and Support Sharing`
- Date: `2026-07-15`
- Owner/context: KD98 inventory users and operators; initiated after users raised concern that Resources, Speedups, and Materials screenshots remain visible to other server members while the current `/inventory import` workflow is being processed
- Programme type: `Product UX | Discord interaction architecture | privacy and permissions | file handling | SQL/audit | operations`
- One-pass approved: `No — deliver as separately reviewed, PR-sized tasks with one atomic user-facing cutover`
- Product direction approved: `Yes`
- Runtime implementation status: `Not started`
- Headline: **Make every inventory import private from other users, while allowing the importing user to deliberately share a problem case with authorised support.**
- User-facing release model: `One visible workflow change after all hidden foundations, support controls, migration work, and regression gates are complete`
- Approved primary technology: `Pycord 2.8.0 DesignerModal + FileUpload`
- Current canonical command: `/inventory import`
- Related operator command: `/inventory audit`

## 2. Programme Vision

A player should be able to run `/inventory import`, choose the governor and inventory type, and
upload one or more screenshots in a private Discord modal. No ordinary channel message should ever
contain the screenshots, extracted values, correction controls, warnings, or error details. Other
server members should see nothing beyond the user's decision to invoke the slash command, subject to
normal Discord command visibility.

The full review journey remains private and author-gated. Resources and Speedups accept one
screenshot. Materials accepts one to four screenshots in the first modal and can offer a private
add-more action until the four-image limit is reached. The bot analyses the files, presents one
consolidated review, supports correction and approval, and releases the raw image bytes when the
session terminates.

Authorised support access is explicit rather than automatic. The bot does not post raw screenshots
to an administrator channel merely because confidence is low, a user cancels, or a correction is
made. Instead, the player chooses **Share with Support**, sees a clear consent notice, may add a note,
and then shares the relevant screenshots and import context into a restricted support channel.
Derived import values remain available to authorised administrators through existing SQL-backed
audit tooling, which is already an accepted access boundary.

The programme should set the standard for future sensitive Discord uploads: private interaction
transport, thin Discord callbacks, validated and bounded file handling, transient raw-data custody,
explicit escalation, durable metadata audit, fail-closed behaviour, and no hidden public fallback.

## 3. Why This Programme Exists

### 3.1 Current user problem

The current public/private inventory preference controls report delivery. It does not control how
inventory screenshots enter the system. `/inventory import` begins with an ephemeral response, but
then instructs the user to upload a normal message in the configured inventory channel. That
attachment is visible to everyone who can view the channel.

The current processing path also treats the uploaded message as the conversation anchor. When an
`original_message` exists, the review helper posts the extracted values and buttons back into the
same channel rather than using the private interaction response. The exposure is therefore wider
than the screenshot alone: detected Resources, Speedups, Materials, warnings, and review controls can
also be visible.

The original upload is deleted on some terminal paths, particularly successful approval and explicit
cancellation, but cleanup is not the privacy boundary and is not uniformly reached on every failure,
rejection, exception, or timeout path. Even a fast delete cannot prevent a member who is already
viewing the channel, a notification client, or a moderation/logging integration from seeing or
retaining the message first.

### 3.2 Current administrator exposure

The current `_post_admin_debug` path can automatically upload raw image bytes and structured JSON to
`INVENTORY_ADMIN_DEBUG_CHANNEL_ID` after selected failures, rejections, cancellations, or corrected
approvals. This was designed for operational diagnosis, but it does not require the importing user
to opt in.

The approved replacement is not "no administrator access." The accepted boundary is:

- other normal users cannot see screenshots or extracted values;
- authorised administrators can inspect derived database values through existing audit paths;
- authorised support staff receive raw screenshots only after explicit user consent;
- retained support screenshots are subject to a defined lifecycle rather than indefinite accidental
  retention.

### 3.3 Why a programme instead of one large patch

The change crosses several high-risk surfaces:

- a foundational Discord library upgrade;
- all existing legacy modals and views across multiple domains;
- new Components V2 modal APIs;
- user-controlled file uploads and image validation;
- transient in-memory storage and bounded resource use;
- multi-image Materials analysis and merge behaviour;
- interaction-token, timeout, concurrency, and restart behaviour;
- SQL-backed support consent and idempotency;
- restricted-channel delivery and attachment retention;
- existing import audit semantics;
- command registration and global `on_message` routing;
- removal of public fallbacks and retirement of the upload-first path.

The implementation should therefore be split into small internal tasks. The player should still
experience one release: the old public upload instructions disappear at the same time the private
modal becomes available.

### 3.4 Why now

Adoption is increasing and more users are questioning even brief public exposure. Leaving the
current flow unchanged increases the chance of:

- screenshots being copied before bot cleanup;
- inventory values being exposed through public review messages;
- a failed or timed-out upload remaining visible;
- raw images being retained automatically in an administrator debug channel;
- privacy expectations diverging from the report preference wording;
- growing distrust in the platform as inventory participation expands.

### 3.5 Current implementation evidence

The programme is grounded in the current repository behaviour rather than a theoretical Discord
flow.

| Current behaviour | Repository area | Programme consequence |
|---|---|---|
| `/inventory import` defers privately but creates a pending session and tells the player to upload in the channel | `commands/inventory_cmds.py`, `ui/views/inventory_views.py::start_import_command` | Replace the pending public-message handoff with a private setup view and modal. |
| The global message listener routes inventory attachments only from the configured upload channel | `DL_bot.py`, `upload_routes/inventory_route.py` | Retire the inventory `on_message` fast path at cutover. |
| The upload handler reads a normal message attachment and keeps its message/channel IDs and URL | `ui/views/inventory_views.py::handle_inventory_upload_message`, `InventoryImagePayload` | Modal imports must read immediately and persist no attachment URL. |
| Review delivery uses `original_message.channel.send(...)` when a message upload exists | `ui/views/inventory_views.py::_send_review_message` | New review delivery must have no public-message branch. |
| Approval and explicit cancellation delete the original message, but not every terminal path reaches the same cleanup | `InventoryConfirmationView`, analysis failure/rejection/timeout paths | Privacy cannot depend on cleanup after publication; terminal byte release must be central and idempotent. |
| Corrected/failing/rejected/cancelled cases can upload raw bytes to the configured administrator debug channel | `ui/views/inventory_views.py::_post_admin_debug` | Remove automatic raw-image escalation and replace it with explicit user consent. |
| Existing review views retain `InventoryImagePayload`, including raw bytes, for the review lifetime | `InventoryConfirmationView` | Move raw custody into a bounded store and keep view objects byte-free. |
| Report visibility is stored separately as `only_me` or `public` | inventory reporting preference service/DAL | Do not couple import privacy to report visibility. |
| Materials already supports up to four screenshots through repeated public uploads | active Materials batch and add-more flow | Preserve the four-image product limit, but collect initial/additional images through private modals. |
| Import audit already records hashes and structured phases | `services/inventory_import_audit_service.py` | Extend metadata to ordered multi-image hashes without retaining raw files. |

### 3.6 Solution options considered

| Option | Privacy from normal users | Multi-image UX | Operational complexity | Decision |
|---|---|---|---|---|
| Keep public message and delete immediately | Weak: exposure exists before deletion and may survive in clients/integrations | Existing behaviour | Low | Rejected as a final privacy solution; deletion remains defence in depth only. |
| Temporary private thread | Better, but members with thread-management permissions can see it; thread lifecycle and orphan cleanup are required | Good | Medium-high | Rejected. It keeps message routing/session-channel complexity and is unnecessary when modal upload exists. |
| Temporary permissioned text channel | Better for normal users, but administrators bypass overwrites; channel creation/deletion and permission failure create risk | Good | High | Rejected. More guild-resource and permission risk than the selected interaction-native design. |
| DM upload | Private from the guild | Good | Medium | Rejected as the primary journey because of DM restrictions, context switching, and separate session routing. |
| Slash-command attachment options | Strong: attachment arrives through the interaction | Acceptable but awkward for one-to-four Materials images and add-more | Low-medium | Rejected as an interim user journey. It would be replaced by the modal and create a second change for users. |
| Pycord DesignerModal + FileUpload | Strong: no ordinary guild message; interaction-native attachments | Best fit for one-to-four initial files and private add-more | Medium, with one shared dependency upgrade | **Selected.** It meets the privacy, usability, and one-release objectives. |

### 3.7 Decision rationale

The selected modal is not merely the most private option. It has the best total product and
engineering fit:

- it removes the public-message object rather than racing to delete it;
- it uses a Discord-native interaction surface rather than creating temporary guild resources;
- it supports a bounded multi-file Materials journey;
- it keeps governor/type setup and all results private;
- it allows the same button-to-modal pattern for additional Materials images;
- it avoids a DM context switch;
- it avoids adding an attachment-option journey that would soon be removed;
- it can fail closed without posting into a channel;
- it creates a reusable security pattern without forcing a generic framework in the first build.

The cost is a bot-wide Pycord upgrade. Isolating that dependency work as Phase 1 is therefore a
delivery-risk control, not an interim user workflow.

## 4. Product and Engineering Goal

The programme must answer these questions clearly for a player:

- Can anyone else in the server see the screenshots I upload?
- Can anyone else see the values the bot extracts?
- How many screenshots can I submit for each inventory type?
- What happens when the bot reads an image incorrectly?
- Can I correct the result without exposing it publicly?
- When and how can support see my screenshots?
- How long are raw screenshots retained?
- What happens if the bot restarts or the interaction expires?
- Will the bot ever fall back to posting my data in the channel?

For operators and developers, it must answer:

- Which component owns file validation, transient storage, analysis orchestration, support sharing,
  persistence, and Discord presentation?
- How is duplicate or concurrent support sharing prevented?
- How are raw bytes released on approval, cancellation, timeout, failure, restart, and support share?
- How are existing public upload paths retired without changing reporting preferences or approved
  inventory data?
- How is the Pycord upgrade proven safe across every existing modal/view surface?
- How is support-image retention enforced and audited?
- How can the final release be rolled back without silently re-exposing users?

## 5. Approved Decisions and Non-Negotiable Outcomes

### 5.1 Approved product decisions

1. Go directly to a Pycord version that supports `discord.ui.DesignerModal`,
   `discord.ui.Label`, and `discord.ui.FileUpload`.
2. Pin the stable `py-cord==2.8.0` release unless implementation-time evidence identifies a newer
   explicitly approved stable patch release.
3. Do not introduce temporary private threads, temporary channels, DM uploads, or slash-command
   attachment options as interim user journeys.
4. Keep `/inventory import` as the canonical entry point.
5. Use an ephemeral setup view followed by a fresh button interaction that opens the file-upload
   modal. Do not defer an interaction and then attempt to open a modal from the same response.
6. Ask the user to choose the inventory type before upload so the modal can enforce:
   - Resources: exactly one image;
   - Speedups: exactly one image;
   - Materials: one to four images.
7. Keep every setup, processing, review, correction, failure, support-consent, and completion response
   private/ephemeral.
8. Add **Share with Support** as an explicit user action.
9. Remove automatic raw-image posting from normal failure, rejection, cancellation, timeout,
   corrected approval, and other diagnostic paths.
10. Keep the existing public/private report preference independent from import privacy.
11. Retire the public upload-first route in the same user-facing release that enables the modal.
12. Fail closed. A private response failure must not cause screenshots or extracted values to be
    posted publicly.

### 5.2 Approved access boundary

| Actor | Normal import values | Raw screenshots |
|---|---|---|
| Importing player | Private interaction only | Private interaction/session only |
| Other normal server members | No access | No access |
| Bot process and configured vision processor | Required processing access | Required processing access |
| Authorised administrators/support | Existing SQL/audit access | Only after explicit Share with Support |
| Logs/telemetry | Sanitised metadata only | Never |

### 5.3 User-facing release constraint

Internal tasks may be merged and, where safe, deployed behind disabled flags. Users must not be
moved through several temporary upload journeys. Final cutover must atomically:

```text
enable private modal import
disable legacy public-message import
remove public response fallbacks
publish updated user guidance
```

## 6. Target Command, Workflow, and Data Model

### 6.1 Target command model

No new top-level command is required.

```text
/inventory import   -> private setup, upload, analysis, review, correction, approval, support share
/inventory audit    -> authorised metadata/value/support-reference audit
/myinventory        -> existing report journey, unchanged
/me inventory       -> existing report journey, unchanged
```

The programme changes neither top-level command count nor grouped subcommand count. The description
and version of `/inventory import` may be updated, but its canonical path remains stable.

### 6.2 Target player workflow

```text
Player runs /inventory import
-> bot defers privately
-> bot resolves registered governors
-> ephemeral setup view opens
-> player selects governor when required
-> player selects Resources, Speedups, or Materials
-> Upload Privately button becomes available
-> button interaction opens a DesignerModal with FileUpload
-> modal returns one validated file, or one-to-four validated Materials files
-> modal submission is deferred ephemerally
-> files are read immediately, validated, normalised, hashed, and held in a bounded transient store
-> import batch is created
-> vision analysis runs with an explicit type hint
-> Materials images are analysed and merged in deterministic submission order
-> one private review is shown
-> player approves, corrects, adds remaining Materials screenshots, shares with support, or cancels
-> terminal action releases transient image bytes
```

### 6.3 Target failure workflow

```text
validation failure
-> private explanation
-> no batch when validation failed before persistence
-> no public fallback
-> no raw support post

analysis failure after batch creation
-> batch marked failed or remains in a defined retryable state
-> private failure view
-> Try Again / Share with Support / Cancel as appropriate
-> transient files retained only for the bounded support/retry window
-> timeout releases bytes
```

### 6.4 Target support workflow

```text
Player selects Share with Support
-> author and live session are revalidated
-> consent modal explains restricted-admin access and retention
-> player may add an optional note
-> submission reserves one idempotent support-share record
-> bot posts sanitised screenshots and structured case context to restricted support channel
-> support record stores channel/message reference, hashes, actor, note, count, and retention deadline
-> player receives private confirmation
-> transient in-process bytes are released
-> support images are removed from the message on resolution or retention expiry
-> support metadata and derived database values remain auditable
```

### 6.5 Target data flow

```text
Discord FileUpload attachments
-> private upload validation/normalisation service
-> transient bounded image store
-> inventory analysis service
-> existing inventory normalisation and approval service
-> inventory DAL / SQL values

explicit support consent
-> support service
-> support DAL reservation/idempotency
-> restricted Discord support message
-> support DAL posted/retention state
```

### 6.6 Legacy paths to retire

```text
/inventory import -> "upload in this channel" pending session
normal inventory-channel attachment -> global on_message fast path
upload-first governor discovery
public channel review message
automatic raw-image admin debug post
public error/rejection fallback
message deletion as the primary privacy control
```

## 7. Navigation and Discord Interaction Model

### 7.1 Setup view

The first private screen should contain only the choices needed to open the correct modal:

- selected governor, or a governor selector when the player has several;
- inventory type selector;
- concise per-type screenshot guidance;
- `Upload Privately` primary button;
- `Cancel` secondary button.

The upload button remains disabled until all required choices are valid. Every callback must recheck
the invoking Discord user rather than trusting component state alone.

### 7.2 Why the modal opens from a button

`/inventory import` currently performs asynchronous account resolution and is safely deferred.
A modal must be the initial response to the interaction that opens it. The final model therefore uses
a fresh button interaction after setup. The button callback responds immediately with
`interaction.response.send_modal(...)`; the modal callback then defers ephemerally while analysis
runs.

### 7.3 File-upload modal

Recommended presentation:

```text
Title: Private Inventory Import

Resources / Speedups:
  Inventory screenshot
  Upload one full, uncropped screenshot.

Materials:
  Materials screenshots
  Upload one to four full, uncropped screenshots.
  You can add remaining screenshots from the review before approval.
```

The modal should use `DesignerModal`, `Label`, explanatory `TextDisplay` where helpful, and one
`FileUpload`. Do not mix unsupported legacy modal items directly into `DesignerModal`.

### 7.4 Review view

The review remains private and uses the current extracted-value and correction concepts. The target
action set is contextual:

```text
Approve Import
Correct Data
Add Materials Images   # Materials only, when fewer than four images exist
Share with Support
Cancel Import
```

For a failed or unreadable result:

```text
Try Again
Share with Support
Cancel
```

Button rows must stay within Discord component limits. Low-value explanatory controls must not crowd
the primary approve/correct actions.

### 7.5 Back and replacement behaviour

- Before modal submission, the player may change governor or type in the setup view.
- After a batch is created, changing governor is not allowed within that batch.
- `Try Again` creates or resets a private upload attempt according to the service contract; it does
  not ask for a public channel message.
- An additional Materials modal may append only the number of files still available under the
  four-image limit.
- The newest private review supersedes the previous review. Old controls are disabled.
- Forged, stale, duplicate, foreign-user, and concurrent interactions return private denials.

### 7.6 Timeout behaviour

- Setup timeout: disable controls; no SQL batch exists and no raw files are held.
- Upload modal timeout/close: no SQL batch exists and no raw files are held.
- Review timeout: cancel or expire the active batch according to the existing domain contract,
  disable controls, release transient images, and record cleanup.
- Support confirmation timeout: keep the original private review usable until its own timeout;
  do not share anything.
- An expired interaction webhook must never trigger a channel fallback.

### 7.7 Restart behaviour

The transient store is intentionally not durable. On bot restart:

- raw images disappear with process memory;
- an active private batch with no corresponding in-process image session cannot continue;
- the next command invocation or startup reconciliation cancels/marks the orphaned review state and
  tells the player to upload again;
- the player is not blocked until an arbitrary long expiry;
- support images already posted after explicit consent remain governed by the durable support record
  and retention process.

## 8. Target User Journeys

### Journey A — Single-image Resources or Speedups import

Should answer:

- How can the player submit a screenshot without exposing it?
- How quickly can the player reach a review?

Target behaviour:

- one-governor players see that governor preselected;
- the player selects Resources or Speedups;
- the modal requires exactly one image;
- server-side validation independently enforces one image;
- one private review is produced;
- approval writes the same normalised inventory values as today;
- terminal cleanup releases raw bytes.

Success means:

- no normal guild message contains the image or values;
- the existing approval and duplicate-import rules remain correct;
- reporting output remains unchanged.

### Journey B — Multi-image Materials import

Should answer:

- Can all relevant Materials screenshots be provided privately?
- Can the player add images later without posting in the channel?

Target behaviour:

- the initial modal accepts one to four files;
- each file is validated and assigned a deterministic source index;
- analysis uses the selected Materials hint;
- merged values preserve current duplicate/unreadable safeguards;
- one review shows the consolidated result and screenshot count;
- when fewer than four images were submitted, `Add Materials Images` opens another private modal
  with `max_values` equal to the remaining capacity;
- the newest review supersedes the old one.

Success means:

- one-to-four images work;
- the four-image limit cannot be bypassed through forged interactions or concurrent callbacks;
- source ordering and merge behaviour are deterministic and tested.

### Journey C — Correction and approval

Should answer:

- Can a user correct a bad value without sharing it?
- Does support sharing remain optional?

Target behaviour:

- existing Resources, Speedups, and Materials correction semantics remain private;
- significant-change confirmation remains in force;
- corrected values update the same private review;
- the player may approve without ever sharing raw files with an administrator;
- corrected approval no longer triggers an automatic raw-image debug post.

Success means:

- existing data safeguards remain;
- every correction and approval response is ephemeral;
- raw images are released after terminal approval.

### Journey D — Unreadable or failed analysis

Should answer:

- What can the player do when image recognition fails?
- Is the image sent to support automatically?

Target behaviour:

- failure is explained privately;
- no value is saved as approved;
- the image is not automatically posted to administrators;
- the player can try again, explicitly share with support, or cancel;
- the support/retry window is bounded by the session TTL.

Success means:

- a failure never becomes a public message;
- failure paths release images on cancellation or expiry;
- support receives files only after consent.

### Journey E — Share with Support

Should answer:

- Who will see the files?
- What exactly is shared?
- Can duplicate clicks create duplicate cases?

Target behaviour:

- a consent modal states that authorised support administrators will receive the screenshots,
  detected context, and optional note;
- the user submits explicit consent;
- one support case is reserved per batch;
- screenshots, batch ID, governor ID, selected/detected type, confidence, warnings, model/prompt,
  detected/corrected state summary, and note are posted to the restricted support channel;
- the importing user receives a private reference;
- duplicate and concurrent actions return the existing support reference;
- raw in-process bytes are released after a successful post.

Success means:

- the database proves who shared what metadata and when;
- ordinary users cannot access the support channel;
- a failed support post can be retried without duplicate successful messages.

### Journey F — Support resolution and retention

Should answer:

- Are shared screenshots retained forever?
- Can support preserve the case without retaining the files?

Target behaviour:

- support records receive a configurable retention deadline, default 30 days;
- an authorised support action can resolve early;
- expiry or resolution edits the bot-authored support message to remove attachments while retaining
  case metadata;
- SQL records `ImagesDeletedAtUtc`, resolution actor where applicable, and final state;
- cleanup retries safely after restart.

Success means:

- raw support images do not persist indefinitely by accident;
- support/audit metadata remains available after attachments are removed.

### Journey G — Accidental legacy channel upload after cutover

Should answer:

- Does the old route still process a public screenshot?
- What guidance does the user receive?

Target behaviour:

- the legacy `on_message` inventory route does not start an import;
- where bot permissions and product policy permit, an accidental attachment in the former upload
  channel is deleted promptly and the user receives generic private or minimally revealing guidance
  to use `/inventory import`;
- deletion is defence in depth, not the privacy guarantee;
- no extracted values are generated from the accidental public message.

Success means:

- the platform can truthfully state that supported inventory imports are private;
- no hidden upload-first path remains.

## 9. Visual and Output Direction

Target direction:

- private, calm, and explicit rather than technical;
- one obvious primary action per step;
- concise privacy wording at upload and support consent points;
- no raw JSON, internal model details, or administrator-channel references in normal player output;
- existing detected-value clarity and corrections retained;
- failure output gives a next action without exposing data.

Recommended output shape:

```text
Setup:
  ephemeral embed/content + compact selectors + Upload Privately

Upload:
  Discord DesignerModal + FileUpload

Processing:
  ephemeral deferred state, optionally "Processing N screenshot(s)..."

Review:
  ephemeral embed + contextual controls

Support consent:
  modal with clear restricted-access wording and optional note

Support confirmation:
  ephemeral case reference

Fallback:
  private text/embed only; never a guild-channel post
```

Suggested player wording:

> Your screenshots and detected values are private from other server members. They are processed by
> the bot's configured vision service. Authorised support receives screenshots only when you choose
> **Share with Support**.

Suggested support-consent wording:

> Share these screenshots with authorised support administrators? They will receive the screenshots,
> this import's analysis details, and your optional note. Other server members cannot see the support
> case. Shared screenshots are removed under the support retention policy.

## 10. Privacy, Security, and Retention Model

### 10.1 Data-classification matrix

| Data | Normal location | Retention | Publicly visible? |
|---|---|---|---|
| Slash command invocation | Discord interaction metadata | Discord platform policy | Command use may be observable under normal Discord behaviour |
| Governor/type selection | Ephemeral interaction | Interaction lifetime | No |
| Uploaded image transport | Ephemeral modal attachment | Read immediately | No ordinary guild message |
| Canonical validated image bytes | Bounded bot memory store | Until terminal action, successful support post, restart, or TTL | No |
| Attachment URL | Transport only | Never persisted or logged | No |
| Image hash/size/type/index | Audit metadata | Existing audit policy | Admin audit only |
| Detected/corrected/final values | Existing inventory SQL | Existing inventory policy | Subject to current report/audit permissions |
| Shared support image | Restricted support message | Default 30 days or early resolution | Restricted admins/support only |
| Support note and consent metadata | Support SQL table | Audit policy | Restricted admins/support only |
| Logs | IDs, counts, statuses, hashes where needed | Logging policy | Operator only; never raw bytes or URLs |

### 10.2 File validation and canonicalisation

The modal limits are a user-interface aid, not a security boundary. Server-side validation must:

1. Enforce the selected type's file count.
2. Enforce per-file and total-batch byte limits.
3. Accept only the approved image MIME/extension family.
4. Decode with Pillow and verify that the bytes represent a real image.
5. Enforce safe dimensions and total pixel count.
6. Reject animated or multi-frame images.
7. Apply orientation safely.
8. Re-encode to a canonical, metadata-free image representation where validation proves this
   preserves the visible screenshot and existing OCR behaviour.
9. Use sanitised generated filenames.
10. Hash the canonical processing bytes.
11. Never log attachment URLs, image bytes, base64, EXIF, or image content.

The exact byte and pixel limits must be central constants or validated configuration, with tests at
and around each boundary. They must account for Discord's current interaction attachment limit but
may be stricter to protect bot memory and the vision request.

### 10.3 Transient image store

Create a dedicated bounded store rather than retaining payload bytes inside long-lived Discord view
objects.

Target entry shape:

```text
batch_id
actor_discord_id
governor_id
selected_import_type
ordered images:
  source_index
  sanitised filename
  content_type
  size_bytes
  sha256
  canonical bytes (repr/log excluded)
created_at_utc
expires_at_utc
```

Required properties:

- asynchronous lock around mutation;
- per-user and global active-session limits;
- total-byte ceiling;
- TTL eviction;
- idempotent delete;
- no disk spill;
- no serialization;
- no raw bytes in object `repr`;
- no claim of cryptographic zeroisation: cleanup releases references and records the outcome;
- startup begins with an empty store and reconciles orphaned SQL state safely.

### 10.4 Interaction and permission security

Every component callback must validate:

- actor Discord ID;
- live batch ownership;
- governor access;
- batch status;
- timeout/expiry;
- selected import type;
- remaining Materials image capacity;
- action idempotency;
- support-channel configuration;
- support sharing state.

Do not rely solely on a custom ID, view instance, or hidden state supplied by the client.

### 10.5 Fail-closed rules

The following are forbidden:

- posting screenshots to the import channel when a modal fails;
- posting extracted values publicly when an ephemeral webhook expires;
- re-enabling upload-first processing automatically;
- using `INVENTORY_ADMIN_DEBUG_CHANNEL_ID` as an automatic raw-image fallback;
- logging attachment URLs or image content for diagnosis;
- keeping a batch active indefinitely because transient bytes were lost;
- accepting more than four Materials images through concurrent callbacks;
- treating a support-share attempt as successful before the restricted message exists.

### 10.6 Support retention

Default target:

```text
INVENTORY_SUPPORT_RETENTION_DAYS=30
```

Retention is configurable but must have a finite, documented production value. On expiry or early
resolution, the bot edits its support message to remove attachments while preserving the case
summary. The support record remains for audit.

A cleanup pass should run:

- on startup;
- periodically through an existing task-registration/lifecycle pattern;
- on explicit support resolution.

Cleanup must be retryable and idempotent.

## 11. Target Architecture

### 11.1 Layer ownership

| Concern | Target owner |
|---|---|
| Slash command entry/decorators | `commands/inventory_cmds.py` |
| Setup/upload/review/support Discord components | new or split modules under `ui/views/` |
| File validation/canonicalisation | inventory-domain upload service/helper |
| Transient image custody | dedicated inventory upload store |
| Import orchestration and multi-image merge | inventory-domain service |
| Existing value normalisation/approval | existing inventory services, refactored narrowly where needed |
| Support consent/posting/retention orchestration | inventory support service |
| Import persistence | existing inventory DAL |
| Support-share persistence | dedicated inventory support DAL |
| Audit phase mapping | `services/inventory_import_audit_service.py` |
| Legacy message-route retirement | `upload_routes/inventory_route.py`, `DL_bot.py` |
| Configuration | `bot_config.py`, environment reference |
| SQL schema | authoritative SQL repository |
| Tests | `tests/` |

### 11.2 Recommended module boundaries

Likely targets, subject to the architecture audit in each task:

```text
commands/inventory_cmds.py
ui/views/inventory_private_import_views.py
ui/views/inventory_review_views.py             # optional split, avoid forced broad rewrite
inventory/private_upload_models.py
inventory/private_upload_service.py
inventory/private_upload_store.py
inventory/support_service.py
inventory/inventory_service.py
inventory/dal/inventory_dal.py
inventory/dal/inventory_support_dal.py
services/inventory_import_audit_service.py
upload_routes/inventory_route.py
DL_bot.py
bot_config.py
```

Do not create all modules mechanically. The audit should choose the smallest boundaries that keep
commands/views thin and avoid making the existing large `inventory_views.py` even harder to own.

### 11.3 Typed contracts

Recommended contracts:

```text
InventoryUploadSelection
  actor_discord_id
  governor_id
  import_type

InventoryUploadedImage
  source_index
  filename
  content_type
  size_bytes
  sha256
  image_bytes (excluded from repr)

InventoryPrivateUploadSession
  import_batch_id
  selection
  images
  created_at_utc
  expires_at_utc

InventorySupportShareRequest
  import_batch_id
  actor_discord_id
  optional_note

InventorySupportShareResult
  support_share_id
  channel_id
  message_id
  image_count
  shared_at_utc
  retention_expires_at_utc
```

### 11.4 Batch lifecycle

The setup view does not create a SQL batch.

```text
setup only, no row
-> modal files validated
-> batch created using the existing active-import and ownership rules
-> analysis
-> analysed
-> awaiting_more_material (Materials only, explicit add-more action)
-> analysed after merge
-> approved | rejected | cancelled | failed
```

The implementation may use the existing transient `awaiting_upload` status during immediate handoff
rather than add a new status, provided the semantics and orphan cleanup remain correct. Do not add a
new status merely for naming cleanliness without SQL/index justification.

Support state is orthogonal to import status. Sharing does not approve, reject, or otherwise mutate
the player's inventory decision.

### 11.5 Multi-image Materials orchestration

- Process images in submission order with stable source indices.
- Reuse the existing per-image vision and Materials merge semantics.
- Do not run unbounded parallel model requests.
- Choose sequential or explicitly bounded concurrency after measuring service/rate-limit behaviour.
- Preserve current unreadable-item and duplicate-candidate safeguards.
- Record source image count and per-image hash metadata.
- If one image fails, do not silently discard it. Return a truthful consolidated warning/failure
  state and keep support sharing available.
- Adding more files reuses the same batch and audit record.
- Approval writes one final normalised Materials snapshot.

### 11.6 Interaction response ownership

- Slash command: defer ephemeral and render setup.
- Setup button: send modal as the immediate button response.
- Modal callback: defer ephemeral before file reads/analysis.
- Review actions: defer or respond ephemerally using the existing safe interaction pattern.
- No callback sends sensitive content through `channel.send`.
- If the interaction token is no longer valid, log a sanitised batch/action result and stop.

## 12. SQL and Audit Design

### 12.1 SQL source of truth

All schema, index, check-constraint, and DAL decisions must be validated against:

```text
C:\K98-bot-SQL-Server
```

Python-side schema scripts are review aids, not the authority.

### 12.2 Existing batch usage

Private modal imports can keep these existing source fields null:

```text
SourceMessageID = NULL
ImageAttachmentURL = NULL
SourceChannelID = command channel ID or NULL, based on approved audit semantics
FlowType = command
```

Do not persist ephemeral attachment URLs.

### 12.3 Dedicated support-share table

Do not overload `AdminDebugChannelID` and `AdminDebugMessageID` with new consent semantics. Preserve
them as legacy references for historical rows and add a dedicated support-share contract.

Recommended table concept:

```sql
dbo.InventoryImportSupportShare
(
    SupportShareID BIGINT IDENTITY PRIMARY KEY,
    ImportBatchID BIGINT NOT NULL,
    SharedByDiscordUserID BIGINT NOT NULL,
    SupportChannelID BIGINT NULL,
    SupportMessageID BIGINT NULL,
    Status NVARCHAR(32) NOT NULL,
    UserNote NVARCHAR(1000) NULL,
    ImageCount TINYINT NOT NULL,
    ImageHashJson NVARCHAR(MAX) NOT NULL,
    AttemptCount INT NOT NULL,
    LastErrorJson NVARCHAR(MAX) NULL,
    CreatedAtUtc DATETIME2(3) NOT NULL,
    PostedAtUtc DATETIME2(3) NULL,
    RetentionExpiresAtUtc DATETIME2(3) NULL,
    ResolvedAtUtc DATETIME2(3) NULL,
    ResolvedByDiscordUserID BIGINT NULL,
    ImagesDeletedAtUtc DATETIME2(3) NULL
)
```

Required constraints/index concepts:

- foreign key to `InventoryImportBatch`;
- one logical support share per import batch;
- image count between 1 and 4;
- non-negative attempt count;
- status check;
- index for active retention cleanup;
- index/reference lookup by import batch;
- no raw image/blob column;
- no attachment URL column.

Exact names and status values are subject to SQL-repository validation.

### 12.4 Support-share state and idempotency

Target logical states:

```text
requested
posting
posted
post_failed
resolved
images_removed
message_missing
```

The DAL should reserve or re-enter the single logical row before posting. Concurrent clicks must not
produce multiple successful support messages. A failed attempt may be retried through the same row.

### 12.5 Audit changes

The current import audit should evolve from a single public-message image assumption to a private
multi-image source.

Target source type:

```text
discord_modal_file_upload
```

Target details:

```text
image_count
ordered image hashes
sanitised filenames
content types
byte sizes
selected import type
support share status/reference
raw-image release reason
```

If the shared common import-audit table accepts one source hash, calculate a deterministic aggregate
hash from the ordered per-image hashes and store the ordered hashes in details.

Recommended audit phases:

```text
inventory_private_upload_received
inventory_private_upload_validated
inventory_batch_handoff
inventory_vision_analysis
inventory_material_merge
inventory_review_transition
inventory_support_share_requested
inventory_support_share_posted
inventory_support_share_failed
inventory_raw_images_released
inventory_approval_sql_ingest
inventory_terminal_outcome
```

Legacy phase names may remain readable for historical records. New code should use privacy-accurate
terminology rather than calling explicit support consent an "admin debug post."

## 13. Design Principles

1. **Private transport, not fast deletion** — screenshots must never need to exist as public messages.
2. **One user-facing cutover** — hidden foundations are acceptable; multiple temporary player
   workflows are not.
3. **Explicit support consent** — raw administrator access is a deliberate player action, not an
   automatic diagnostic side effect.
4. **Derived data and raw images are different classes** — existing authorised SQL access does not
   justify automatic raw-image retention.
5. **Fail closed** — interaction failures make the import unavailable; they never make it public.
6. **Commands and views stay thin** — validation, storage, analysis, support posting, and persistence
   belong in services and DALs.
7. **Bound every user-controlled resource** — file count, bytes, pixels, active sessions, processing
   concurrency, and retention all need limits.
8. **Authorise every action** — custom IDs and in-memory views are not permission checks.
9. **Do not persist transport URLs** — read ephemeral attachments immediately and retain only
   approved metadata.
10. **Support must remain operable** — explicit share includes enough context and a retention-safe
    case record to diagnose image/icon changes.
11. **Preserve inventory truth** — normalisation, correction, duplicate-import, approval, reporting,
    and Materials merge safeguards must not regress.
12. **Respect the SQL source of truth** — validate every schema and index change in the SQL repository.
13. **No broad library migration** — Pycord 2.8 enables the new modal; existing legacy modals stay on
    the compatible API unless an actual break requires a focused fix.
14. **Honest restart semantics** — transient images may be lost on restart; tell the user to re-upload
    and clear orphaned state safely.
15. **Observable without leaking** — logs and audit show IDs, counts, hashes, phases, and errors, never
    raw screenshots or attachment URLs.

## 14. Programme Phases and Task Map

The phases below are internal delivery slices. No player-facing modal launch occurs until the cutover
phase.

### Phase 1 — Pycord 2.8 Upgrade and UI Compatibility Foundation

Status: `prepared; companion task pack and chat starter included with this programme`.

Deliver:

- verify local, CI, and production Python meet Pycord 2.8's supported range;
- replace the current historical Git commit pin with stable `py-cord==2.8.0`;
- audit all existing modal/view/component usage for 2.7/2.8 behaviour changes;
- make only compatibility fixes required by the upgrade;
- add an explicit capability contract for `DesignerModal`, `Label`, and `FileUpload`;
- prove legacy `Modal`/`InputText` and representative existing views still work;
- run broad regression, command-registration, startup/import, and security gates;
- make no inventory workflow change.

User-visible effect: `None intended`.

### Phase 2 — Private Upload Domain Foundation

Status: `proposed`.

Deliver:

- typed private-upload contracts;
- file validation and canonicalisation service;
- bounded transient image store;
- private batch-creation service after modal validation;
- multi-image audit metadata and deterministic aggregate hashing;
- orphan/restart reconciliation;
- focused unit and concurrency tests;
- disabled feature flag with no user entry point.

User-visible effect: `None`.

### Phase 3 — Private Modal Import UX and Multi-Image Materials

Status: `proposed`.

Deliver:

- ephemeral governor/type setup view;
- `DesignerModal`/`FileUpload` upload flow;
- exactly one Resources/Speedups image;
- one-to-four Materials images;
- private add-more Materials modal with remaining-capacity enforcement;
- private processing, review, correction, approval, retry, cancellation, and timeout paths;
- removal of public fallbacks from the new path;
- existing data and report behaviour preserved;
- feature remains disabled for normal users until support and cutover are ready.

User-visible effect: `None for normal users; optional restricted operator smoke only`.

### Phase 4 — Explicit Share with Support, SQL Consent Audit, and Retention

Status: `proposed`.

Deliver:

- dedicated restricted support-channel configuration;
- support consent modal and optional note;
- SQL support-share table, constraints, DAL, and migrations;
- idempotent restricted-channel post;
- support reference in authorised audit output;
- no automatic raw-image debug post;
- transient-byte release after successful share;
- configurable retention deadline;
- startup/periodic retention cleanup;
- authorised early resolution and attachment removal;
- failure/retry/concurrency tests;
- SQL-repository validation and deployment sequencing.

User-visible effect: `Still hidden until cutover`.

### Phase 5 — Atomic Cutover and Legacy Public Route Retirement

Status: `proposed`.

Deliver:

- enable private modal workflow;
- disable/remove pending public-message upload instructions;
- disable/remove inventory upload-first handling in `on_message`;
- remove public review/error fallback paths;
- retire or repurpose former upload-channel guidance;
- update command text, canonical command reference, setup docs, privacy wording, and operator runbook;
- confirm no normal path stores attachment URLs or posts raw admin debug images;
- one end-to-end migration/reconciliation for active legacy sessions;
- production configuration for support channel and retention;
- operator smoke across Resources, Speedups, Materials, corrections, failures, support share, and
  accidental legacy uploads.

User-visible effect: `One release — inventory imports become private`.

### Phase 6 — Soak, Retention Verification, and Programme Close-Out

Status: `proposed`.

Deliver:

- observe error, timeout, memory, vision, support-share, and cleanup telemetry during soak;
- verify support attachments are removed at or before retention deadline;
- verify no legacy public imports are accepted;
- resolve post-launch defects without reopening the public path;
- archive completed task packs and starter files;
- update programme status and change log;
- capture genuinely out-of-scope findings as structured deferred optimisations.

User-visible effect: `Stability and trust, no new workflow`.

## 15. In Scope for the Programme

- Pycord 2.8 stable upgrade and compatibility validation.
- Private `/inventory import` setup and multi-file upload modal.
- Resources, Speedups, and Materials screenshots.
- One-to-four Materials screenshots and private add-more flow.
- Existing analysis, correction, significant-change, approval, duplicate-import, and reporting
  behaviour.
- Private errors, retries, cancellation, and timeout.
- Bounded transient raw-image custody.
- Explicit Share with Support.
- Restricted support channel.
- Dedicated support consent/audit persistence.
- Support attachment retention and early resolution.
- Import audit updates for private multi-image sources.
- Retirement of public upload-first routing.
- Removal of automatic raw-image debug posts.
- User/operator documentation and deployment guidance.
- Full architecture, command, SQL, permission, file-handling, restart, security, and regression
  validation.

## 16. Out of Scope for the First Build

- Changing inventory report visibility preferences or report rendering.
- Changing approved Resources, Speedups, or Materials calculations.
- Changing the OpenAI model selection or prompt except where an explicit selected-type hint is
  already supported and required.
- Adding Action Points or another inventory category.
- Temporary private threads, temporary channels, DMs, or slash-command attachment options.
- A generic file-upload framework for unrelated bot domains.
- Persistent raw-image storage in SQL, local disk, object storage, or another service.
- End-to-end encryption claims.
- Allowing administrators to access unshared transient images.
- Leadership editing or approving a player's inventory on their behalf.
- New top-level commands.
- Website or external support portal.
- Historical backfill of screenshots that were never retained.
- Rewriting every existing Pycord legacy modal to `DesignerModal`.

## 17. Likely Source Commands and Areas

### Commands to audit

```text
/inventory import
/inventory audit
/myinventory
/me inventory
```

### Runtime modules to audit

```text
commands/inventory_cmds.py
ui/views/inventory_views.py
ui/views/inventory_report_views.py
inventory/inventory_service.py
inventory/material_service.py
inventory/models.py
inventory/parsing.py
inventory/dal/inventory_dal.py
inventory/dal/inventory_material_dal.py
inventory/dal/inventory_audit_dal.py
services/inventory_import_audit_service.py
services/vision_client.py
upload_routes/inventory_route.py
DL_bot.py
bot_config.py
bot_instance.py
core/interaction_safety.py
account_picker.py
```

### Dependency and compatibility areas

```text
requirements.txt
requirements-freeze.txt
.github/workflows/
all discord.ui.Modal subclasses
all discord.ui.View subclasses
all modal/view tests
scripts/smoke_imports.py
scripts/validate_command_registration.py
```

### SQL repo areas to validate

```text
C:\K98-bot-SQL-Server
```

Likely SQL contracts:

- `dbo.InventoryImportBatch`;
- its status, active-session, user/status, and audit indexes;
- existing inventory audit integration;
- proposed `dbo.InventoryImportSupportShare`;
- support retention lookup/index;
- any SQL repo deployment/migration convention.

## 18. Cross-Programme Constraints

- The existing GovernorOS `/me` reporting experience must not regress.
- Existing `/myinventory` and inventory export data contracts remain unchanged.
- Command registration governance remains green.
- The canonical `/inventory import` path remains stable.
- `@versioned`, `@safe_command`, `@track_usage`, permission decorators, and channel policy must be
  preserved or deliberately updated.
- No direct SQL may be added to command or view modules.
- The SQL repository is authoritative.
- The bot remains Windows-first and production deploys only from the private production repository.
- Existing singleton/restart lifecycle patterns must be respected.
- Existing OpenAI vision processing remains the configured processor; privacy wording must not imply
  that only local bot code sees the bytes.
- New logs must avoid raw data.
- Existing administrator audit access to derived values remains accepted.
- Feature flags must not silently re-enable the public route.
- Any out-of-scope debt found during implementation must be captured through the deferred
  optimisation framework.

## 19. Programme-Level Validation Strategy

### 19.1 Automated gates for every implementation phase

At minimum consider:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe -m pre_commit run -a
```

Run focused tests selected for the phase and a full suite before PR handoff or document a justified
exception. Analyse pytest operational-log noise when required by current standards.

### 19.2 Dependency-upgrade validation

- clean-environment install;
- `pip check`;
- exact runtime Pycord version;
- supported Python version;
- all modal/view modules import;
- representative legacy modal callbacks;
- interaction defer/follow-up/edit behaviour;
- command registration inventory unchanged;
- startup smoke;
- no broad unrelated dependency changes.

### 19.3 Private upload validation

Cover:

- valid PNG/JPEG/WebP;
- extension/MIME mismatch;
- invalid image bytes;
- oversized file;
- oversized aggregate batch;
- excessive dimensions/pixels;
- animated/multi-frame file;
- zero, one, four, and five file attempts;
- Resources/Speedups multi-file forgery;
- sanitised filename and metadata behaviour;
- deterministic hashes and order;
- store capacity, TTL, deletion, and concurrency;
- process restart/orphan reconciliation.

### 19.4 Discord interaction validation

Cover:

- one and multiple governor states;
- every inventory type;
- modal open from button response;
- ephemeral response flags;
- author gating;
- forged custom IDs;
- stale controls;
- duplicate clicks;
- concurrent Add Materials Images;
- expired interaction token;
- response edit/send failures;
- timeout;
- private fallback only;
- no `channel.send` of values or files.

### 19.5 Inventory regression validation

Cover:

- Resources normalisation and correction;
- Speedups deterministic day handling and correction;
- Materials merge, duplicate candidates, unreadable items, and four-image limit;
- significant-change confirmation;
- same-day duplicate rules and admin override;
- approval transactions;
- report and export output unchanged;
- existing audit rows and legacy debug references remain readable.

### 19.6 Support validation

Cover:

- explicit consent required;
- optional note bounds and sanitisation;
- restricted channel missing/unavailable;
- successful post;
- failed post and retry;
- duplicate/concurrent share;
- one logical support case per batch;
- correct image count and hashes;
- no share after bytes have been released;
- support message attachment removal;
- retention cleanup on schedule and startup;
- early authorised resolution;
- missing/deleted message;
- audit output;
- no automatic support post.

### 19.7 SQL validation

- validate schema objects in the SQL repo;
- migration is additive and rollback-aware;
- check constraints match Python enums;
- unique/idempotency constraint;
- retention index;
- foreign key behaviour;
- no blob/raw-image storage;
- DAL contract tests;
- deployment sequence tested against a non-production database where available.

### 19.8 Manual Discord smoke

Before final cutover acceptance:

1. Run `/inventory import` as a normal user.
2. Confirm another normal account cannot see setup, files, values, or controls.
3. Import Resources and approve.
4. Import Speedups, correct, and approve.
5. Import one Materials image.
6. Import four Materials images.
7. Add remaining Materials images from review.
8. Exercise unreadable/low-confidence failure.
9. Share with Support and verify restricted access.
10. Retry/duplicate Share with Support.
11. Resolve/remove support attachments.
12. Exercise cancellation and timeout.
13. Restart during an active review and verify safe re-upload guidance.
14. Post an accidental legacy channel attachment and verify it is not imported.
15. Confirm `/myinventory`, `/me inventory`, exports, and `/inventory audit` remain correct.

### 19.9 AI-assisted review gates

Because the programme touches dependency supply chain, Discord permissions/interactions,
user-controlled files, SQL, retention, and restart-sensitive state:

- use `codex-security:security-diff-scan` after each implementation diff;
- use `k98-pr-review` before PR handoff;
- use `k98-promotion-check` before production promotion;
- use a deeper security scan if the diff or review identifies uncertainty in file handling,
  permissions, or persistence.

## 20. Release, Configuration, and Rollback Strategy

### 20.1 Feature flags and configuration

Recommended configuration:

```text
INVENTORY_PRIVATE_MODAL_ENABLED=false       # hidden until final cutover
INVENTORY_LEGACY_PUBLIC_UPLOAD_ENABLED=true # true only before final cutover
INVENTORY_SUPPORT_CHANNEL_ID=
INVENTORY_SUPPORT_RETENTION_DAYS=30
```

Exact flag names are subject to current environment-reference conventions.

Required invariant at public launch:

```text
INVENTORY_PRIVATE_MODAL_ENABLED=true
INVENTORY_LEGACY_PUBLIC_UPLOAD_ENABLED=false
```

An invalid combination must log clearly and fail safely. It must not leave both user paths active
without explicit operator intent.

### 20.2 Deployment sequence

1. Promote Pycord 2.8 compatibility foundation.
2. Promote hidden private-upload foundation with the modal flag off.
3. Promote hidden modal UX.
4. Deploy SQL support-share migration.
5. Configure and permission the support channel.
6. Promote support sharing and retention with normal-user entry still off.
7. Run restricted operator smoke.
8. Update former upload-channel permissions/guidance.
9. Atomically enable the modal and disable the public route.
10. Run final normal-user and second-account privacy smoke.
11. Begin soak monitoring.

### 20.3 Rollback

Before cutover:

- disable the private flag;
- retain the existing production user path;
- correct the hidden feature without user disruption.

After cutover:

- default emergency action is to disable `/inventory import` privately and show a service-unavailable
  message;
- do not automatically turn the public upload route back on;
- code rollback to the previous public workflow requires an explicit operator decision acknowledging
  the privacy regression;
- SQL migration should be additive so application rollback does not require destructive schema
  rollback;
- support retention cleanup must continue or have an operator runbook even if the modal is disabled.

## 21. Programme Acceptance Criteria

The programme is complete when:

- [ ] Stable Pycord with `DesignerModal` and `FileUpload` is deployed and existing bot interactions
      remain green.
- [ ] `/inventory import` never requires a normal channel attachment.
- [ ] Resources and Speedups accept exactly one private image.
- [ ] Materials accepts one to four private images and supports private add-more within the limit.
- [ ] No screenshot, detected value, warning, correction, or failure is posted to normal users.
- [ ] Every callback is author-gated and revalidates live batch/access state.
- [ ] Raw attachment URLs are not persisted or logged.
- [ ] Raw bytes are held only in a bounded transient store during the active private session.
- [ ] Approval, cancellation, rejection/failure finalisation, timeout, successful support share,
      and restart/orphan handling release transient images.
- [ ] Automatic raw-image administrator debug posts are removed.
- [ ] Share with Support requires explicit user consent.
- [ ] Support cases are idempotent, restricted, auditable, and retryable.
- [ ] Shared support attachments are removed on early resolution or finite retention expiry.
- [ ] Existing administrator access to derived SQL values remains available.
- [ ] The legacy upload-first route and public review/error fallbacks are retired.
- [ ] Report visibility preferences and report/export outputs remain unchanged.
- [ ] SQL changes are validated against the SQL repository and deployed in the correct order.
- [ ] Command registration validation remains green.
- [ ] No new direct SQL exists in command or view layers.
- [ ] Architecture, focused/full tests, manual Discord privacy smoke, K98 review, promotion, and
      security gates pass.
- [ ] Documentation and command references are updated.
- [ ] Deferred findings are captured structurally.
- [ ] Operator acceptance confirms the one-release player experience.

## 22. Programme Stop / Escalation Gates

Stop and request operator review if any of the following becomes true:

1. Production Python is below 3.10 or outside the chosen Pycord release's supported range.
2. Pycord 2.8 requires a broad rewrite of existing legacy modals rather than narrow compatibility
   fixes.
3. Discord's production File Upload component does not return the documented attachment contract.
4. The private modal cannot support the required one-to-four Materials files in the target guild or
   client experience.
5. Exact privacy requires a public fallback or ordinary message transport.
6. The existing vision/Materials merge service cannot process a deterministic ordered list without
   changing approved inventory values.
7. The SQL repository cannot support an idempotent support-share record without destructive change.
8. The support channel cannot be permissioned to the approved administrator/support boundary.
9. Retention cannot remove attachments while preserving case metadata and no equivalent safe
   lifecycle is available.
10. Final cutover would leave both public and private import paths active unintentionally.
11. A security review identifies a high-confidence unresolved file-handling, permission, retention,
    or data-exposure issue.

Do not silently weaken privacy, omit support consent, keep automatic raw debug posts, or widen the
programme into unrelated inventory/report work.

## 23. Deferred and Future Opportunities

Do not include these in early phases unless separately approved:

- a reusable private upload framework for other bot imports;
- support-case dashboards or ticket-system integration;
- user-visible support case history;
- object-storage support archives;
- client-side image guidance or automatic screenshot quality scoring before analysis;
- image diff tooling for game icon changes;
- support dataset export for model/prompt evaluation;
- additional inventory categories such as Action Points;
- website-based upload/review;
- encryption-at-rest for a future durable raw-image store;
- broader migration of legacy Pycord views to Components V2.

## 24. Suggested Next Action

```text
Use the companion chat starter to implement:
Private Inventory Import and Support Sharing Phase 1 —
Pycord 2.8 Upgrade and UI Compatibility Foundation.
```

The first task is intentionally user-invisible. It establishes the supported modal API and proves
that upgrading the shared Discord library does not destabilise existing commands, views, modals,
webhooks, or startup behaviour. Do not start inventory modal implementation inside Phase 1.

## 25. Programme Change Log

| Date | Change | Notes |
|---|---|---|
| 2026-07-15 | Programme created | Approved direct path to Pycord 2.8 multi-file private modal and explicit Share with Support |
