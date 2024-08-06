add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt upgrade -y
apt install git -y

git clone https://github.com/simplycleverlol/vpb.git

wget https://get.vpnsetup.net -O vpn.sh && sudo sh vpn.sh
wget -O wireguard.sh https://get.vpnsetup.net/wg && sudo bash wireguard.sh --auto
wget -O openvpn.sh https://get.vpnsetup.net/ovpn && sudo bash openvpn.sh --auto
wget -O add_vpn_user.sh https://raw.githubusercontent.com/hwdsl2/setup-ipsec-vpn/master/extras/add_vpn_user.sh
wget -O del_vpn_user.sh https://raw.githubusercontent.com/hwdsl2/setup-ipsec-vpn/master/extras/del_vpn_user.sh
wget -O ikev2.sh https://raw.githubusercontent.com/hwdsl2/setup-ipsec-vpn/master/extras/ikev2setup.sh 

iptables -I INPUT -p tcp --dport 443  -j ACCEPT
iptables -I INPUT -p tcp --dport 8080  -j ACCEPT
iptables -I INPUT -p tcp --dport 1488  -j ACCEPT
iptables-save > /etc/iptables.rules

wget -qO- https://raw.githubusercontent.com/Jigsaw-Code/outline-server/master/src/server_manager/install_scripts/install_server.sh | bash

chmod u+x *.sh

cd vpb
apt-get -y install python3.11 python3-pip python3.11-venv lrzsz
python3.11 -m venv venv

./venv/bin/python -m pip install -r requirements.txt

cp vpn_api.service /lib/systemd/system/
systemctl daemon-reload
systemctl start vpn_api.service
systemctl enable vpn_api.service
