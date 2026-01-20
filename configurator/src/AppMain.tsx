import ConfigForm from './pages/ConfigForm';

export default function AppMain() {
    return (
        <div className="app-shell">
            <header>
                <h2>HangarBuddy</h2>
            </header>
            <main>
                <ConfigForm />
            </main>
        </div>
    );
}