import { TestArrayHighlight } from '../../components/debug/TestArrayHighlight';
import { TestUserHighlight } from '../../components/debug/TestUserHighlight';
import { MarkdownTest } from '../../components/debug/MarkdownTest';

export const DebugPage = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h1>Страница тестирования подсветки</h1>
      
      <div style={{ marginBottom: '40px' }}>
        <TestArrayHighlight />
      </div>
      
      <hr style={{ margin: '40px 0' }} />
      
      <div style={{ marginBottom: '40px' }}>
        <TestUserHighlight />
      </div>
      
      <hr style={{ margin: '40px 0' }} />
      
      <div style={{ marginBottom: '40px' }}>
        <MarkdownTest />
      </div>
    </div>
  );
};
