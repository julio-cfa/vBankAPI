# vBankAPI

<div align="center"><img src="https://i.imgur.com/6GoqypC.png" width="350"></center></div>
<p align="justify"></p><strong>Vulnerable Bank API (vBankAPI)</strong> is an application written with FastAPI and <strong>vulnerable by design and by default</strong>. The idea of this API is to help security professionals - especially junior security engineers, junior penetration testers, and the like - understand vulnerabilities that could be found in the wild.</p>

<p align="justify">I decided to use FastAPI for two reasons: 1) it is made for Python; and 2) the syntax and its structure is easy for people who are not very development-savvy to understand. I, myself, am not a developer and still struggle with some software engineering concepts (you will see how terribly written this project is). Writing this API has helped me a lot and I would encourage anyone working with application security to develop a similar project.</p>

## Vulnerabilities

The flaws in this API include, but are not limited to:
- Broken Access Control
- Insecure CORS
- Information Disclosure
- SQL Injection
- Hidden Functionality (Backdoor)
- OS Command Injection
- Hardcoded Secrets
- Security Misconfiguration

## Running It

The easiest way to run vBankAPI is by using <a href="https://docs.docker.com/engine/install/">Docker</a>. You can execute the following commands:

```bash
git clone https://github.com/julio-cfa/vBankAPI.git
cd vBankAPI
docker build -t vbank-api .
docker run -d -p 8000:8000 vbank-api
```

If you want to run it without Docker, it is also possible:
```bash
git clone https://github.com/julio-cfa/vBankAPI.git
cd vBankAPI
pip3 install -r requirements.txt
uvicorn main:app --reload
```

Either way you will be able to access the API over http://127.0.0.1:8000. However, I would recommend adding an entry to your `/etc/hosts`:

```bash
sudo echo "127.0.0.1	vbank.api" >> /etc/hosts
```

After that, you will be able to access the API over http://vbank.api:8000.

## Testing The API

The way this project was designed, this API should be tested with a white-box approach. You should run a SAST, perform a manual code review, and also do a penetration test. There are vulnerabilities that can only be detected by inspecting the code.

The API code is simple enough so that people with not a lot of programming and/or code review experience can go through the code and find such vulnerabilities.

At http://127.0.0.1:8000/docs you will find Swagger documentation that you can leverage for your tests.

