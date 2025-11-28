"""
Migration script: rename upload folder paths from capitalized names to lowercase
- Supports --dry-run (report only) and --apply (perform moves and DB updates)
- Uses `MONGODB_URI` and `DB_NAME` from environment or imports `database` module
"""
import argparse
import os
import shutil
import json
import datetime
from pathlib import Path

try:
    # prefer centralized database if available
    from database import uploads as uploads_collection
    from database import client as mongo_client
    USE_DATABASE_MODULE = True
except Exception:
    USE_DATABASE_MODULE = False
    from pymongo import MongoClient


def find_matches(collection):
    """Find documents that reference capitalized upload folders."""
    # Patterns we look for in strings
    patterns = ["/uploads/answers/Descriptive/", "/uploads/answers/OMR/"]
    query = {
        "$or": [
            {"file_url": {"$regex": "/uploads/answers/(Descriptive|OMR)/"}},
            {"file_urls": {"$elemMatch": {"$regex": "/uploads/answers/(Descriptive|OMR)/"}}},
            {"files": {"$elemMatch": {"$regex": "(Descriptive|OMR)"}}},
            {"answer_sheet_type": {"$in": ["Descriptive", "descriptive", "OMR", "omr"]}}
        ]
    }
    docs = list(collection.find(query))
    return docs


def compute_new_path(s):
    return s.replace('/uploads/answers/Descriptive/', '/uploads/answers/descriptive/') \
            .replace('/uploads/answers/OMR/', '/uploads/answers/omr/')


def backup_documents(docs, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = out_dir / f'db_backup_{datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(docs, f, default=str, indent=2)
    return fname


def perform_filesystem_moves(uploads_root: Path, dry_run=True, force=False, backup_dir: Path=None):
    ops = []
    src_descriptive = uploads_root / 'answers' / 'Descriptive'
    src_omr = uploads_root / 'answers' / 'OMR'
    targets = [(src_descriptive, uploads_root / 'answers' / 'descriptive'),
               (src_omr, uploads_root / 'answers' / 'omr')]

    for src, dst in targets:
        if not src.exists():
            continue
        ops.append({'src': str(src), 'dst': str(dst), 'action': 'rename'})
        if not dry_run:
            # if destination exists, handle conflicts
            if dst.exists():
                if not force:
                    raise RuntimeError(f'Destination exists: {dst} (use --force to merge)')
                # merge: copy non-colliding files
                for root, _, files in os.walk(src):
                    rel = Path(root).relative_to(src)
                    target_dir = dst / rel
                    target_dir.mkdir(parents=True, exist_ok=True)
                    for f in files:
                        sfile = Path(root) / f
                        dfile = target_dir / f
                        if dfile.exists():
                            # rename colliding file
                            stamped = dfile.with_name(dfile.stem + '_' + datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S') + dfile.suffix)
                            shutil.copy2(sfile, stamped)
                            ops.append({'moved': str(sfile), 'to': str(stamped), 'note': 'conflict_renamed'})
                        else:
                            shutil.copy2(sfile, dfile)
                            ops.append({'moved': str(sfile), 'to': str(dfile)})
                # after copying, optionally remove source tree
                shutil.rmtree(src)
            else:
                # atomic move on same filesystem
                shutil.move(str(src), str(dst))
    return ops


def update_db_documents(collection, docs, dry_run=True):
    updated = []
    for doc in docs:
        doc_id = doc.get('_id')
        changes = {}
        # file_url single
        if 'file_url' in doc and isinstance(doc['file_url'], str) and ('/Descriptive/' in doc['file_url'] or '/OMR/' in doc['file_url']):
            new_val = compute_new_path(doc['file_url'])
            changes['file_url'] = new_val
        # file_urls array
        if 'file_urls' in doc and isinstance(doc['file_urls'], list):
            new_urls = [compute_new_path(s) if isinstance(s, str) else s for s in doc['file_urls']]
            if new_urls != doc['file_urls']:
                changes['file_urls'] = new_urls
        # files array: filenames only — usually no folder embedded; skip unless it contains folder
        if 'files' in doc and isinstance(doc['files'], list):
            new_files = []
            changed = False
            for f in doc['files']:
                if isinstance(f, str) and ('Descriptive' in f or 'OMR' in f):
                    nf = f.replace('Descriptive', 'descriptive').replace('OMR', 'omr')
                    new_files.append(nf)
                    changed = True
                else:
                    new_files.append(f)
            if changed:
                changes['files'] = new_files
        # answer_sheet_type normalization
        if 'answer_sheet_type' in doc and isinstance(doc['answer_sheet_type'], str):
            ast = doc['answer_sheet_type'].strip()
            if ast.lower() == 'descriptive' and ast != 'descriptive':
                changes['answer_sheet_type'] = 'descriptive'
            if ast.lower() == 'omr' and ast != 'omr':
                changes['answer_sheet_type'] = 'omr'

        if changes:
            if dry_run:
                updated.append({'_id': str(doc_id), 'changes': changes})
            else:
                res = collection.update_one({'_id': doc_id}, {'$set': changes})
                updated.append({'_id': str(doc_id), 'modified_count': res.modified_count, 'changes': changes})
    return updated


def main():
    parser = argparse.ArgumentParser(description='Rename upload paths from capitalized folders to lowercase')
    parser.add_argument('--apply', action='store_true', help='Perform the filesystem moves and DB updates')
    parser.add_argument('--force', action='store_true', help='Force-merge when destination exists')
    parser.add_argument('--uploads-root', default=None, help='Path to backend uploads folder (defaults to backend/uploads)')
    args = parser.parse_args()

    cwd = Path(__file__).resolve().parent.parent
    uploads_root = Path(args.uploads_root) if args.uploads_root else cwd / 'uploads'

    # Connect to DB
    if not USE_DATABASE_MODULE:
        mongo_uri = os.environ.get('MONGODB_URI') or os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/'
        db_name = os.environ.get('DB_NAME') or 'exam_system'
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db['uploads']
    else:
        collection = uploads_collection
        client = mongo_client

    print(f"Uploads root: {uploads_root}")
    print("Discovering affected documents...")
    docs = find_matches(collection)
    print(f"Found {len(docs)} documents that reference capitalized paths.")

    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    backups_dir = Path(__file__).resolve().parent / 'backups' / ts

    if not args.apply:
        # dry-run: show planned DB changes and file ops
        planned_fs = []
        for p in [uploads_root / 'answers' / 'Descriptive', uploads_root / 'answers' / 'OMR']:
            if p.exists():
                planned_fs.append({'src': str(p), 'dst': str(p.parent / p.name.lower())})
        print('Planned filesystem moves:')
        for op in planned_fs:
            print(op)
        print('\nPlanned DB changes (sample):')
        sample_updates = update_db_documents(collection, docs, dry_run=True)
        print(json.dumps(sample_updates, indent=2))
        print('\nDry-run complete. To apply changes, re-run with --apply after taking backups.')
        return

    # Apply mode
    print('Running apply: creating backups and performing moves/updates')
    backups_dir.mkdir(parents=True, exist_ok=True)
    db_backup = backup_documents(docs, backups_dir)
    print(f'DB backup written to: {db_backup}')

    # Copy files to backup location before moving
    file_backup_dir = backups_dir / 'files'
    file_backup_dir.mkdir(parents=True, exist_ok=True)
    # Copy entire answers directory if exists
    answers_src = uploads_root / 'answers'
    if answers_src.exists():
        shutil.copytree(answers_src, file_backup_dir / 'answers_backup', dirs_exist_ok=True)
        print(f'Copied answers folder to {file_backup_dir / "answers_backup"}')

    # Perform file moves
    try:
        fs_ops = perform_filesystem_moves(uploads_root, dry_run=False, force=args.force, backup_dir=file_backup_dir)
        print('Filesystem operations:')
        print(json.dumps(fs_ops, indent=2))
    except Exception as e:
        print(f'Filesystem operation failed: {e}')
        print('Aborting. Restore from backups manually if needed.')
        return

    # Update DB
    updates = update_db_documents(collection, docs, dry_run=False)
    ops_log = backups_dir / 'ops_log.json'
    with open(ops_log, 'w', encoding='utf-8') as f:
        json.dump({'db_updates': updates, 'fs_ops': fs_ops}, f, default=str, indent=2)
    print(f'Applied DB updates: {len(updates)} records modified. Ops log: {ops_log}')
    print('Migration complete.')


if __name__ == '__main__':
    main()
