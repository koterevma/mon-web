sudo apt update
sudo apt install -y python3-venv python3-pip
python3 -m venv venv
source venv/bin/activate
pip install --no-cache-dir -U pip wheel
pip install -r requirements.txt --no-cache-dir