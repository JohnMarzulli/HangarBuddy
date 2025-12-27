const pins: Array<{ board: number; gpio: number; }> = [
    { board: 11, gpio: 17 }, { board: 13, gpio: 27 }, { board: 15, gpio: 22 }, { board: 19, gpio: 10 }, { board: 21, gpio: 9 }, { board: 23, gpio: 11 },
    { board: 29, gpio: 5 }, { board: 31, gpio: 6 }, { board: 33, gpio: 13 }, { board: 35, gpio: 19 }, { board: 37, gpio: 26 }, { board: 10, gpio: 15 },
    { board: 12, gpio: 18 }, { board: 16, gpio: 23 }, { board: 18, gpio: 24 }, { board: 22, gpio: 25 }, { board: 24, gpio: 8 }, { board: 26, gpio: 7 },
    { board: 32, gpio: 12 }, { board: 36, gpio: 16 }, { board: 38, gpio: 20 }, { board: 40, gpio: 21 }
];

export default function PinSelect({ value, onChange }: { value?: number; onChange?: (v: number) => void; }) {
    const defaultBoard = pins[0].board;
    return (
        <div className="pin-select">
            <label>Heater Pin
                <select value={String(value ?? defaultBoard)} onChange={e => onChange && onChange(Number(e.target.value))}>
                    {pins.map(p => (
                        <option key={p.board} value={p.board}>{`${p.board} / GPIO ${p.gpio}`}</option>
                    ))}
                </select>
            </label>
        </div>
    );
}