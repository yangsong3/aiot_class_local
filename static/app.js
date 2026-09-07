const byId = (id) => document.getElementById(id);
let currentState = null;
let busy = false;

function render(state) {
  currentState = state;
  byId('led-state').textContent = state.led ? '켜짐' : '꺼짐';
  byId('button-state').textContent = state.button ? '눌림' : '대기';
  byId('led-light').classList.toggle('active', state.led);
  byId('button-light').classList.toggle('active', state.button);
  byId('led-on').disabled = state.led;
  byId('led-off').disabled = !state.led;
  const mockButton = byId('mock-button');
  if (mockButton) {
    mockButton.disabled = false;
    mockButton.textContent = state.button ? '모의 버튼 놓기' : '모의 버튼 누르기';
    mockButton.setAttribute('aria-pressed', String(state.button));
  }
  byId('connection').textContent = state.mock ? '● 모의 장치 연결됨' : '● 장치 연결됨';
  byId('error').hidden = true;
}

async function sync(device, on) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button').forEach((button) => { button.disabled = true; });
  try {
    const response = await fetch(device ? `/api/${device}` : '/api/state', {
      method: device ? 'POST' : 'GET',
      headers: device ? { 'Content-Type': 'application/json' } : {},
      body: device ? JSON.stringify({ on }) : undefined,
      cache: 'no-store',
      signal: AbortSignal.timeout(5000),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '장치 요청에 실패했습니다.');
    render(data);
  } catch (error) {
    byId('connection').textContent = '○ 연결 확인 필요';
    byId('led-state').textContent = '확인 불가';
    byId('button-state').textContent = '확인 불가';
    byId('led-light').classList.remove('active');
    byId('button-light').classList.remove('active');
    byId('error').textContent = `${error.message} 서버 연결을 확인하세요. 자동으로 다시 연결합니다.`;
    byId('error').hidden = false;
  } finally {
    busy = false;
  }
}

byId('led-on').addEventListener('click', () => sync('led', true));
byId('led-off').addEventListener('click', () => sync('led', false));
byId('mock-button')?.addEventListener('click', () => sync('button', !currentState.button));

async function poll() {
  await sync();
  window.setTimeout(poll, 500);
}
poll();
