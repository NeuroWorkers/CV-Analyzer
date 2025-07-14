import { HighlightWithMarkdown } from '../ui/hightlight/HighlightWithMarkdown';

const TestMarkdownHighlight = () => {
  const testText = `**Про опыт:**
📍бывший руководитель юридических отделов в Наукасофт и [REG.RU](https://reg.ru/);
📍практикующий юрист (12 лет стажа);
📍преподаватель в Русской Школе Управления и Moscow Business Academy;`;

  const testHighlight = "[REG.RU](https://reg.ru/);";

  return (
    <div style={{ padding: '20px', maxWidth: '800px' }}>
      <h2>Тест подсветки Markdown ссылок</h2>
      
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
        <p><strong>Ожидаемый результат:</strong> Текст "REG.RU" должен быть подсвечен желтым цветом внутри ссылки, но сама ссылка должна остаться функциональной.</p>
        <p><strong>Проблема была:</strong> "reg.ru/&gt;REG.RU;" - некорректный HTML</p>
        <p><strong>Исправление:</strong> Подсветка применяется только к текстовому содержимому, не нарушая HTML структуру</p>
      </div>
    </div>
  );
};

export default TestMarkdownHighlight;
