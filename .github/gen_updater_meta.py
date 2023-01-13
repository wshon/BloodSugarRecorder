import hashlib, json, os, sys

def get_file_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as fp:
        while True:
            data = fp.read(4096)
            if not data: break
            md5.update(data)
    return md5.hexdigest().upper()

os.chdir('apk-release')
os.makedirs('apks', exist_ok = True)

print('open output-metadata.json')
with open('output-metadata.json') as fp:
    output_metadata = json.load(fp)

print('scan output-metadata.json')
for element in output_metadata['elements']:
    if element['type'] == 'UNIVERSAL':
        version_code = element['versionCode']
        print(f'version_code is {version_code}')
        version_name = element['versionName']
        print(f'version_name is {version_name}')
        break
else:
    print('type UNIVERSAL not in elements')
    exit(-1)

download_host = os.getenv('download_host')

print('rename apks')
for file_name in os.listdir('.'):
    if not file_name.endswith('.apk'): continue
    print(f'find apk {file_name}')
    if 'universal' in file_name:
        apk_path = f'apks/BloodSugarRecorder_{version_name}+{version_code}.apk'
        mate_file = 'updater.json'
    else:
        abi = file_name.split('-', 1)[-1].rsplit('-', 1)[0]
        apk_path = f'apks/BloodSugarRecorder_{abi}_{version_name}+{version_code}.apk'
        mate_file = f'updater_{abi}.json'
    print(f'rename {file_name} to {apk_path}')
    os.rename(file_name, apk_path)
    apk_size = os.path.getsize(apk_path)
    print(f'apk_size is {apk_size}')
    apk_md5 = get_file_md5(apk_path)
    print(f'apk_md5 is {apk_md5}')
    with open(mate_file, 'w') as fp:
        apk_meta = {
            "Code": 0,
            "Msg": "",
            "UpdateStatus": 1,
            "VersionCode": version_code,
            "VersionName": version_name,
            "ModifyContent": "发现新版本",
            "DownloadUrl": f"http://{download_host}/BloodSugarRecorder/{apk_path}",
            "ApkSize": apk_size,
            "ApkMd5": apk_md5
        }
        print(f'apk_meta is {apk_meta}')
        json.dump(apk_meta, fp, ensure_ascii = False, indent = 4)
        print(f'write apk_meta to {mate_file}')

print('remove output-metadata.json')
os.remove('output-metadata.json')

print('')
print('now is time clean upyun')
try:
    import upyun
except ImportError:
    import pip
    pip.main(["install", "requests", "upyun"])
    import upyun

service = os.getenv('service')
username = os.getenv('username')
password = os.getenv('password')
up = upyun.UpYun(service, username, password)
up_dir_path = '/BloodSugarRecorder/apks/'
up_files = up.getlist(up_dir_path)
for up_file in up_files:
    up_apk_name = up_file['name']
    up_apk_path = up_dir_path + up_apk_name
    print(f'find file on upyun {up_apk_path}')
    up_version_code = -1
    try:
        up_version_code = int(up_apk_name.split('+', 1)[-1].rsplit('.', 1)[0])
        print(f'up_version_code is {up_version_code}, i will keep it')
    except Exception as e:
        print(e)
    if version_code - up_version_code > 1:
        print(f'version_code {up_version_code} is too old, now is {version_code}')
        print(f'and i will delete this upyun file {up_apk_path}')
        up.delete(up_apk_path)
