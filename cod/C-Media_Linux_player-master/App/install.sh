#!/bin/sh

echo "Instalando..."

if [ -d "$HOME/Desktop" ]
then
	ESCRITORIO="$HOME/Desktop"
else	
	ESCRITORIO="$HOME/Escritorio"
fi

echo $ESCRITORIO
sudo cp C-Media_Player_config.desktop C-Media_Player.desktop /usr/share/applications
sudo cp C-Media_Player_config.desktop C-Media_Player.desktop "$ESCRITORIO"
sudo chown $USER:dialout "$ESCRITORIO/C-Media_Player_config.desktop" 
sudo chown $USER:dialout "$ESCRITORIO/C-Media_Player.desktop" 
sudo chmod 775 "$ESCRITORIO/C-Media_Player_config.desktop" 
sudo chmod 775 "$ESCRITORIO/C-Media_Player.desktop" 
sudo cp -r /home/digiturno/Escritorio/CMedia_Player_installer/CMedia_Player  /usr/share/C-Media_Player
sudo cp C-Media_Player /usr/bin
sudo cp logo/CmediaPlayer.png /usr/share/pixmaps/CmediaPlayer.png
sudo cp logo/CmediaPlayerLx.png /usr/share/pixmaps/CmediaPlayerLx.png
sudo cp logo/CmediaPlayerC.png /usr/share/pixmaps/CmediaPlayerC.png
sudo cp 50-CMediaPlayer.rules /lib/udev/rules.d/50-CMediaPlayer.rules

sudo udevadm control --reload
sudo udevadm trigger
sudo apt-get -y install mpg123

CMEDIA_PATH="$HOME/.config/Ciel/C-Media_Player"
mkdir -p "$CMEDIA_PATH/configs"

mkdir -p "$CMEDIA_PATH/logs"
mkdir -p "$CMEDIA_PATH/certificados"

sudo cp /usr/local/share/ca-certificates/server.crt /home/digiturno/.config/Ciel/C-Media_Player/certificados
sudo cp config.json "$CMEDIA_PATH/configs/config.json"
sudo cp LinuxPlayer.ccmj "$CMEDIA_PATH/configs/LinuxPlayer.ccmj"
sudo chown $USER:dialout "$CMEDIA_PATH/configs/config.json" 
sudo chown $USER:dialout "$CMEDIA_PATH/configs/LinuxPlayer.ccmj" 
sudo cp -r Media "$CMEDIA_PATH"

gnome-extensions install disable-gestures@mattbell.com.au.v2.shell-extension.zip 
gnome-extensions enable disable-gestures@mattbell.com.au
gnome-extensions install cariboublocker@git.keringar.xyz.v1.shell-extension.zip
gnome-extensions enable cariboublocker@git.keringar.xyz
sudo adduser $USER dialout 
sudo adduser $USER lp

echo "La aplicacion se ha instalado"
