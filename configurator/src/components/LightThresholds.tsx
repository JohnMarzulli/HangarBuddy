export default function LightThresholds({ dark, dim, lit, onChange }: { dark: number; dim: number; lit: number; onChange: (d: number, m: number, l: number) => void; }) {
    const error = dark < dim && dim < lit ? null : 'Ensure DARK < DIM < LIT';

    return (
        <div className="light-thresholds">
            <label>HANGAR_DARK
                <input type="number" value={dark} onChange={e => onChange(Number(e.target.value), dim, lit)} /></label>
            <label>HANGAR_DIM
                <input type="number" value={dim} onChange={e => onChange(dark, Number(e.target.value), lit)} /></label>
            <label>HANGAR_LIT
                <input type="number" value={lit} onChange={e => onChange(dark, dim, Number(e.target.value))} /></label>
            {error && <div className="error">{error}</div>}
        </div>
    );
}