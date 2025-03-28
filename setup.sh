apt update
apt-get remove cloud-init -y
sh -c 'DEBIAN_FRONTEND=noninteractive apt-get upgrade -y'
sh -c 'DEBIAN_FRONTEND=noninteractive apt-get install git curl gpg-agent apt-utils -y'

curl https://get.docker.com/ | bash

echo "Checking docker installation"
if command -v docker &> /dev/null; then
    echo "Docker installation found"
else
    echo "Docker installation not found. Please install docker."
    exit 1
fi

add-apt-repository ppa:deadsnakes/ppa -y
apt update

git clone https://github.com/agicotech/vpb.git

#cd vpb
#bash setup_adguard.sh
#cd ..

#wget https://get.vpnsetup.net -O vpn.sh && sudo sh vpn.sh
wget -O wireguard.sh https://get.vpnsetup.net/wg && sudo bash wireguard.sh --dns1 94.140.14.14 --dns2 94.140.15.15 --auto
wget -O openvpn.sh https://get.vpnsetup.net/ovpn && sudo bash openvpn.sh --dns1 94.140.14.14 --dns2 94.140.15.15 --auto
#wget -O add_vpn_user.sh https://raw.githubusercontent.com/hwdsl2/setup-ipsec-vpn/master/extras/add_vpn_user.sh
#wget -O del_vpn_user.sh https://raw.githubusercontent.com/hwdsl2/setup-ipsec-vpn/master/extras/del_vpn_user.sh
#wget -O ikev2.sh https://raw.githubusercontent.com/hwdsl2/setup-ipsec-vpn/master/extras/ikev2setup.sh 

iptables -I INPUT -p tcp --dport 443  -j ACCEPT
iptables -I INPUT -p tcp --dport 8080  -j ACCEPT
iptables -I INPUT -p tcp --dport 1488  -j ACCEPT
iptables-save > /etc/iptables.rules

echo DNS=94.140.15.15#dns.adguard 94.140.14.14#dns.adguard 2a10:50c0::ad1:ff#dns.adguard 2a10:50c0::ad2:ff#dns.adguard >> /etc/systemd/resolved.conf
echo FallbackDNS=1.1.1.1#cloudflare-dns.com 1.0.0.1#cloudflare-dns.com 2606:4700:4700::1111#cloudflare-dns.com 2606:4700:4700::1001#cloudflare-dns.com >> /etc/systemd/resolved.conf
service systemd-resolved restart

wget -qO- https://raw.githubusercontent.com/Jigsaw-Code/outline-server/master/src/server_manager/install_scripts/install_server.sh | bash

git clone https://github.com/MHSanaei/3x-ui.git
cd 3x-ui
docker compose up -d 
# Захерачиваем контейнер с 3x-ui, там дефолтный логин пароль admin admin

sleep 5

# Времячко на раздуплиться

curl --cookie-jar tempcookies.txt --form password=admin --form username=admin http://localhost:2053/login

# Кладем в баночку печеньку

VLESSPWD=$(openssl rand -base64 33)

# Ohuenno difficult parol'

curl 'http://localhost:2053/panel/setting/updateUser'\
    -b tempcookies.txt \
    --form password=admin \
    --form username=admin \
    --form loginSecret= \
    --form oldUsername=admin \
    --form oldPassword=admin \
    --form newUsername=admin \
    --form newPassword=$VLESSPWD

# Меняем пароль

rm tempcookies.txt
# Куки нахуй
cd ..

echo XUI_PASSWORD="$VLESSPWD" >> .env
# Перешел с decouple на dotenv - так проще и более распространенное решение

chmod u+x *.sh


API_PASS=$(openssl rand -base64 33)
echo API_PASSWORD="$API_PASS" >> .env

ip=$(curl -s4 ifconfig.me)
openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes \
  -keyout server.key -out server.crt -subj "/CN=$ip" \
  -addext "subjectAltName=IP:$ip"

cd vpb

apt-get -y install python3.11 python3-pip python3.11-venv lrzsz
python3.11 -m venv venv

./venv/bin/python -m pip install -r requirements.txt

cp vpn_api.service /lib/systemd/system/
systemctl daemon-reload
systemctl start vpn_api.service
systemctl enable vpn_api.service

./venv/bin/python gen_config.py
