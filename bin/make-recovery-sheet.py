#!/usr/bin/env python3
"""Generate a non-secret recovery reference sheet; requires reportlab."""
import argparse, json, os, subprocess
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 cfg=json.loads(subprocess.check_output(['sudo','cat','/etc/productivity-recovery.json']))
 receipt=json.loads(subprocess.check_output(['sudo','cat','/var/lib/productivity-recovery/latest.json']))
 account=json.loads(subprocess.check_output(['op','account','list','--format','json']))[0]['account_uuid']
 link=f"https://start.1password.com/open/i?a={account}&v={cfg['vault_id']}&i={cfg['item_id']}"
 repo='https://github.com/superterran/bazzite/blob/main/docs/secure-desktop-recovery.md'
 a.output.parent.mkdir(parents=True,exist_ok=True);os.umask(0o077)
 c=canvas.Canvas(str(a.output),pagesize=letter);c.setTitle('Secure Desktop recovery reference')
 def line(y,text,size=11):
  c.setFont('Helvetica',size);c.drawString(42,y,text)
 def qr(url,x,y):
  q=QrCodeWidget(url);bounds=q.getBounds();d=Drawing(160,160,transform=[160/(bounds[2]-bounds[0]),0,0,160/(bounds[3]-bounds[1]),0,0]);d.add(q);renderPDF.draw(d,c,x,y);c.linkURL(url,(x,y,x+160,y+160),relative=0)
 line(744,'SECURE DESKTOP / RECOVERY',22)
 line(718,'Desktop + Closet | Prepared 1 November 2026',11)
 line(682,'1. Keep 1Password access and its Emergency Kit available separately.')
 line(660,'2. Use the Closet vault item: Desktop Secure Recovery.')
 line(638,'3. Follow the repository runbook before reinstalling or replacing data.')
 qr(link,42,442);qr(repo,330,442)
 line(424,'Private 1Password recovery record',12);c.drawString(330,424,'Full restoration runbook')
 line(395,'These QR codes contain links, not passwords. 1Password sign-in is required.')
 line(365,'The recovery record contains TWO secrets:')
 line(345,'- Backup decryption key (age): decrypts the Closet archive.')
 line(325,'- Encrypted home recovery password: unlocks the LUKS home.')
 line(290,'Backup location on Closet:')
 line(270,'/mnt/storage/backups/desktop-secure/',10)
 line(245,'Tested baseline: desktop-secure-20261101T175057Z.tar.zst.age',10)
 line(220,'Archive decryption, home unlock, filesystem and saved-file checks passed.')
 line(200,'Fresh-machine graphical rebuild has not yet been exercised.')
 line(170,'Restore to a separate staging location first. Never reinitialize the volume.')
 line(145,'Desktop + NAS loss still needs an off-site copy; none is configured yet.')
 line(105,'Nightly: 04:15 + up to 5 minutes, while desktop is awake. Monitor NAS space.')
 line(82,'No decryption key is stored on this sheet or with the NAS archive.')
 c.showPage()
 line(744,'TECHNICAL RESTORE REFERENCE',20)
 line(710,'Account: desktop-secure | UID 1002 | GID 1003')
 line(688,'LUKS UUID: '+cfg['uuid'],10)
 line(660,'Required: Linux, Python 3, age, zstd, GNU tar, cryptsetup; Podman for gateway.')
 line(630,'Use the runbook QR for complete commands and prerequisites.')
 for y,t in [(600,'sudo python3 bin/restore-secure-desktop.py'),(584,'  --archive /path/to/desktop-secure-TIMESTAMP.tar.zst.age'),(568,'  --destination /mnt/secure-recovery'),(530,'sudo python3 bin/install-restored-secure-desktop.py'),(514,'  --staging /mnt/secure-recovery --plan')]:line(y,t,10)
 line(480,'The first tool privately prompts for the age identity. Review the plan before --apply.')
 line(458,'An online copy may need journal replay on the COPY before read-only checks.')
 line(436,'Do not repair the live mapper or replace an existing encrypted home.')
 line(400,'Baseline encrypted archive SHA256:',11)
 digest='47c35103b3a3efaa4035b124971ced8bbfa83cb6bd97316e82e69267d7c2e59a'
 line(378,digest[:32],11);line(360,digest[32:],11)
 line(325,'Baseline size: 8,676,320,350 bytes. Compare the saved receipt before decryption.')
 line(295,'Repository carries scripts, units and artwork. Archive carries encrypted home,')
 line(275,'selected Steam/Sunshine/SSH/cooling config, Git bundle and gateway image.')
 line(245,'Recover Tailscale enrollment and notification credentials using the runbook.')
 line(225,'Do not run the old and restored machine with duplicate network identities.')
 line(190,'Ordinary access: Jump RDP port 3392; TV uses Secure Desktop in Steam.')
 line(170,'Disconnecting keeps apps open; Lock encrypted desktop ends and locks them.')
 line(125,'Passwords must never be pasted into URLs, command arguments or support logs.')
 c.save();os.chmod(a.output,0o600);print(a.output)
if __name__=='__main__':main()
