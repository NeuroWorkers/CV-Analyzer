import { useState } from 'react';
import { Button } from '@mantine/core';
import { CardComponent } from '../ui/card/Card';
import type { ICardData } from '../../core/types/ui-types/cardTypes';

export const TestArrayHighlight = () => {
  const [showCards, setShowCards] = useState(false);

  // Тестовые данные в формате, который приходит с сервера
  const testApiData = {
    "data": [
      {
        "author": "@anton08081982556943f22man Умберг Антон",
        "date": "2025-07-01T22:41:50+00:00",
        "text": "If youth knew; if age could.",
        "photo": null
      },
      {
        "author": "@AKavalerchik Kavalerchik Anton",
        "date": "2025-07-01T18:51:15+00:00",
        "text": "Серийный IT Предприниматель📲🌍👨🏻‍💻 FinTech 🏦 MedTech 🏥 EdTech 👩🏼‍🏫👩🏻‍🎓",
        "photo": null
      },
      {
        "author": "@panchenko_d Panchenko Daniil",
        "date": "2025-07-02T17:41:07+00:00",
        "text": "CEO https://robosharing.ai/ RaaS robotics development. Безумие — это делать одно и то же снова и снова, ожидая иного результата",
        "photo": null
      }
    ],
    "count": 3,
    "highlight_text": [
      ["Антон"],
      ["Антон"],
      ["Panchenko", "Daniil"]
    ]
  };

  // Преобразуем данные в формат ICardData
  const processedCards: ICardData[] = testApiData.data.map((card, index) => ({
    author: card.author,
    text: card.text,
    date: card.date,
    highlight_text: testApiData.highlight_text[index] || null,
    photo: card.photo || 'https://i0.wp.com/zblibrary.info/wp-content/uploads/sites/76/2017/03/default-user.png'
  }));

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Тест индивидуальной подсветки для каждой карточки</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Исходные данные API:</h3>
        <pre style={{ 
          background: '#f5f5f5', 
          padding: '10px', 
          borderRadius: '4px',
          fontSize: '12px',
          overflow: 'auto',
          maxHeight: '300px'
        }}>
          {JSON.stringify(testApiData, null, 2)}
        </pre>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Обработанные данные карточек:</h3>
        <pre style={{ 
          background: '#f0f8ff', 
          padding: '10px', 
          borderRadius: '4px',
          fontSize: '12px',
          overflow: 'auto',
          maxHeight: '300px'
        }}>
          {JSON.stringify(processedCards, null, 2)}
        </pre>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <Button onClick={() => setShowCards(!showCards)}>
          {showCards ? 'Скрыть карточки' : 'Показать карточки'}
        </Button>
      </div>

      {showCards && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h3>Карточки с индивидуальной подсветкой:</h3>
          {processedCards.map((card, index) => (
            <div key={index} style={{ border: '1px solid #ddd', padding: '10px', borderRadius: '8px' }}>
              <div style={{ marginBottom: '10px', fontSize: '14px', color: '#666' }}>
                <strong>Карточка {index + 1}:</strong> Подсвечиваем: {JSON.stringify(card.highlight_text)}
              </div>
              <CardComponent data={card} />
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '20px', fontSize: '14px', color: '#666' }}>
        <strong>Ожидаемый результат:</strong>
        <ul>
          <li>Карточка 1: Подсветка "Антон" в имени и юзернейме</li>
          <li>Карточка 2: Подсветка "Антон" в имени и юзернейме</li>
          <li>Карточка 3: Подсветка "Panchenko" и "Daniil" в имени и юзернейме</li>
        </ul>
      </div>
    </div>
  );
};
