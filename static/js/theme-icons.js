/* Original vector icon skins: semantic shapes keep the same labels/actions. */
(function(){'use strict';
 const paths={
 home:'<path d="M3 11L12 3l9 8v10h-6v-7H9v7H3z"/>',
 learn:'<path d="M3 5c4-1 7 0 9 2 2-2 5-3 9-2v14c-4-1-7 0-9 2-2-2-5-3-9-2zM12 7v14"/>',
 review:'<path d="M20 7a9 9 0 1 0 1 8M20 2v6h-6"/><path d="M8 12l3 3 5-6"/>',
 explore:'<circle cx="12" cy="12" r="9"/><path d="M8 16l2-6 6-2-2 6z"/>',
 progress:'<path d="M4 21V11h4v10M10 21V7h4v14M16 21V3h4v18"/>',
 search:'<circle cx="10" cy="10" r="7"/><path d="M15 15l6 6"/>',
 voice:'<rect x="8" y="2" width="8" height="13" rx="4"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/>',
 settings:'<path d="M3 6h18M3 12h18M3 18h18"/><circle cx="8" cy="6" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="10" cy="18" r="2"/>',
 brand:'<path d="M5 4h14v11H9l-4 4zM8 8h8M8 11h5"/>'
 };
 const frames={ripple:'<circle cx="16" cy="16" r="15"/><path d="M3 23q6-4 13 0t13 0M5 27q5-3 11 0t11 0"/>',star:'<path d="M16 1l4 6 7-1-1 7 5 4-6 4 1 7-7-1-4 4-4-5-7 1 1-7-4-4 6-4-1-7 7 1z"/>',hex:'<path d="M8 1h16l7 8v14l-7 8H8l-7-8V9z"/><path d="M3 9h3M26 23h3"/>',torii:'<path d="M1 4q15 5 30 0M3 9h26M8 8v21M24 8v21M5 29h6M21 29h6"/>',bamboo:'<path d="M3 3v26M29 3v26M1 9h4M27 23h4M3 15q6-7 8-5M29 12q-6-7-8-5"/>',lantern:'<path d="M10 2h12M10 30h12M8 5h16q7 11 0 22H8q-7-11 0-22z"/><path d="M16 0v3M16 30v2"/>',fuji:'<path d="M1 27L16 2l15 25zM9 15l5 1 2-3 3 3 4-1"/>'};
 function refresh(){
  const theme=window.KotobaThemeCatalog.themes.find(t=>t.id===document.documentElement.dataset.theme);if(!theme)return;
  document.querySelectorAll('[data-theme-icon]').forEach(node=>{
   const key=node.dataset.themeIcon;if(key==='brand'||!paths[key]||node.dataset.iconSkin===theme.id)return;
   node.dataset.iconSkin=theme.id;node.classList.add('theme-icon');
   node.innerHTML='<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><g class="theme-icon-frame">'+'<rect x="1" y="1" width="30" height="30" rx="10"/>'+'</g><g transform="translate(6 6) scale(.84)" class="theme-icon-symbol">'+paths[key]+'</g></svg>';
  });
 }
 window.KotobaThemeIcons={refresh};document.addEventListener('DOMContentLoaded',refresh);window.addEventListener('kotoba-theme-change',refresh);
})();
