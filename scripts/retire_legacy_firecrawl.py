#!/usr/bin/env python3
"""Archive a known older Firecrawl slash command; never delete or overwrite modified user files."""
import argparse, datetime, hashlib, os, pathlib, sys
KNOWN_SHA256 = "f634ee45facfce3aac9d7bb7e0901e7539f63e641c519d50a86e74ee0279afdc"

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true',help='Archive the exact unchanged legacy command (default: dry-run)')
    parser.add_argument('--config-dir',type=pathlib.Path,default=pathlib.Path(os.environ.get('XDG_CONFIG_HOME',str(pathlib.Path.home()/'.config')))/'opencode')
    args=parser.parse_args(argv)
    target=args.config_dir/'commands/firecrawl-research.md'
    if target.is_symlink():
        print('REFUSED: legacy command path is a symlink',file=sys.stderr);return 2
    if not target.is_file():
        print('No legacy Firecrawl command found; nothing to retire.');return 0
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    if digest!=KNOWN_SHA256:
        print('REFUSED: legacy command is modified or unknown. Review and archive manually:',target,file=sys.stderr);return 3
    if not args.apply:
        print('DRY RUN: exact old command found; run with --apply to archive:',target);return 0
    archive=args.config_dir/'archive'/('firecrawl-replaced-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    archive.mkdir(mode=0o700,parents=True,exist_ok=False)
    final=archive/target.name
    target.rename(final)
    print('Archived old Firecrawl command at:',final)
    return 0
if __name__=='__main__':sys.exit(main())
