interface ConfigType {
  basenameFrontend: string;
  domain: string;
  port: string;
  apiPath: string;
  defaultList: string[];
  backendCheckToPath: string;
}

let globalConfig: ConfigType | null = null;
let cachedUrl: string | null = null; // Кэшируем результат

try {
    const configModule = await import("../config/config") as { globalConfig: ConfigType };
    globalConfig = configModule.globalConfig;
    console.log('Импорт globalConfig прошел успешно:', globalConfig);
} catch (error) {
    console.error('Ошибка импорта globalConfig:', error);
    globalConfig = null; 
}

export async function init(): Promise<string | null> {
    // Если уже есть кэшированный результат, возвращаем его
    if (cachedUrl) {
        console.log('Используем кэшированный URL:', cachedUrl);
        return cachedUrl;
    }
    
    console.log('🚀 Начинаем инициализацию...');
    const protocol = window.location.protocol.replace(':', '');
    
    if (!globalConfig) {
        console.error('❌ globalConfig не загружен');
        return null;
    }
    
    if (!globalConfig.port) {
        console.log('⚠️ Порт не задан');
    }

    // Создаем массив всех возможных URL для проверки
    const urlsToCheck: string[] = [];
    
    // Сначала добавляем основной путь бэкенда (если задан)
    if (globalConfig.backendCheckToPath) {
        urlsToCheck.push(`${protocol}://${globalConfig.backendCheckToPath}/init437721`);
    }
    
    // Затем добавляем все пути из defaultList
    for (const proto of ['https', 'http']) {
        for (const path of globalConfig.defaultList) {
            const url = `${proto}://${path}/init437721`;
            // Избегаем дублирования URL
            if (!urlsToCheck.includes(url)) {
                urlsToCheck.push(url);
            }
        }
    }

    console.log(`🔍 Начинаем параллельную проверку ${urlsToCheck.length} путей...`);
    
    // Запускаем все проверки параллельно
    const checkPromises = urlsToCheck.map(async (url, index) => {
        try {
            console.log(`   ${index + 1}. Проверяем: ${url}`);
            const result = await checkConnection(url);
            return result ? { url, result } : null;
        } catch (error) {
            console.log(`   ❌ ${url} - ошибка: ${error}`);
            return null;
        }
    });

    // Ждем результата от первого успешного соединения
    try {
        const results = await Promise.allSettled(checkPromises);
        
        // Ищем первый успешный результат
        for (const result of results) {
            if (result.status === 'fulfilled' && result.value) {
                cachedUrl = result.value.result;
                console.log(`✅ Найден работающий сервер: ${result.value.url}`);
                console.log('✅ Инициализация завершена успешно');
                return cachedUrl;
            }
        }
        
        console.error('❌ Все попытки подключения не удались');
        return null;
    } catch (error) {
        console.error('❌ Ошибка при параллельной проверке:', error);
        return null;
    }
}

// Функция для сброса кэша (если нужно переподключиться)
export function resetCache(): void {
    cachedUrl = null;
    console.log('🔄 Кэш инициализации сброшен');
}

async function checkConnection(url: string): Promise<string | null> {
    try {
        console.log('Проверяем соединение с:', url);
        
        // Создаем AbortController для таймаута
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 секунд таймаут
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        console.log('Ответ получен:', response.status);
        
        if (response.status === 200) {
            const data = await response.json();
            if (data.status === 'ok') {
                console.log('✅ Успешное соединение с:', url);
                return url;
            }
        }
        console.log('❌ Неверный ответ от:', url);
        return null;
    } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
            console.error('⏰ Таймаут соединения с:', url);
        } else {
            console.error('❌ Ошибка соединения с:', url, error);
        }
        return null;
    }
}