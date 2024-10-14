wget https://static.adguard.com/adguardhome/release/AdGuardHome_linux_amd64.tar.gz
tar -xzf AdGuardHome_linux_amd64.tar.gz
cd AdGuardHome

sudo mkdir -p /etc/systemd/resolved.conf.d
echo $'[Resolve]\nDNS=127.0.0.1\nDNSStubListener=no' > /etc/systemd/resolved.conf.d/adguardhome.conf
sudo mv /etc/resolv.conf /etc/resolv.conf.backup
sudo ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf
sudo systemctl reload-or-restart systemd-resolved

sudo ./AdGuardHome -s install
sleep 2
API_PASS=$(openssl rand -base64 16)
echo ADGUARD_PASS="$API_PASS" > adgps

curl 'http://localhost:3000/control/install/configure' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: en-US,en;q=0.9,ru-US;q=0.8,ru;q=0.7' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36' \
  --data-raw "{\"web\":{\"ip\":\"0.0.0.0\",\"port\":3033,\"status\":\"\",\"can_autofix\":false},\"dns\":{\"ip\":\"0.0.0.0\",\"port\":53,\"status\":\"\",\"can_autofix\":false},\"username\":\"admin\",\"password\":\"$API_PASS\"}" \
  --insecure

sudo ./AdGuardHome -s stop

grep -E "^users:|^\s+- name:|^\s+password:" AdGuardHome.yaml > temp.yaml
cat ../preset.yaml >> temp.yaml
mv temp.yaml AdGuardHome.yaml

sudo ./AdGuardHome -s start

cd ..
rm AdGuardHome_linux_amd64.tar.gz