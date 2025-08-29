cd /root/vpb
git pull
./venv/bin/python -m pip install -r requirements.txt
cp /root/vpb/vpn_api.service /lib/systemd/system/vpn_api.service
systemctl daemon-reload
service vpn_api restart