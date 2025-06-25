let globalConfig: {
  port: number;
  backendCheckToPath: string;
  defaultList: string[];
} | null;

try {
    // @ts-ignore
    ({ globalConfig } = await import("../config/config"));
    console.log('Импорт globalConfig прошел успешно:', globalConfig);
} catch (error) {
    console.error('Ошибка импорта globalConfig:', error);
    globalConfig = null; 
}

export async function init() {
    console.log('начало работы init')
    const protocol = window.location.protocol.replace(':', '');
    if (!globalConfig.port) {
        console.log('порт не задан');
    }

    if (globalConfig.backendCheckToPath) {
        const result = await checkConnection(`${protocol}://${globalConfig.backendCheckToPath}/init437721`);
        if (result) return result;
    }
    console.log('параметр backendCheckToPath не задан!')

    for (const proto of ['https', 'http']) {
        for (const path of globalConfig.defaultList) {
            const url = `${proto}://${path}/init437721`;
            console.log('проверка коннекта:', url)
            const result = await checkConnection(url);
            console.log('result:', result)
            if (result) return result;
        }
    }

    return null;
}

async function checkConnection(url) {
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        console.log('response (ответ):', response)
        if (response.status === 200) {
            const data = await response.json();
            if (data.status === 'ok') {
                return url;
            }
        }
        return null;
    } catch (error) {
        console.error('error: ', error);
        return null;
    }
}
