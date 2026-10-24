# Media Asset Organization Design

**Status:** Proposed
**Date:** 2026-10-19

## Goal

Organize every uploaded asset into a stable user, startup, or template folder; assign collision-resistant generated filenames while retaining the uploaded filename for display; and reduce file size only through verified lossless optimization.

## Current State

The project uses Django's default local filesystem storage with `MEDIA_ROOT = BASE_DIR / 'media'`. Upload fields are spread across `User.profile_picture`, `Startup.logo`, `DeliverableFile.file`, `DeliverableTemplate.admin_file`, and `DeliverableTemplateResource.file`. Their current paths are shared top-level folders such as `profile_pictures/`, `startup_logos/`, `deliverables/`, and `admin_templates/`.

Deliverable uploads record the uploader's role but not the uploader's user ID. FileField names are also used as display names in templates, so replacing stored names requires retaining the original upload name separately.

## Proposed Storage Layout

All stored filenames will be generated UUID names with a sanitized extension. Original filenames will be retained as metadata and shown in the UI where filenames are currently shown.

- Profile images: `users/<user_id>/profile/<uuid>.<ext>`
- Startup logos: `startups/<startup_id>/logo/<uuid>.<ext>`
- Deliverable files and revision attachments: `startups/<startup_id>/milestones/<milestone_id>/deliverables/<deliverable_id>/users/<uploader_id>/<uuid>.<ext>`
- Global deliverable template files/resources: `templates/milestones/<milestone_template_id>/deliverables/<deliverable_template_id>/<uuid>.<ext>`

Historical deliverable files do not identify an uploader, only `uploaded_by_role`; those files will be organized under the startup/milestone/deliverable path and grouped by role, with uploader metadata left null. Future uploads will record the uploader user ID.

Startup creation must persist the startup row before saving a logo into its ID-based folder. Editing existing startups can continue using their existing primary key.

## Naming and Metadata

Stored basenames will be generated UUIDs, not user-controlled path components. Add original-name metadata for every file-bearing field. Existing records will be backfilled from their current stored basenames before files are moved. User interfaces that currently show a stored basename will instead show original-name metadata, falling back to the basename for legacy/null values.

The model relationships remain authoritative for ownership and authorization. Folder paths are organizational, not an authorization mechanism. Existing upload/download permissions remain unchanged.

## Lossless Optimization

Optimization is best-effort and must never reduce image fidelity:

- Optimize PNG data with Pillow only when the result is smaller and decoded pixels are identical; preserve supported color profile and image metadata.
- Do not recompress JPEG, video, PDF, Office documents, archives, or other formats using lossy or format-changing conversions. Leave them byte-for-byte unchanged unless a format-specific lossless optimizer is later explicitly added and verified.
- If image decoding, optimization, metadata preservation, or verification fails, store the original uploaded bytes unchanged.
- Do not retain a second original copy after successful verified lossless optimization; the agreed behavior is to replace the upload completely. Retain the original filename metadata.

## Existing-File Migration

Implement an idempotent Django management command, `organize_media_assets`, that defaults to dry-run and requires an explicit `--apply` option to make changes.

For each database-referenced file, the command will determine the target path from its owning model, copy or losslessly optimize to a temporary/new target, verify the result, update the database field path and original-name metadata, then remove the old storage object only after the database update succeeds. Re-running it must skip already-organized files safely. If a step fails, leave the old file and database reference intact and report the error.

Files in `MEDIA_ROOT` that are not referenced by the database will be reported but not moved or deleted because their ownership cannot be inferred. The command will print a per-model summary and individual failures without printing file contents.

The command is separate from schema migrations: it performs potentially long-running filesystem work and must not run automatically during deployment.

## Schema and Code Changes

Expected implementation areas:

- `incubator/models.py`: upload path callables, original-name fields, and nullable uploader relationship for deliverable files.
- A Django schema migration: add metadata/uploader fields without rewriting historical rows.
- Upload views and startup creation: record uploader/original name, use the shared lossless optimizer, and save startup logos after assigning a primary key.
- Templates: display original filenames and preserve existing preview/download behavior.
- `incubator/management/commands/organize_media_assets.py`: dry-run/apply organization command.
- Tests: new-upload paths and metadata, lossless PNG optimization/non-smaller fallback, permissions/workflow preservation, migration dry-run/idempotency, and failure-safe file movement.
- Deployment documentation: back up the database and `MEDIA_ROOT`, inspect a dry run, then run `--apply` in a maintenance window; configure persistent media backup for the new directory tree.

## Acceptance Criteria

1. Each tracked upload is stored under the appropriate owner/startup/template path with a generated filename.
2. Original filenames remain available for UI display and database traceability.
3. Future deliverable uploads record the uploading user; legacy uploader remains null when unknowable.
4. PNG optimization is accepted only when smaller and pixel-identical; unsupported, failed, or non-beneficial optimization preserves the uploaded bytes.
5. Existing references remain usable after migration; failed moves do not remove old files or alter their database references.
6. A default dry run does not modify files or database rows; applying twice is safe.
7. Unreferenced media is reported and left untouched.
8. Existing access control and download/preview workflows remain unchanged.

## Risks and Rollout

Moving files changes persisted storage paths and must be coordinated with backups. Back up both SQLite and media files before applying the migration command. Deploy schema/code first, inspect the command's dry-run report, then run `organize_media_assets --apply`. Keep web workers stopped or in maintenance mode during the apply phase to avoid concurrent uploads being missed. The command should be rerun after deployment to capture files uploaded during the transition.

The local filesystem design preserves the current deployment model. If uploads later move to S3/object storage, retain the owner path and metadata contract while replacing the storage backend and migration transport.
