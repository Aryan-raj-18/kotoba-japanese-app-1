"""Verify signed Android outputs and extract their actual Python package for tests.

Requires Python 3.13 and KOTOBA_TOOLS pointing to SDK/JDK/bundletool.
"""
import hashlib,io,json,marshal,os,re,shutil,struct,subprocess,types,zipfile
from pathlib import Path
root=Path(__file__).parent.resolve();tools=Path(os.environ['KOTOBA_TOOLS']);out=root/'verification'
jdk=tools/'jdk/usr/lib/jvm/java-17-openjdk-amd64';sdk=tools/'sdk/build-tools/36.0.0'
env=os.environ.copy();env['JAVA_HOME']=str(jdk);env['PATH']=str(jdk/'bin')+':'+env['PATH']
def run(name,args):
 p=subprocess.run([str(a) for a in args],capture_output=True,text=True,env=env)
 (out/(name+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,(name,p.returncode)
 return p.stdout+p.stderr
apk=root/'android/app/build/outputs/apk/release/app-release.apk';aab=root/'android/app/build/outputs/bundle/release/app-release.aab'
cert='C603358EF51A0F7A9C9C21592880B63700E872533B3C499B033A2D8D22AD0976'
signature=run('apk-signature',[sdk/'apksigner','verify','--verbose','--print-certs',apk]);assert cert.lower() in signature.lower().replace(':','')
badging=run('apk-version',[sdk/'aapt','dump','badging',apk]);assert "versionCode='47'" in badging and "versionName='1.0.0'" in badging
run('zip-alignment',[sdk/'zipalign','-c','-P','16','4',apk])
assert 'jar verified' in run('aab-signature',[jdk/'bin/jarsigner','-verify',aab])
assert cert in run('aab-certificate',[jdk/'bin/keytool','-printcert','-jarfile',aab]).replace(':','')
run('bundle-validation',[jdk/'bin/java','-jar',tools/'bundletool.jar','validate','--bundle='+str(aab)])
config=run('bundle-config',[jdk/'bin/java','-jar',tools/'bundletool.jar','dump','config','--bundle='+str(aab)]);assert 'PAGE_ALIGNMENT_16K' in config
metadata={'version':'1.0.0','version_code':47,'artifacts':{}};payloads=[];dexes=[]
for file,prefix in [(apk,''),(aab,'base/')]:
 b=file.read_bytes();info={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};libs=[]
 with zipfile.ZipFile(file) as z:
  dex={Path(n).name:z.read(n) for n in z.namelist() if n.endswith('.dex')}
  assert any(b'KotobaKanjiNotificationNative' in content for content in dex.values())
  dexes.append(dex)
  payloads.append(z.read(prefix+'assets/chaquopy/app.imy'))
  assert z.read(prefix+'assets/kotoba-opening.html')==(root/'android/app/src/main/assets/kotoba-opening.html').read_bytes()
  assert z.read(prefix+'assets/kanji-notification.json')==(root/'android/app/src/main/assets/kanji-notification.json').read_bytes()
  for name in z.namelist():
   if name.endswith('.so'):
    elf=z.read(name);assert elf[:5]==b'\x7fELF\x02'
    offset=struct.unpack_from('<Q',elf,32)[0];size,count=struct.unpack_from('<HH',elf,54)
    aligns=[struct.unpack_from('<IIQQQQQQ',elf,offset+i*size)[7] for i in range(count) if struct.unpack_from('<I',elf,offset+i*size)[0]==1]
    assert aligns and min(aligns)>=16384,(name,aligns);libs.append({'name':name,'minimum_PT_LOAD_alignment':min(aligns)})
 info.update(intro_matches=True,kanji_catalog_matches=True,native_libraries=libs);metadata['artifacts'][file.suffix]=info
assert payloads[0]==payloads[1];metadata['APK_AAB_payload_identical']=True
assert dexes[0]==dexes[1];metadata['APK_AAB_Dex_identical']=True
package=root/'android/app/src/main/python';asset_count=0;python_count=0
def equal_code(a,b):
 for name in ['co_code','co_names','co_varnames','co_freevars','co_cellvars','co_argcount','co_kwonlyargcount','co_posonlyargcount','co_flags']:assert getattr(a,name)==getattr(b,name),name
 assert len(a.co_consts)==len(b.co_consts)
 for x,y in zip(a.co_consts,b.co_consts):
  if isinstance(x,types.CodeType):assert isinstance(y,types.CodeType);equal_code(x,y)
  else:assert x==y
with zipfile.ZipFile(io.BytesIO(payloads[1])) as z:
 for f in package.rglob('*'):
  if not f.is_file() or '__pycache__' in f.parts:continue
  name=f.relative_to(package).as_posix()
  if f.suffix=='.py':
   code=marshal.loads(z.read(name+'c')[16:]);equal_code(code,compile(f.read_text(),code.co_filename,'exec'));python_count+=1
  else:assert z.read(name)==f.read_bytes(),name;asset_count+=1
 actual=tools/'actual-package'
 if actual.exists():shutil.rmtree(actual)
 actual.mkdir();z.extractall(actual)
 assert not any('/login' in n or '/signup' in n for n in z.namelist() if '/templates/' in n)
 for f in actual.rglob('*.py'):f.unlink()
metadata.update(packaged_asset_matches=asset_count,compiled_modules_match=python_count,actual_package=str(actual))
with zipfile.ZipFile(os.environ['KOTOBA_BASELINE_ZIP']) as baseline:
 count=0
 for f in (root/'data').glob('*.json'):
  name='kotoba-1.0.0/data/'+f.name
  if name in baseline.namelist():
   assert baseline.read(name)==f.read_bytes(),name;count+=1
 assert count==21;metadata['original_course_JSON_unchanged']=count
lint=root/'android/app/build/reports/lint-results-release.txt';text=lint.read_text();assert '0 errors' in text
metadata['lint_summary']=re.search(r'\d+ errors, \d+ warnings',text).group();(out/'lint-results-release.txt').write_text(text)
(out/'artifact-verification.json').write_text(json.dumps(metadata,indent=2)+'\n')
print('PASS signatures, build 47 identity, bundle, 16 KB alignment, all compiled/source assets, identical payloads, 21 unchanged public JSON files')
