// Runtime template appended to the existing protected Closet 1Password helper.
// __RECOVERY_MATERIAL__ is substituted only in anonymous SSH stdin, never files.
const material = __RECOVERY_MATERIAL__;
const recoveryTitle = 'Desktop Secure Recovery';
const matches = op(['item','list','--vault',vault,'--format','json']).filter(x => x.title === recoveryTitle);
if (matches.length > 1) throw Error('Ambiguous recovery items');
let recovery;
if (matches.length) recovery = op(['item','get',matches[0].id,'--vault',vault,'--format','json']);
else {
  if (!material.identity || !material.password || !material.uuid) throw Error('Recovery item missing; explicit initialization required');
  const template = {title:recoveryTitle, category:'SECURE_NOTE', fields:[
    {id:'notesPlain',type:'STRING',label:'notesPlain',value:'Desktop encrypted GNOME recovery. The age identity decrypts the independent Closet backup; the volume password opens its LUKS2 home. Repository github.com/superterran/bazzite, docs/secure-desktop-recovery.md. Keep access to this vault and your 1Password Emergency Kit. Printed QR links are references, not bearer decryption keys.'},
    {id:'ageIdentity',type:'CONCEALED',label:'Backup decryption key (age)',value:material.identity},
    {id:'volumePassword',type:'CONCEALED',label:'Encrypted home recovery password',value:material.password},
    {id:'volumeUUID',type:'STRING',label:'LUKS UUID',value:material.uuid}
  ]};
  recovery = op(['item','create','--vault',vault,'--format','json','-'],JSON.stringify(template));
}
function field(id) { const f=recovery.fields.find(x=>x.id===id); if(!f || !f.value)throw Error('Missing recovery field');return f.value; }
// Caller captures secrets privately and prints only public metadata.
process.stdout.write(JSON.stringify({item_id:recovery.id,vault_id:vault,title:recoveryTitle,
 identity:field('ageIdentity'),password:field('volumePassword'),uuid:field('volumeUUID')}));
