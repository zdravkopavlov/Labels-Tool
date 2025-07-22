import os
import re
import json

CHANGELOG_FILE = os.path.join(os.path.dirname(__file__), "Documentation", "changelog.md")
VERSION_PY = os.path.join(os.path.dirname(__file__), "version.py")
LATEST_JSON = os.path.join(os.path.dirname(__file__), "git_release.json")
ISS_FILE = os.path.join(os.path.dirname(__file__), "Installer.iss")
# DOWNLOAD_URL_FMT = "https://github.com/zdravkopavlov/Currency-Coverter/releases/download/v{version}/BGN-EUR_Converter_Setup_{version}.exe"

def get_latest_version_info(changelog_file=CHANGELOG_FILE):
    with open(changelog_file, encoding="utf-8") as f:
        content = f.read()
    header_match = re.search(r"^##\s*([\d.]+)\s*\(([\d\-]+)\)", content, re.MULTILINE)
    if not header_match:
        raise RuntimeError("Could not find a version in the changelog.")
    version = header_match.group(1)
    date = header_match.group(2)
    # Find the changelog entry (lines after this header, until next ## or end)
    start = header_match.end()
    next_header = re.search(r"^##\s*", content[start:], re.MULTILINE)
    if next_header:
        end = start + next_header.start()
        entry = content[start:end].strip()
    else:
        entry = content[start:].strip()
    # Clean up bullet points and whitespace
    entry = re.sub(r'^\s*[-*]\s*', '- ', entry, flags=re.MULTILINE)
    entry = entry.strip()
    return version, date, entry

def write_version_py(version, version_py=VERSION_PY):
    with open(version_py, "w", encoding="utf-8") as f:
        f.write(f'VERSION = "{version}"\n')

def write_latest_version_json(version, changelog, date, json_file=LATEST_JSON):
    data = {
        "version": version,
        "download_url": DOWNLOAD_URL_FMT.format(version=version),
        "changelog": changelog,
        "date": date
    }
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_iss_version(iss_file, version):
    with open(iss_file, encoding="utf-8") as f:
        data = f.read()
    new_data = re.sub(
        r'(#define\s+MyAppVersion\s+)"[^"]+"',
        r'\1"{}"'.format(version),
        data
    )
    with open(iss_file, "w", encoding="utf-8") as f:
        f.write(new_data)

if __name__ == "__main__":
    version, date, changelog_entry = get_latest_version_info()
    write_version_py(version)
    write_latest_version_json(version, changelog_entry, date)
    update_iss_version(ISS_FILE, version)
    print(f"Updated version.py, latest_version.json, and Installer.iss to VERSION = \"{version}\"")
