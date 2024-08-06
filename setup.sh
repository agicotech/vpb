apt update
apt upgrade -y
wget https://get.vpnsetup.net -O vpn.sh && sudo sh vpn.sh
wget -O wireguard.sh https://get.vpnsetup.net/wg && sudo bash wireguard.sh --auto
wget -O openvpn.sh https://get.vpnsetup.net/ovpn && sudo bash openvpn.sh --auto
iptables -I INPUT -p tcp --dport 443  -j ACCEPT
iptables -I INPUT -p tcp --dport 8080  -j ACCEPT
iptables-save > /etc/iptables.rules
sudo wget -qO- https://raw.githubusercontent.com/Jigsaw-Code/outline-server/master/src/server_manager/install_scripts/install_server.sh | bash
