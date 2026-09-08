const get = (id) => document.getElementById(id);
let busy = false;

function value(number, digits = 1) { return number == null ? '--' : Number(number).toFixed(digits); }
function render(state) {
  get('led-state').textContent = state.led ? '켜짐' : '꺼짐';
  get('led-icon').classList.toggle('active', state.led);
  const motorText = { forward: '정회전', reverse: '역회전', stop: '정지' };
  get('motor-state').textContent = motorText[state.motor];
  get('motor-icon').classList.toggle('spinning', state.motor !== 'stop');
  get('motor-icon').classList.toggle('reverse', state.motor === 'reverse');
  get('temperature').textContent = value(state.temperature);
  get('humidity').textContent = value(state.humidity);
  get('distance').textContent = value(state.distance);
  get('ultrasonic-state').textContent = state.ultrasonic_on ? '측정 중' : '꺼짐';
  get('connection').textContent = state.mock ? '● 모의 장치 연결됨' : '● Raspberry Pi 연결됨';
  get('error').hidden = true;
}
async function request(path = '/api/state', body) {
  if (busy) return;
  busy = true;
  try {
    const response = await fetch(path, {method: body ? 'POST' : 'GET', headers: body ? {'Content-Type':'application/json'} : {}, body: body ? JSON.stringify(body) : undefined, cache:'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '요청에 실패했습니다.');
    render(data);
  } catch (error) {
    get('connection').textContent = '● 연결 확인 필요';
    get('error').textContent = `${error.message} 서버 연결을 확인하세요.`;
    get('error').hidden = false;
  } finally { busy = false; }
}
document.querySelectorAll('[data-led]').forEach((button) => button.addEventListener('click', () => request('/api/led', {on: button.dataset.led === 'true'})));
document.querySelectorAll('[data-motor]').forEach((button) => button.addEventListener('click', () => request('/api/motor', {direction: button.dataset.motor})));
document.querySelectorAll('[data-ultrasonic]').forEach((button) => button.addEventListener('click', () => request('/api/ultrasonic', {on: button.dataset.ultrasonic === 'true'})));
async function poll() {
  await request();
  const interval = get('connection').textContent.includes('모의') ? 30000 : 2000;
  window.setTimeout(poll, interval);
}
poll();
