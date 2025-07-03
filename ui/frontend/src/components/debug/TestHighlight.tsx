import { HighlightWithMarkdown } from '../ui';

export const TestHighlight = () => {
  const testText = "Меня зовут Иван, я предприниматель с 2007 года 😄, **эксперт по систематизации бизнеса и построению эффективных команд**. В 2019 году получил сертификат коуча ICF.";
  const testHighlight = "сертификат коуча ICF";
  
  console.log("Test highlight data:", { testText, testHighlight });
  
  return (
    <div style={{ padding: '20px', border: '2px solid red', margin: '20px' }}>
      <h3>Тест подсветки:</h3>
      <p>Исходный текст: {testText}</p>
      <p>Слова для подсветки: "{testHighlight}"</p>
      <div style={{ background: '#f0f0f0', padding: '10px' }}>
        <HighlightWithMarkdown 
          text={testText}
          highlights={testHighlight}
        />
      </div>
    </div>
  );
};
