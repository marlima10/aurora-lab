import fs from 'node:fs';
const path='index.html';let html=fs.readFileSync(path,'utf8');
if(!html.includes('<title>MagicMirror²</title>'))throw Error('Unexpected upstream index');
html=html.replace('<html>','<html lang="pt-BR">').replace('<title>MagicMirror²</title>','<title>AuroraLAB · Início</title>\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta name="theme-color" content="#231e17">\n<meta name="apple-mobile-web-app-title" content="AuroraLAB">\n<link rel="manifest" href="/manifest.json">\n<link rel="apple-touch-icon" href="/icons/app-192.png">');
html=html.replace('href="favicon.svg"','href="/favicon.svg"');
fs.writeFileSync(path,html);

const socketPath='js/socketclient.js',socket=fs.readFileSync(socketPath,'utf8');
const old='"/socket.io/socket.io.esm.min.js"';
if(socket.split(old).length!==2)throw Error('Unexpected upstream Socket.IO import');
fs.writeFileSync(socketPath,socket.replace(old,'"../socket.io/socket.io.esm.min.js"'));
