read -s -p "Enter Desktop Password: " PASS && echo ""
ssh -t spoob@ciel.local "sudo YDOTOOL_SOCKET=/tmp/.ydotool_socket ydotool type '$PASS' && sudo YDOTOOL_SOCKET=/tmp/.ydotool_socket ydotool key 28:1 28:0"
