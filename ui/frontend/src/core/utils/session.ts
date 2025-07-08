// Генерация и получение session_id (uuid v4) из localStorage
function uuidv4() {
  // https://stackoverflow.com/a/2117523/65387
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export function getSessionId(): string {
  let sessionId = localStorage.getItem('session_id');
  if (!sessionId) {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      sessionId = crypto.randomUUID();
    } else {
      sessionId = uuidv4();
    }
    localStorage.setItem('session_id', sessionId);
  }
  return sessionId;
}
