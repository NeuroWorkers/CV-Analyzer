import { createRoot } from 'react-dom/client'
import './index.css'
import { App } from './App.tsx'
import '@mantine/core/styles.css';
import { MantineProvider } from '@mantine/core';
import { Provider } from 'react-redux';
import { store } from './core/store/index.ts';

import { init } from './core/init/init3419471368.js';
import { setConfig, setError } from './core/store/slices/initSlice';
import { globalConfig } from './core/config/config.ts';


async function main() {
  const url = await init();
  
  let cleanedUrl = '';
  if (url) {
    console.log('Original URL:', url);
    cleanedUrl = url.replace(/\/init[^/]*$/, '');
    console.log('Cleaned URL:', cleanedUrl);
    store.dispatch(setConfig({
      url: cleanedUrl,
      basenameFrontend: globalConfig.basenameFrontend,
    }));
  } else {
    store.dispatch(setError('No valid backend connection found'));
    console.error('Failed to initialize: No valid backend connection');
    store.dispatch(setConfig({
      url: '',
      basenameFrontend: globalConfig.basenameFrontend,
    }));
  }
  
  createRoot(document.getElementById('root')!).render(
    <MantineProvider>
      <Provider store={store}>
        <App />
      </Provider>
    </MantineProvider>,
  )

}

main();
