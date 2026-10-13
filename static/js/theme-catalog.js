/* Two accessible appearance foundations; Liquid Glass is a visual finish.
   Previously selected decorative skins are migrated on the next visit. */
(function(){'use strict';
const themes=[{"id":"sakura-journey","name":"Light","jp":"昼 · Light","description":"Warm ivory · clear reading","dark":false,"paper":"#F8F5EF","warm":"#EFE8DD","card":"#FFFDFA","ink":"#1B2C47","soft":"#536074","accent":"#304B70","deep":"#1B2C47","seal":"#9E4568","sealsoft":"#F4E2E8","gold":"#826223","fg":"#FFFFFF","jpfont":"mincho","bodyfont":"serif","motion":"rise","duration":180,"frame":"rounded","featured":true},{"id":"kyoto-night","name":"Dark","jp":"夜 · Dark","description":"Deep navy · gentle contrast","dark":true,"paper":"#111B2B","warm":"#1B283B","card":"#1D2B40","ink":"#F5EFE5","soft":"#C4CEDC","accent":"#E9C485","deep":"#F7DCAA","seal":"#F0ADB4","sealsoft":"#382E40","gold":"#E9C485","fg":"#172237","jpfont":"mincho","bodyfont":"serif","motion":"ink","duration":180,"frame":"rounded","featured":true}];
const darkLegacy=new Set(['neon-tokyo','matsuri-lantern','sumi','yozakura']);
const lightLegacy=new Set(['water-glass','anime-dawn','kyoto-paper','bamboo-zen','fuji-mist','washi','sakura','matcha']);
function migrate(id){
 if(id==='auto'||themes.some(t=>t.id===id))return id;
 if(darkLegacy.has(id))return 'kyoto-night';
 if(lightLegacy.has(id))return 'sakura-journey';
 return 'auto';
}
function resolve(id){id=migrate(id);return id==='auto'?(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'kyoto-night':'sakura-journey'):id;}
function read(){try{return migrate(localStorage.getItem('kotoba:theme'));}catch(_){return 'auto';}}
function early(){const choice=read(),id=resolve(choice);try{localStorage.setItem('kotoba:theme',choice);}catch(_){}
 document.documentElement.setAttribute('data-theme',id);document.documentElement.setAttribute('data-theme-choice',choice);
 const meta=document.querySelector('meta[name="theme-color"]');if(meta)meta.content=themes.find(t=>t.id===id).paper;
}
window.KotobaThemeCatalog={themes,migrate,resolve,read};early();
})();
