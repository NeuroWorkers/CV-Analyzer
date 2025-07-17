import { HighlightWithMarkdown } from '../ui/hightlight/HighlightWithMarkdown';

const TestAIHighlight = () => {
  const testText = "Техлидство / AI / спорт: https://t.me/etechlead";
  const testHighlight = "AI";

  return (
    <div style={{ padding: '20px', maxWidth: '800px' }}>
      <h2>Тест подсветки коротких слов (AI)</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Исходный текст:</h3>
        <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px', fontSize: '12px' }}>
          {testText}
        </pre>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Хайлайт:</h3>
        <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px', fontSize: '12px' }}>
          {testHighlight}
        </pre>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Результат с подсветкой:</h3>
        <div style={{ border: '1px solid #ccc', padding: '10px', borderRadius: '4px', background: 'white' }}>
          <HighlightWithMarkdown 
            text={testText} 
            highlights={[testHighlight]} 
          />
        </div>
      </div>

      <div style={{ marginTop: '20px' }}>
        <p><strong>Ожидаемый результат:</strong> Текст "AI" должен быть подсвечен желтым цветом.</p>
        <p><strong>Проблема была:</strong> Фильтр length &gt;= 3 отфильтровывал короткие слова как "AI", "IT"</p>
        <p><strong>Исправление:</strong> Изменен фильтр на length &gt;= 2 для поддержки аббревиатур</p>
      </div>

      <div style={{ marginTop: '20px' }}>
        <h3>Дополнительные тесты:</h3>
        <div style={{ marginBottom: '10px' }}>
          <strong>IT:</strong>
          <div style={{ border: '1px solid #ccc', padding: '5px', borderRadius: '4px', background: 'white', marginTop: '5px' }}>
            <HighlightWithMarkdown 
              text="Работаю в IT сфере более 10 лет" 
              highlights={["IT"]} 
            />
          </div>
        </div>
        <div style={{ marginBottom: '10px' }}>
          <strong>JS:</strong>
          <div style={{ border: '1px solid #ccc', padding: '5px', borderRadius: '4px', background: 'white', marginTop: '5px' }}>
            <HighlightWithMarkdown 
              text="Программирую на JS и Python" 
              highlights={["JS"]} 
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestAIHighlight;
