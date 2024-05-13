# BETA-vBankAPI
This is the BETA version of the vBankAPI. An API that was designed to be vulnerable.

## Installation

The easiest way to run vBankAPI is by using Docker. You can execute the following commands:

```bash
git clone https://github.com/julio-cfa/BETA-vBankAPI.git
cd BETA-vBankAPI
docker build -t vbank-api .
docker run -d -p 8000:8000 vbank-api
```

You can now access the API over http://127.0.0.1:8000. However, I'd recommend adding an entry to your /etc/hosts:

```bash
sudo echo "127.0.0.1	vbank.api" >> /etc/hosts
```

After that, you will be able to access the API over http://vbank.api.
