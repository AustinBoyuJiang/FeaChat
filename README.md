# FeaChat

FeaChat is the first chat application I developed using Python. One funny thing I did was writing all 3000+ lines of code in a single file. You can review it in ./client/old/client.pyw. This is a record of my progress.

## Modern Stack

The active migration target is:

- Client: React + Tauri
- Server: FastAPI + WebSocket
- DB: SQLite now, PostgreSQL later
- Communication: REST for auth, friends, and history; WebSocket for real-time messages

The old PyQt/socket client is still kept under `client/` while the migration is in progress. The new desktop client lives in `desktop-client/`.

## Environments

Create the Python environments:

```bash
conda env create -f environment-server.yml
conda env create -f environment-client.yml
```

Install the React/Tauri client dependencies:

```bash
cd desktop-client
npm install
```

Tauri native builds require Rust/Cargo. This machine currently has Node/npm available but no `cargo`, so the React client can run with Vite first. After Rust is installed, use `npm run tauri dev`.

## Server

Create a local environment file:

```bash
cp server/.env.example server/.env
```

Run the FastAPI server:

```bash
conda activate feachat-server
python -m server
```

The API listens on `http://127.0.0.1:8000` by default. SQLite data is stored at `server/data/feachat.db` unless `DB_PATH` is overridden.

Run the server tests:

```bash
conda activate feachat-server
python -m unittest server.tests.test_api
```

## Desktop Client

Run the React client in browser dev mode:

```bash
cd desktop-client
npm run dev
```

Open `http://127.0.0.1:1420`.

After Rust/Cargo is installed, run the Tauri shell:

```bash
cd desktop-client
npm run tauri dev
```

## Quick Two-Account Dev

This seeds `alice1` and `bob001`, starts the FastAPI server and Vite client, then opens two isolated Chrome profiles:

```bash
./scripts/start_modern_dev.sh
```

Both accounts use password `secret1`.

To start two Tauri desktop windows instead:

```bash
./scripts/start_modern_tauri_clients.sh
```

## Legacy Client

The old PyQt client can still be run while migration is underway:

```bash
conda activate feachat-client
python -m client
```

![FeaChat](https://github.com/AustinBoyuJiang/FeaChat/blob/master/demo/img/1.png)
![FeaChat](https://github.com/AustinBoyuJiang/FeaChat/blob/master/demo/img/2.png)
![FeaChat](https://github.com/AustinBoyuJiang/FeaChat/blob/master/demo/img/3.png)
![FeaChat](https://github.com/AustinBoyuJiang/FeaChat/blob/master/demo/img/4.png)
