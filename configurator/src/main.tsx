import { createRoot } from 'react-dom/client';
import '../style.css';
import App from './AppMain';

const root = createRoot(document.getElementById('root')!);
root.render(<App />);
