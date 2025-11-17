const socket = io();
let myNode = null;

// Chart data
const latencyData = {Direct: [], PubSub: []};
const throughputData = {Direct: [], PubSub: []};
const timeLabels = [];
let latencyChart, throughputChart;

document.getElementById('registerBtn').addEventListener('click', () => {
  myNode = document.getElementById('nodeSelect').value;
  socket.emit('register', {node: myNode});
  logEvent(`Registered as node ${myNode}`);
});

document.getElementById('updateConfigBtn').addEventListener('click', () => {
  const cfg = {
    loss_rate: document.getElementById('lossRate').value,
    latency_min: document.getElementById('latencyMin').value,
    latency_max: document.getElementById('latencyMax').value,
    max_retries: document.getElementById('maxRetries').value,
    ack_timeout: document.getElementById('ackTimeout').value
  };
  socket.emit('update_config', cfg);
  logEvent('Config update sent');
});

socket.on('connected', (d) => { logEvent('Socket connected'); initCharts(); });
socket.on('registered', (d) => { logEvent('Server acknowledged registration: '+d.node) });
socket.on('config_updated', (cfg) => {
  document.getElementById('lossRate').value = cfg.loss_rate;
  document.getElementById('latencyMin').value = cfg.latency_min;
  document.getElementById('latencyMax').value = cfg.latency_max;
  document.getElementById('maxRetries').value = cfg.max_retries;
  document.getElementById('ackTimeout').value = cfg.ack_timeout;
  logEvent('Config updated by server');
});

function sendFrom(node){
  const method = document.getElementById('methodSelect').value;
  let to = (node === 'A') ? 'B' : 'A';
  const content = (node === 'A') ? document.getElementById('msgA').value : document.getElementById('msgB').value;
  const payload = {from: node, to: to, method: method, content: content};
  socket.emit('send_message', payload);
  appendPanel(node, `You -> ${to}: ${content}`);
}

socket.on('message', (data) => {
  // delivered generic message
  appendPanel(data.to, `(${data.method}) ${data.from} -> ${data.to}: ${data.content}`);
  logEvent(`Delivered (Direct): ${data.msg_id} from ${data.from} to ${data.to}`);
});

socket.on('pubsub_message', (data) => {
  // For pubsub, each subscriber receives message and should ACK
  appendPanel(data.to, `(PubSub attempt ${data.attempt}) ${data.from} -> ${data.to}: ${data.content}`);
  // send ack back to server
  socket.emit('pubsub_ack', {msg_id: data.msg_id, node: data.to});
  logEvent(`PubSub received by ${data.to} attempt ${data.attempt}`);
});

socket.on('sent_ack', (d) => { logEvent(`Server accepted send (${d.msg_id}) method=${d.method}`); });
socket.on('delivery_failed', (d) => { logEvent(`Delivery failed: ${d.msg_id} (${d.reason})`) });

socket.on('metrics_update', (snap) => {
  const el = document.getElementById('metrics');
  el.innerHTML = '';
  const now = new Date().toLocaleTimeString();
  for(const k of Object.keys(snap)){
    const s = snap[k];
    const line = `${k}: sent=${s.sent} delivered=${s.delivered} lost=${s.lost} avg_latency=${s.avg_latency}s`;
    const p = document.createElement('div'); p.textContent = line; el.appendChild(p);
    // Update chart data
    latencyData[k].push(s.avg_latency);
    if(latencyData[k].length > 20) latencyData[k].shift();
    const rate = s.delivered / ((Date.now() / 1000) || 1); // rough throughput
    throughputData[k].push(rate);
    if(throughputData[k].length > 20) throughputData[k].shift();
  }
  // Update time labels
  timeLabels.push(now);
  if(timeLabels.length > 20) timeLabels.shift();
  updateCharts();
});

function appendPanel(node, text){
  const id = (node === 'A') ? 'panelA' : 'panelB';
  const el = document.getElementById(id);
  const d = document.createElement('div'); d.textContent = `[${(new Date()).toLocaleTimeString()}] ` + text; el.appendChild(d); el.scrollTop = el.scrollHeight;
}

function logEvent(text){
  const el = document.getElementById('eventLog');
  const d = document.createElement('div'); d.textContent = `[${(new Date()).toLocaleTimeString()}] ` + text; el.appendChild(d); el.scrollTop = el.scrollHeight;
}

function initCharts(){
  const latencyCtx = document.getElementById('latencyChart').getContext('2d');
  latencyChart = new Chart(latencyCtx, {
    type: 'line',
    data: {
      labels: timeLabels,
      datasets: [
        {label: 'Direct', data: latencyData.Direct, borderColor: 'rgb(75, 192, 192)', tension: 0.1},
        {label: 'PubSub', data: latencyData.PubSub, borderColor: 'rgb(255, 99, 132)', tension: 0.1}
      ]
    },
    options: {responsive: true, maintainAspectRatio: false, scales: {y: {beginAtZero: true}}}
  });
  const throughputCtx = document.getElementById('throughputChart').getContext('2d');
  throughputChart = new Chart(throughputCtx, {
    type: 'line',
    data: {
      labels: timeLabels,
      datasets: [
        {label: 'Direct', data: throughputData.Direct, borderColor: 'rgb(75, 192, 192)', tension: 0.1},
        {label: 'PubSub', data: throughputData.PubSub, borderColor: 'rgb(255, 99, 132)', tension: 0.1}
      ]
    },
    options: {responsive: true, maintainAspectRatio: false, scales: {y: {beginAtZero: true}}}
  });
}

function updateCharts(){
  if(latencyChart){
    latencyChart.data.labels = timeLabels;
    latencyChart.data.datasets[0].data = latencyData.Direct;
    latencyChart.data.datasets[1].data = latencyData.PubSub;
    latencyChart.update('none');
  }
  if(throughputChart){
    throughputChart.data.labels = timeLabels;
    throughputChart.data.datasets[0].data = throughputData.Direct;
    throughputChart.data.datasets[1].data = throughputData.PubSub;
    throughputChart.update('none');
  }
}
