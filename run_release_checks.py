"""Run the release regressions with optional extracted compiled Android modules."""
import json,os,subprocess,sys,time
from pathlib import Path
root=Path(__file__).parent.resolve();out=root/'verification';out.mkdir(exist_ok=True)
python=os.environ.get('KOTOBA_TEST_PYTHON',sys.executable)
suites=[('content',[python,'test_restored_content.py']),('search',[python,'test_search.py','--android']),('safety',[python,'test_release_safety.py']),('numbers-startup',[python,'test_numbers_startup.py']),('cloud',[python,'test_cloud_sync.py']),('assets',[python,'test_asset_loading.py']),('speaking-phrasebook',[python,'test_speaking_phrasebook.py']),('original-speaking-data',[python,'test_original_speaking_data.py'])]
suites.append(('speaking-situations',['node','test_speaking_situations.cjs']))
suites.append(('liquid-glass',['node','test_liquid_glass.cjs']))
suites.append(('glass-layout-contract',[python,'-m','unittest','test_glass_integration','test_glass_coverage','test_glass_surface_41','test_glass_artifacts_42','test_water_glass_build43','test_responsive_shell','test_content_categories']))
suites.append(('kanji-notification-catalog',[python,'test_kanji_notification.py']))
suites.append(('roadmap-order',[python,'test_roadmap_order.py']))
suites.append(('speech-reading-data',[python,'test_speech_readings.py']))
for name in ['speech_readings','roadmap_position','navigation_theme','kanji_themes','journey_home','onboarding','kanji_notification','search_suggestions','scroll_lock','jlpt_mock','cloud_sync','audio_lifecycle','intro_startup','catalog_batches','browser_cache','voice_search','japan_map','speaking']:
 suites.append((name,['node','test_'+name+('.js' if name=='voice_search' else '.cjs')]))
if os.environ.get('KOTOBA_TEST_PACKAGE'):suites.append(('actual-bundle-smoke',[python,'smoke_test_android.py']))
results=[]
for name,args in suites:
 start=time.monotonic()
 p=subprocess.run(args,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (out/(name+'.log')).write_text(p.stdout)
 results.append(dict(suite=name,exit_code=p.returncode,seconds=round(time.monotonic()-start,2)))
 print(name,p.returncode,flush=True)
(out/'regression-results.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['exit_code']==0 for r in results),results
