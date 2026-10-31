// Run only inside Closet's codex-rc. Never log the returned credential.
'use strict';
const fs = require('fs'), path = require('path'), os = require('os');
const crypto = require('crypto'), cp = require('child_process');
process.umask(0o077);
function privateFile(name) {
  const p = path.join(os.homedir(), '.local/share/closet-secrets', name);
  const s = fs.lstatSync(p);
  if (!s.isFile() || s.uid !== process.getuid() || (s.mode & 0o077)) throw Error('Invalid secret permissions');
  return fs.readFileSync(p);
}
const record = JSON.parse(privateFile('token.json'));
const decipher = crypto.createDecipheriv('aes-256-gcm', privateFile('key'), Buffer.from(record.iv, 'base64'));
decipher.setAuthTag(Buffer.from(record.tag, 'base64'));
const token = Buffer.concat([decipher.update(Buffer.from(record.data, 'base64')), decipher.final()]).toString();
const env = {...process.env, OP_SERVICE_ACCOUNT_TOKEN:token, OP_BIOMETRIC_UNLOCK_ENABLED:'false', OP_CACHE:'false'};
delete env.OP_CONNECT_HOST; delete env.OP_CONNECT_TOKEN; delete env.OP_SESSION;
function op(args, input) {
  const executable = path.join(os.homedir(), '.local/bin/op');
  // Node supplies a socket for child stdin. op expects a real pipe when reading
  // JSON; cat converts it without writing any secret to disk or arguments.
  const command = input === undefined ? executable : '/bin/sh';
  const argv = input === undefined ? args : ['-c', 'cat | "$@"', 'op-stdin', executable, ...args];
  const r = cp.spawnSync(command, argv, {env, input, encoding:'utf8', timeout:45000, maxBuffer:2*1024*1024});
  if (r.status !== 0) throw Error('1Password operation failed: ' + r.stderr.replace(/[A-Za-z0-9_-]{24,}/g, '[redacted]').slice(0,700));
  return JSON.parse(r.stdout);
}
const vault = '2zx6acnxcyxxisbycygxflsb2i';
const title = 'Desktop Encrypted GNOME';
const existing = op(['item','list','--vault',vault,'--format','json']).filter(x => x.title === title);
if (existing.length > 1) throw Error('Ambiguous credential items');
let item;
if (existing.length) item = op(['item','get',existing[0].id,'--vault',vault,'--format','json']);
else {
  const password = crypto.randomBytes(32).toString('base64url');
  const template = {title, category:'LOGIN', fields:[
    {id:'username', type:'STRING', purpose:'USERNAME', label:'username', value:'desktop-secure'},
    {id:'password', type:'CONCEALED', purpose:'PASSWORD', label:'password', value:password},
    {id:'notesPlain', type:'STRING', label:'notesPlain', value:'Independent encrypted GNOME desktop. RDP over Tailscale: 100.119.114.55 port 3392. Full password unlocks the LUKS2 home and authorizes login. Disconnect keeps it unlocked; Lock encrypted desktop ends apps and locks it. Keep this password for volume recovery. Original unencrypted desktop remains at port3391 during migration.'}
  ], urls:[{href:'rdp://100.119.114.55:3392', primary:true}]};
  item = op(['item','create','--category','login','--title',title,'--vault',vault,'--format','json','-'], JSON.stringify(template));
}
let password = item.fields.find(f => f.purpose === 'PASSWORD').value;
if (!password) {
  item.fields.find(f => f.purpose === 'PASSWORD').value = crypto.randomBytes(32).toString('base64url');
  item.fields.find(f => f.purpose === 'USERNAME').value = 'desktop-secure';
  item.fields.find(f => f.id === 'notesPlain').value = 'Encrypted virtual GNOME. RDP host100.119.114.55 port3392. Full password unlocks LUKS2 home before starting GNOME. Disconnect retains apps/unlocked home; Lock encrypted desktop closes apps and locks it. Keep password for volume recovery. Original desktop remains on3391 during testing.';
  item.urls = [{href:'rdp://100.119.114.55:3392', primary:true}];
  item = op(['item','edit',item.id,'--vault',vault,'--format','json'], JSON.stringify(item));
  password = item.fields.find(f => f.purpose === 'PASSWORD').value;
}
if (!password || password.length < 32) throw Error('Stored password is not strong enough');
// The caller captures this privately in memory, never forwards raw stdout to chat.
process.stdout.write(JSON.stringify({item_id:item.id, vault_id:vault, title, password}));
