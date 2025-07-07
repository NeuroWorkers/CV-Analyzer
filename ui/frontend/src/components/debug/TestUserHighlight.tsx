import { CardComponent } from '../ui/card/Card';
import { ModalWindow } from '../ui/modal/ModalWindow';
import { useDisclosure } from '@mantine/hooks';
import { Button } from '@mantine/core';
import type { ICardData } from '../../core/types/ui-types/cardTypes';

export const TestUserHighlight = () => {
  const [opened, { open, close }] = useDisclosure(false);

  const testData: ICardData = {
    author: "@ivan_petrov Иван Петров",
    text: "Привет! Меня зовут **Иван Петров**, я опытный разработчик с экспертизой в React и TypeScript. Работаю в сфере IT уже более 5 лет.",
    date: "2024-01-15",
    highlight_text: "Иван Петров React TypeScript",
    photo: "/api/photo/123.jpg"
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Тест подсветки имени пользователя</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Тестовые данные:</h3>
        <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
          {JSON.stringify(testData, null, 2)}
        </pre>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Карточка с подсветкой:</h3>
        <CardComponent data={testData} />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <Button onClick={open}>Открыть модальное окно</Button>
        <ModalWindow opened={opened} close={close} data={testData} />
      </div>

      <div style={{ marginTop: '20px', fontSize: '14px', color: '#666' }}>
        <strong>Ожидаемый результат:</strong>
        <ul>
          <li>Юзернейм "@ivan_petrov" должен иметь подсветку на "Иван Петров"</li>
          <li>Имя "Иван Петров" должно быть полностью подсвечено</li>
          <li>В тексте должны быть подсвечены: "Иван Петров", "React", "TypeScript"</li>
        </ul>
      </div>
    </div>
  );
};
