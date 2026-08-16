# FeaChat

FeaChat is the first chat application I developed using Python. One funny thing I did was writing all 3000+ lines of code in a single file. You can review it in ./client/old/client.pyw. This is a record of my progress.

## Environments

This project keeps the GUI client and socket server dependencies separate.

```bash
conda env create -f environment-server.yml
conda env create -f environment-client.yml
```

## /server/

Create a local environment file:

```bash
cp server/.env.example server/.env
```

The server uses SQLite by default. Email variables are only required when sending register verification codes through SMTP.

### Initialization

First-time:
```bash
conda activate feachat-server
python -m server --init
```
Afterwards:
```bash
conda activate feachat-server
python -m server
```

Run the server tests:

```bash
conda activate feachat-server
python -m unittest server.tests.test_core
```

## /client/

Switch in core.py
```python
DEV_MODE = True/False
```

Run the client:

```bash
conda activate feachat-client
python -m client
```

When `DEV_MODE = True`, the client uses mock data and does not connect to the server. When `DEV_MODE = False`, it connects to the configured socket server.



![FeaChat](https://github.com/AustinBoyuJiang/FeaChat/blob/master/demo/img/1.png)
![FeaChat](https://github.com/AustinBoyuJiang/FeaChat/blob/master/demo/img/2.png)
![FeaChat](https://github.com/AustinBoyuJiang/FeaChat/blob/master/demo/img/3.png)
![FeaChat](https://github.com/AustinBoyuJiang/FeaChat/blob/master/demo/img/4.png)
