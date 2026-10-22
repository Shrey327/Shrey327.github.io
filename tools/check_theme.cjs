// Exercise the theme preference without changing the user's system settings.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../assets/theme.js'), 'utf8');
function page({dark=false,saved=null,blocked=false}={}) {
  const root={dataset:{}};
  const events={};
  const button={hidden:true,attrs:{},setAttribute(k,v){this.attrs[k]=v;},addEventListener(k,v){events[k]=v;}};
  const system={matches:dark,addEventListener(_,fn){this.change=fn;}};
  const storage={value:saved,getItem(){if(blocked)throw Error('blocked');return this.value;},setItem(_,v){if(blocked)throw Error('blocked');this.value=v;}};
  let ready;
  vm.runInNewContext(source,{window:{matchMedia:()=>system},document:{documentElement:root,querySelector:()=>button,addEventListener(_,fn){ready=fn;}},localStorage:storage});
  // Preference must be applied before DOMContentLoaded and the stylesheet.
  assert.equal(root.dataset.theme,saved==='light'?'light':saved==='dark'?'dark':dark?'dark':'light');
  ready();
  assert.equal(button.hidden,false);
  return {root,button,system,storage,click:()=>events.click()};
}
for(const dark of [false,true]) {
  const p=page({dark});
  assert.equal(p.button.attrs['aria-pressed'],String(dark));
  p.system.matches=!dark;p.system.change();
  assert.equal(p.root.dataset.theme,!dark?'dark':'light');
  p.click();
  const chosen=p.root.dataset.theme;
  assert.equal(p.storage.value,chosen);
  p.system.matches=!p.system.matches;p.system.change();
  assert.equal(p.root.dataset.theme,chosen);
  assert.equal(page({dark:!dark,saved:chosen}).root.dataset.theme,chosen);
}
assert.equal(page({dark:true,saved:'invalid'}).root.dataset.theme,'dark');
const blocked=page({blocked:true});blocked.click();assert.equal(blocked.root.dataset.theme,'dark');
console.log('PASS: system default and changes, explicit override, persistence across page loads, invalid storage, blocked storage and early application.');
