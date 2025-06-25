import { createSlice } from '@reduxjs/toolkit';

const configSlice = createSlice({
  name: 'config',
  initialState: {
    url: '',
    basenameFrontend: '',
    error: null, 
  },
  reducers: {
    setConfig(state, action) {
      state.url = action.payload.url || '';
      state.basenameFrontend = action.payload.basenameFrontend || '';
      state.error = action.payload.error || null;
      console.log('Config set:', { url: state.url, basenameFrontend: state.basenameFrontend });
    },
    updateUrl(state, action) {
      state.url = action.payload;
    },
    updateBasenameFrontend(state, action) {
      state.basenameFrontend = action.payload;
    },
    setError(state, action) {
      state.error = action.payload;
    },
  },
});

export const { setConfig, updateUrl, updateBasenameFrontend, setError } = configSlice.actions;
export default configSlice.reducer;