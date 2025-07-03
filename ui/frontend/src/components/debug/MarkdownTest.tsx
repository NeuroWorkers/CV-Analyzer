import { MarkdownRenderer } from '../ui/markdown/MarkdownRenderer';
import { HighlightWithMarkdown } from '../ui/hightlight/HighlightWithMarkdown';

export const MarkdownTest = () => {
  const testData = [
    {
      title: "Простой текст с жирным",
      content: "Это **жирный текст** и *курсив*. Обычный текст.",
      highlights: ["жирный", "курсив"]
    },
    {
      title: "Списки",
      content: "## Навыки:\n\n- JavaScript\n- React\n- TypeScript\n\n### Опыт:\n1. Frontend разработка\n2. Backend разработка",
      highlights: ["JavaScript", "React", "Frontend"]
    },
    {
      title: "Ссылки и код",
      content: "Мой профиль: [GitHub](https://github.com/user)\n\nКод: `const x = 5;`\n\n```js\nfunction test() {\n  return 'hello';\n}\n```",
      highlights: ["GitHub", "test"]
    },
    {
      title: "Переносы строк",
      content: "Первая строка\nВторая строка\n\nНовый абзац после пустой строки.",
      highlights: ["строка", "абзац"]
    },
    {
      title: "Сложный случай",
      content: "**Имя:** Иван Петров\n**Должность:** Senior Developer\n\n**Навыки:**\n- React ⚛️\n- Node.js 🟢\n- **TypeScript** (5+ лет)\n\n**Контакты:**\n- Email: ivan@example.com\n- Телефон: +7-xxx-xxx-xx-xx",
      highlights: ["Иван", "React", "TypeScript", "Senior"]
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h1>Тест Markdown и подсветки</h1>
      
      {testData.map((test, index) => (
        <div key={index} style={{ marginBottom: '40px', border: '1px solid #ccc', padding: '20px', borderRadius: '8px' }}>
          <h3>{test.title}</h3>
          
          <div style={{ marginBottom: '20px' }}>
            <h4>Исходный текст:</h4>
            <pre style={{ background: '#f5f5f5', padding: '10px', fontSize: '12px' }}>
              {test.content}
            </pre>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h4>Слова для подсветки:</h4>
            <code>{JSON.stringify(test.highlights)}</code>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h4>Результат с подсветкой:</h4>
            <div style={{ border: '1px solid #ddd', padding: '10px', background: 'white' }}>
              <HighlightWithMarkdown text={test.content} highlights={test.highlights} />
            </div>
          </div>
          
          <div>
            <h4>Обычный markdown (без подсветки):</h4>
            <div style={{ border: '1px solid #ddd', padding: '10px', background: 'white' }}>
              <MarkdownRenderer>{test.content}</MarkdownRenderer>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
