# Media Asset Organization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Organize all current and future uploaded assets into owner-based media paths, preserve original upload names, and apply verified lossless optimization only when it reduces size.

**Architecture:** Keep Django filesystem storage and the existing model fields. Use model-aware `upload_to` callables for stable ownership paths, store original filenames and uploader identity as metadata, and centralize PNG-only lossless optimization in a storage helper. Move existing files with an explicit dry-run-first management command rather than a database migration.

**Tech Stack:** Django 6, SQLite, Django FileField/ImageField, Pillow, Django TestCase.

**Spec:** `docs/superpowers/specs/2026-10-19-media-asset-organization-design.md`

## Global Constraints

- Store files under `users/<user_id>/`, `startups/<startup_id>/`, or `templates/<template_id>/` ownership paths.
- Use generated UUID filenames and retain original filenames as metadata.
- Apply optimization only when it is lossless and produces a smaller file; never use lossy or format-changing conversion.
- If optimization is unsupported, fails, or does not reduce size, store original bytes unchanged.
- Existing-file organization defaults to dry-run and requires explicit `--apply`.
- Unreferenced media files are reported, never moved or deleted.
- Keep existing preview/download and authorization behavior unchanged.

---

### Task 1: Model Metadata And Upload Paths

**Files:**
- Modify: `incubator/models.py`
- Create: `incubator/storage.py`
- Create: next Django migration for filename/uploader fields
- Test: `incubator/tests.py`

**Interfaces:**
- `profile_picture_upload_to(instance, filename)` returns `users/<user_id>/profile/<uuid><ext>`.
- `startup_logo_upload_to(instance, filename)` returns `startups/<startup_id>/logo/<uuid><ext>`.
- `deliverable_file_upload_to(instance, filename)` returns `startups/<startup_id>/milestones/<milestone_id>/deliverables/<deliverable_id>/users/<uploader_id-or-role>/<uuid><ext>`.
- `deliverable_template_upload_to(instance, filename)` returns `templates/milestones/<milestone_template_id>/deliverables/<template_id>/<uuid><ext>`.
- `template_resource_upload_to(instance, filename)` returns the same template-owned directory with a unique filename.
- Add nullable original-name metadata to every file-bearing field and a nullable `uploaded_by` foreign key to `DeliverableFile`; do not make legacy rows invalid.

- [ ] **Step 1: Add failing path and metadata tests.** Test the five upload path callables for owner IDs, retained extensions, and distinct generated names. Test that file metadata and nullable legacy uploader fields exist and that existing model creation remains valid.
- [ ] **Step 2: Run the tests and confirm failure.** Run `python manage.py test incubator.tests.AssetStoragePathTest`; expect missing callables/fields.
- [ ] **Step 3: Implement upload path callables and fields.** Use `uuid.uuid4().hex`; sanitize the supplied extension to an alphanumeric extension; derive ownership only from related model IDs and never from the supplied filename.
- [ ] **Step 4: Generate and verify the schema migration.** Run `python manage.py makemigrations incubator`, inspect that it only adds nullable metadata/uploader columns and alters upload paths, then run `python manage.py makemigrations --check --dry-run`.
- [ ] **Step 5: Run the focused path/model tests.** Run `python manage.py test incubator.tests.AssetStoragePathTest` and require all assertions to pass.

### Task 2: Lossless Upload Optimizer

**Files:**
- Create: `incubator/asset_processing.py`
- Modify: `requirements.txt` only if an already-required Pillow capability proves insufficient
- Test: `incubator/tests.py`

**Interfaces:**
- `optimize_losslessly(upload)` returns `(stored_file, original_filename)`.
- PNG is the only format optimized in this implementation; all other formats return original bytes.
- PNG optimization returns original bytes unless the optimized output is smaller, has equal dimensions/mode/pixel values, and preserves supported ICC/EXIF/DPI metadata.

- [ ] **Step 1: Add failing tests for optimizer behavior.** Use in-memory PNG fixtures to assert smaller optimized PNG output is pixel-identical; use a JPEG fixture to assert bytes remain identical; use a PNG fixture that does not shrink to assert input bytes remain identical; pass a malformed PNG and assert it falls back unchanged.
- [ ] **Step 2: Run `python manage.py test incubator.tests.AssetProcessingTest` and confirm the optimizer is missing.**
- [ ] **Step 3: Implement `optimize_losslessly(upload)`.** Read and rewind the uploaded stream; accept only single-frame PNG; retain ICC profile, EXIF, DPI, and transparency metadata where present; compare decoded pixels; choose optimized bytes only when the output is strictly smaller and all checks pass; otherwise return the original stream.
- [ ] **Step 4: Run the focused optimizer tests.** Require the lossless, fallback, and malformed-input cases to pass.

### Task 3: Route New Uploads Through Ownership And Optimization

**Files:**
- Modify: `incubator/views.py`
- Modify: `incubator/models.py` if model save hooks are needed for metadata synchronization
- Modify: `templates/settings/index.html` only where upload result labels depend on original names
- Test: `incubator/tests.py`

**Interfaces:**
- All upload paths call `optimize_losslessly` before storage and set the corresponding original-name metadata.
- `DeliverableFile.uploaded_by` is set to `request.user` for incubatee/admin uploads and revision attachments.
- Startup logo creation saves the startup row first, then saves its logo once a startup ID exists.

- [ ] **Step 1: Add failing tests for each upload owner path.** Cover profile image, startup logo, incubatee file, admin reference file, revision file, deliverable-template file, and template resource file. Assert owner path, generated basename, original filename metadata, and uploader attribution where applicable.
- [ ] **Step 2: Run the upload tests and confirm current handlers use shared folders or omit metadata.**
- [ ] **Step 3: Update each upload handler/form path.** For startup creation retain the uploaded logo in a local variable, save `Startup` without the logo to obtain its primary key, then call `startup.logo.save(upload.name, processed_file, save=False)`, set original-name metadata, and save the fields. For deliverable and template uploads, assign `uploaded_by`/metadata before `save()`.
- [ ] **Step 4: Run upload tests and existing startup/member/deliverable tests.** Run `python manage.py test incubator.tests.AssetUploadTest incubator.tests.StartupCRUDTest incubator.tests.MemberTest incubator.tests.DeliverableTest`.

### Task 4: Display Original Filenames

**Files:**
- Modify: `templates/startups/edit_deliverable.html`
- Modify: `templates/startups/view_milestone.html`
- Modify: `templates/settings/index.html`
- Test: `incubator/tests.py`

- [ ] **Step 1: Add failing rendering assertions.** Create records with a generated stored basename and original-name metadata; assert rendered deliverable files and template resources show the original name and retain valid download URLs.
- [ ] **Step 2: Render-test before editing.** Run the focused test and confirm it currently displays the generated storage basename.
- [ ] **Step 3: Update filename presentation.** Prefer original-name metadata and fall back to `file.name|cut:'/'` behavior for old/null metadata. Keep URLs sourced from the existing FieldFile storage.
- [ ] **Step 4: Run the filename rendering tests.**

### Task 5: Dry-Run Existing Media Organizer

**Files:**
- Create: `incubator/management/commands/organize_media_assets.py`
- Test: `incubator/tests.py`

**Interfaces:**
- `python manage.py organize_media_assets` is a no-write dry run.
- `python manage.py organize_media_assets --apply` performs organization.
- Per-file operations copy to a temporary/new target and verify it; update the model path/metadata in a database transaction; after that transaction commits, remove the prior file. If database update fails, keep the old file/reference and remove the new copy. If old-file cleanup fails after commit, keep the valid new reference and report the old file as an orphan for later cleanup.
- The command reports unreferenced media and leaves it untouched.

- [ ] **Step 1: Add failing command tests.** Test default dry-run leaves both DB and files unchanged; `--apply` moves one tracked record and preserves its original-name metadata; rerunning `--apply` is idempotent; missing source or failed verification preserves the old database reference and old file; an unreferenced file is reported and untouched.
- [ ] **Step 2: Run `python manage.py test incubator.tests.OrganizeMediaAssetsCommandTest` and confirm the command is missing.**
- [ ] **Step 3: Implement explicit model querysets.** Enumerate each file-bearing field, calculate target names from foreign keys, copy to a unique target, run the same lossless optimizer, verify output, update one record in `transaction.atomic()`, and delete the old object only after commit. If the database update fails, remove the new copy and keep the original reference. If old-file cleanup fails after commit, retain the new reference and report the old path as an orphan. Catch/report per-file errors and continue without deleting active source data.
- [ ] **Step 4: Run command tests with temporary media storage.** Require all dry-run, apply, idempotency, failure, and orphan-file cases to pass.

### Task 6: Rollout Documentation And Final Verification

**Files:**
- Modify: `DEPLOYMENT_GUIDE.md`
- Test: existing test suite

- [ ] **Step 1: Document backups and maintenance-window rollout.** Explain backing up SQLite and `MEDIA_ROOT`, reviewing dry-run output, stopping uploads, applying `organize_media_assets --apply`, checking file counts/downloads, and rerunning the command after any transition-period uploads.
- [ ] **Step 2: Run migration consistency checks.** Run `python manage.py makemigrations --check --dry-run` and `python manage.py check`.
- [ ] **Step 3: Run the complete app tests.** Run `python manage.py test incubator`.
- [ ] **Step 4: Inspect local preview/download flows.** Verify profile photo, startup logo, deliverable file, template file, and template resource URLs return successfully after the test migration command.
- [ ] **Step 5: Do not run the organizer against user media automatically.** Only execute `organize_media_assets --apply` after the operator has reviewed the dry run and confirmed backups.
