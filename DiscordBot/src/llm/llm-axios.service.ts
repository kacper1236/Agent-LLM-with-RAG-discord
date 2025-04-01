import Axios from 'axios';

export const llmAxios = Axios.create({
  baseURL: 'http://localhost:8080',
  // baseURL: 'http://localhost:11434/api',
});
