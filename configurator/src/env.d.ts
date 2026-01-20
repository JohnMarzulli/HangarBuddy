declare module 'react';
declare module 'react/jsx-runtime';

declare global {
    namespace JSX {
        interface IntrinsicElements {
            [elemName: string]: any;
        }
    }
}

// Intentionally left blank; rely on installed @types/react and @types/react-dom

export { };
